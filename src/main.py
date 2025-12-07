"""Main orchestrator for Screenshot Organizer."""
import argparse
import signal
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from .config import load_config, Config
from .utils.logger import setup_logging
from .utils.platform_utils import get_os_type, get_screenshot_folder
from .agents.monitor_agent import MonitorAgent
from .agents.ocr_agent import OCRAgent
from .agents.vision_agent import VisionAgent
from .agents.classifier_agent import ClassifierAgent
from .agents.organizer_agent import OrganizerAgent
from .agents.indexer_agent import IndexerAgent
from .utils.search_engine import SearchEngine
from .schemas.models import ScreenshotMetadata, ProcessingResult


class ScreenshotOrganizer:
    """Main orchestrator coordinating all agents."""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'by_category': {}
        }
        self.checkpoint_file = Path("data/checkpoint.json")
        
        # Initialize agents
        self._init_agents()
        
        # Load checkpoint
        self._load_checkpoint()
    
    def _init_agents(self) -> None:
        """Initialize all agents."""
        try:
            # Get source folder
            os_type = get_os_type()
            if os_type == "windows":
                source_folder = Path(self.config.source_folders.windows.replace("{USERNAME}", Path.home().name))
            elif os_type == "mac":
                source_folder = Path(self.config.source_folders.mac).expanduser()
            else:
                source_folder = Path(self.config.source_folders.linux).expanduser()
            
            # Initialize agents
            self.monitor = MonitorAgent(
                folder_path=source_folder,
                completion_wait=self.config.monitoring.file_completion_wait_seconds
            )
            
            self.ocr = OCRAgent(
                cache_dir=Path(self.config.ocr.cache_dir)
            ) if self.config.ocr.enabled else None
            
            self.vision = VisionAgent(
                model=self.config.claude_vision.model,
                max_tokens=self.config.claude_vision.max_tokens,
                timeout=self.config.claude_vision.timeout_seconds,
                max_retries=self.config.claude_vision.max_retries
            )
            
            self.classifier = ClassifierAgent(
                model=self.config.claude_vision.model,
                max_tokens=500
            )
            
            self.organizer = OrganizerAgent(
                base_folder=Path(self.config.output_base),
                db_path=Path(self.config.database.path),
                dry_run=self.config.dry_run
            )
            
            self.indexer = IndexerAgent(
                db_path=Path(self.config.database.path)
            )
            
            self.search = SearchEngine(
                db_path=Path(self.config.database.path)
            )
            
            logger.info("All agents initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def _load_checkpoint(self) -> None:
        """Load checkpoint for resume capability."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                self.stats = checkpoint.get('stats', self.stats)
                logger.info(f"Loaded checkpoint: {self.stats['total']} processed")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
    
    def _save_checkpoint(self) -> None:
        """Save checkpoint."""
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'stats': self.stats,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
    
    def process_screenshot(self, file_path: Path) -> bool:
        """Process a single screenshot through all agents."""
        self.stats['total'] += 1
        
        try:
            logger.info(f"Processing [{self.stats['total']}]: {file_path.name}")
            
            # Create metadata
            stat = file_path.stat()
            metadata = ScreenshotMetadata(
                file_path=file_path,
                original_filename=file_path.name,
                file_size_bytes=stat.st_size,
                width=0,  # Will be set by PIL
                height=0,
                format="",
                created_timestamp=datetime.fromtimestamp(stat.st_ctime),
                modified_timestamp=datetime.fromtimestamp(stat.st_mtime),
                file_hash=""
            )
            
            # Get image dimensions
            from PIL import Image
            with Image.open(file_path) as img:
                metadata.width = img.width
                metadata.height = img.height
                metadata.format = img.format or "PNG"
            
            # Generate file hash
            from .agents.naming_agent import NamingAgent
            namer = NamingAgent()
            metadata.file_hash = namer._get_file_hash(file_path)
            
            # Step 1: OCR
            ocr_text = ""
            if self.ocr and self.config.ocr.enabled:
                try:
                    ocr_text = self.ocr.extract_text(file_path)
                    logger.debug(f"OCR: {len(ocr_text)} characters")
                except Exception as e:
                    logger.warning(f"OCR failed: {e}")
            
            # Step 2: Vision
            try:
                vision_analysis = self.vision.analyze_image(file_path, ocr_text=ocr_text)
                logger.debug(f"Vision: {vision_analysis.content_type}")
            except Exception as e:
                logger.error(f"Vision analysis failed: {e}")
                self.stats['failed'] += 1
                return False
            
            # Step 3: Classify
            try:
                classification = self.classifier.classify(ocr_text, vision_analysis=vision_analysis)
                logger.info(f"Category: {classification.category} (confidence: {classification.confidence:.2f})")
                
                # Check confidence threshold
                if classification.confidence < self.config.processing.min_confidence:
                    logger.warning(f"Low confidence ({classification.confidence:.2f}), skipping")
                    self.stats['skipped'] += 1
                    return False
            except Exception as e:
                logger.error(f"Classification failed: {e}")
                self.stats['failed'] += 1
                return False
            
            # Step 4: Organize
            try:
                org_result = self.organizer.organize(
                    source_path=file_path,
                    classification=classification,
                    created_date=metadata.created_timestamp
                )
                
                if not org_result.success:
                    logger.error(f"Organization failed: {org_result.error_message}")
                    self.stats['failed'] += 1
                    return False
                
                logger.info(f"Organized: {org_result.new_filename}")
            except Exception as e:
                logger.error(f"Organization failed: {e}")
                self.stats['failed'] += 1
                return False
            
            # Step 5: Index
            if not self.config.dry_run:
                try:
                    processing_result = ProcessingResult(
                        metadata=metadata,
                        ocr_text=ocr_text,
                        vision_analysis=vision_analysis
                    )
                    
                    screenshot_id = self.indexer.index_screenshot(
                        file_path=file_path,
                        processing_result=processing_result,
                        classification=classification,
                        new_filename=org_result.new_filename,
                        new_path=org_result.destination_path
                    )
                    
                    logger.info(f"Indexed: ID {screenshot_id}")
                except Exception as e:
                    logger.error(f"Indexing failed: {e}")
                    # Don't fail the whole process if indexing fails
            
            # Update stats
            self.stats['success'] += 1
            category = classification.category
            self.stats['by_category'][category] = self.stats['by_category'].get(category, 0) + 1
            
            # Save checkpoint every 10 files
            if self.stats['total'] % 10 == 0:
                self._save_checkpoint()
                self._print_progress()
            
            return True
        
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            self.stats['failed'] += 1
            return False
    
    def _print_progress(self) -> None:
        """Print progress statistics."""
        logger.info(
            f"Progress: {self.stats['total']} total, "
            f"{self.stats['success']} success, "
            f"{self.stats['failed']} failed, "
            f"{self.stats['skipped']} skipped"
        )
    
    def run(self) -> None:
        """Main loop."""
        self.running = True
        
        logger.info("Starting Screenshot Organizer")
        logger.info(f"Monitoring: {self.monitor.folder_path}")
        logger.info(f"Output: {self.config.output_base}")
        logger.info(f"Dry run: {self.config.dry_run}")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start monitoring
        self.monitor.start()
        
        try:
            while self.running:
                # Check for completed files
                if self.monitor.event_handler:
                    self.monitor.event_handler.check_file_completion()
                
                # Process queued files
                while not self.monitor.file_queue.empty():
                    file_path = self.monitor.file_queue.get()
                    self.process_screenshot(file_path)
                
                import time
                time.sleep(self.config.monitoring.poll_interval_seconds)
        
        finally:
            self.shutdown()
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info("Received shutdown signal")
        self.running = False
    
    def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down...")
        
        if self.monitor:
            self.monitor.stop()
        
        self._save_checkpoint()
        self._print_progress()
        
        logger.info("Shutdown complete")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI-Powered Screenshot Organizer")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to config file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without moving files"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics and exit"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="Search indexed screenshots"
    )
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
        
        # Override with command-line args
        if args.dry_run:
            config.dry_run = True
        
        if args.debug:
            config.logging.level = "DEBUG"
    
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(
        log_file=Path(config.logging.file),
        level=config.logging.level,
        max_size_mb=config.logging.max_size_mb,
        backup_count=config.logging.backup_count,
        console=config.logging.console
    )
    
    # Handle special modes
    if args.stats:
        search = SearchEngine(Path(config.database.path))
        stats = search.get_stats()
        print(f"\n📊 Statistics:")
        print(f"Total screenshots: {stats['total_screenshots']}")
        print(f"Average confidence: {stats['average_confidence']:.2f}")
        print(f"\nBy category:")
        for category, count in stats['by_category'].items():
            print(f"  {category}: {count}")
        sys.exit(0)
    
    if args.search:
        search = SearchEngine(Path(config.database.path))
        results = search.full_text_search(args.search)
        print(f"\n🔍 Search results for '{args.search}':")
        for result in results[:10]:
            print(f"  {result['current_filename']}")
            print(f"    Category: {result['category']}")
            print(f"    Date: {result['created_date']}")
        sys.exit(0)
    
    # Run organizer
    try:
        organizer = ScreenshotOrganizer(config)
        organizer.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
