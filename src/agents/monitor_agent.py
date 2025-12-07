"""File monitoring agent for detecting new screenshots."""
import time
from pathlib import Path
from queue import Queue
from typing import Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from loguru import logger

from ..utils.platform_utils import is_valid_image_file, is_temporary_file


class ScreenshotEventHandler(FileSystemEventHandler):
    """Handle file system events for screenshots."""
    
    def __init__(self, file_queue: Queue, completion_wait: float = 1.0):
        super().__init__()
        self.file_queue = file_queue
        self.completion_wait = completion_wait
        self.pending_files: dict[str, float] = {}
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        filename = file_path.name
        
        # Filter out temporary and invalid files
        if is_temporary_file(filename):
            logger.debug(f"Ignoring temporary file: {filename}")
            return
        
        if not is_valid_image_file(filename):
            logger.debug(f"Ignoring non-image file: {filename}")
            return
        
        # Track file for completion detection
        self.pending_files[str(file_path)] = 0
        logger.info(f"Detected new file: {filename}")
    
    def check_file_completion(self) -> None:
        """Check if pending files are fully written."""
        completed_files = []
        
        for file_path_str, last_size in list(self.pending_files.items()):
            file_path = Path(file_path_str)
            
            try:
                if not file_path.exists():
                    del self.pending_files[file_path_str]
                    continue
                
                current_size = file_path.stat().st_size
                
                # File size hasn't changed - it's complete
                if current_size == last_size and current_size > 0:
                    completed_files.append(file_path)
                    del self.pending_files[file_path_str]
                    logger.info(f"File complete: {file_path.name} ({current_size} bytes)")
                else:
                    # Update size for next check
                    self.pending_files[file_path_str] = current_size
            
            except (OSError, PermissionError) as e:
                logger.warning(f"Error checking file {file_path.name}: {e}")
                continue
        
        # Add completed files to processing queue
        for file_path in completed_files:
            self.file_queue.put(file_path)


class MonitorAgent:
    """Monitor screenshot folders for new files."""
    
    def __init__(
        self,
        folder_path: Path,
        file_queue: Optional[Queue] = None,
        completion_wait: float = 1.0
    ):
        self.folder_path = Path(folder_path)
        self.file_queue = file_queue or Queue()
        self.completion_wait = completion_wait
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[ScreenshotEventHandler] = None
        self.running = False
    
    def validate_folder(self) -> None:
        """Validate that the folder exists and is accessible."""
        if not self.folder_path.exists():
            raise FileNotFoundError(
                f"Screenshot folder does not exist: {self.folder_path}\n"
                f"Please create the folder or specify a different path."
            )
        
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self.folder_path}")
        
        # Test read permissions
        try:
            list(self.folder_path.iterdir())
        except PermissionError as e:
            raise PermissionError(
                f"No permission to read folder: {self.folder_path}\n"
                f"On Mac: Grant permission in System Preferences → Security & Privacy → Files and Folders\n"
                f"On Windows: Run as administrator or check folder permissions\n"
                f"Error: {e}"
            )
    
    def start(self) -> None:
        """Start monitoring the folder."""
        self.validate_folder()
        
        self.event_handler = ScreenshotEventHandler(
            self.file_queue,
            self.completion_wait
        )
        
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.folder_path),
            recursive=False
        )
        
        self.observer.start()
        self.running = True
        logger.info(f"Started monitoring: {self.folder_path}")
    
    def stop(self) -> None:
        """Stop monitoring."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("Stopped monitoring")
    
    def run(self, callback: Optional[Callable[[Path], None]] = None) -> None:
        """Run the monitor with optional callback for each file."""
        self.start()
        
        try:
            while self.running:
                # Check for file completion
                if self.event_handler:
                    self.event_handler.check_file_completion()
                
                # Process completed files
                while not self.file_queue.empty():
                    file_path = self.file_queue.get()
                    logger.info(f"Processing: {file_path.name}")
                    
                    if callback:
                        try:
                            callback(file_path)
                        except Exception as e:
                            logger.error(f"Error processing {file_path.name}: {e}")
                
                time.sleep(self.completion_wait)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
    
    def get_pending_count(self) -> int:
        """Get number of files waiting for completion."""
        if self.event_handler:
            return len(self.event_handler.pending_files)
        return 0
    
    def get_queue_size(self) -> int:
        """Get number of files ready for processing."""
        return self.file_queue.qsize()
