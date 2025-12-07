"""Organizer agent for moving and organizing screenshot files."""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from loguru import logger

from ..schemas.models import OrganizationResult, ClassificationResult
from .naming_agent import NamingAgent


class OrganizerAgent:
    """Organize screenshots into folders with intelligent naming."""
    
    def __init__(
        self,
        base_folder: Path,
        db_path: Path,
        dry_run: bool = False
    ):
        self.base_folder = Path(base_folder)
        self.db_path = Path(db_path)
        self.dry_run = dry_run
        self.naming_agent = NamingAgent()
    
    def organize(
        self,
        source_path: Path,
        classification: ClassificationResult,
        created_date: Optional[datetime] = None
    ) -> OrganizationResult:
        """Organize screenshot: rename and move to appropriate folder."""
        source_path = Path(source_path)
        
        if not source_path.exists():
            return OrganizationResult(
                original_filename=source_path.name,
                new_filename="",
                source_path=source_path,
                destination_path=source_path,
                operation="move",
                success=False,
                error_message="Source file not found"
            )
        
        try:
            # Generate new filename
            new_filename = self.naming_agent.generate_filename(
                category=classification.category,
                keywords=classification.keywords,
                file_path=source_path,
                created_date=created_date
            )
            
            # Get target folder
            target_folder = self.get_target_folder(
                category=classification.category,
                keywords=classification.keywords,
                date=created_date or datetime.now()
            )
            
            # Handle duplicates
            new_filename = self.naming_agent.handle_duplicate(new_filename, target_folder)
            
            # Full destination path
            destination_path = target_folder / new_filename
            
            # Move file
            if not self.dry_run:
                success = self._move_file(source_path, destination_path)
                
                if success:
                    # Log operation
                    self._log_operation(
                        source_path,
                        destination_path,
                        "move",
                        "success"
                    )
            else:
                success = True
                logger.info(f"[DRY RUN] Would move: {source_path.name} → {destination_path}")
            
            return OrganizationResult(
                original_filename=source_path.name,
                new_filename=new_filename,
                source_path=source_path,
                destination_path=destination_path,
                operation="move",
                success=success,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return OrganizationResult(
                original_filename=source_path.name,
                new_filename="",
                source_path=source_path,
                destination_path=source_path,
                operation="move",
                success=False,
                error_message=str(e)
            )
    
    def get_target_folder(
        self,
        category: str,
        keywords: list[str],
        date: datetime
    ) -> Path:
        """Get target folder path based on category and keywords."""
        # Date folder (YYYY-MM)
        date_folder = date.strftime("%Y-%m")
        
        # Category folder
        category_folder = category.title()
        
        # Subcategory folder (optional)
        subcategory = self._get_subcategory(category, keywords)
        
        # Build path
        if subcategory:
            folder_path = self.base_folder / date_folder / category_folder / subcategory
        else:
            folder_path = self.base_folder / date_folder / category_folder
        
        # Create folder if it doesn't exist
        if not self.dry_run:
            folder_path.mkdir(parents=True, exist_ok=True)
        
        return folder_path
    
    def _get_subcategory(self, category: str, keywords: list[str]) -> Optional[str]:
        """Determine subcategory from keywords."""
        if not keywords:
            return None
        
        keywords_lower = [k.lower() for k in keywords]
        
        if category == "ERROR":
            if any(k in keywords_lower for k in ["database", "db"]):
                return "Database"
            if any(k in keywords_lower for k in ["network", "timeout", "connection"]):
                return "Network"
            if any(k in keywords_lower for k in ["memory", "null", "undefined"]):
                return "Runtime"
            if any(k in keywords_lower for k in ["404", "500", "503"]):
                return "HTTP"
        
        elif category == "CODE":
            lang_map = {
                "python": "Python",
                "javascript": "JavaScript",
                "typescript": "TypeScript",
                "java": "Java",
                "rust": "Rust",
                "go": "Go",
                "config": "Config",
                "yaml": "Config",
                "json": "Config"
            }
            for kw in keywords_lower:
                if kw in lang_map:
                    return lang_map[kw]
        
        elif category == "UI":
            ui_map = {
                "dashboard": "Dashboard",
                "login": "Auth",
                "signup": "Auth",
                "settings": "Settings",
                "form": "Forms"
            }
            for kw in keywords_lower:
                if kw in ui_map:
                    return ui_map[kw]
        
        elif category == "DATA":
            if any(k in keywords_lower for k in ["chart", "graph"]):
                return "Charts"
            if "report" in keywords_lower:
                return "Reports"
            if "table" in keywords_lower:
                return "Tables"
        
        return None
    
    def _move_file(self, source: Path, destination: Path) -> bool:
        """Move file and preserve timestamps."""
        try:
            # Get original timestamps
            stat = source.stat()
            
            # Move file
            shutil.move(str(source), str(destination))
            
            # Preserve timestamps
            shutil.copystat(str(source) if source.exists() else str(destination), str(destination))
            
            logger.info(f"Moved: {source.name} → {destination}")
            return True
        
        except PermissionError as e:
            logger.error(f"Permission denied: {e}")
            return False
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return False
    
    def _log_operation(
        self,
        source: Path,
        destination: Path,
        operation: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Log operation to database for rollback support."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO processing_log (
                    operation, timestamp, old_path, new_path,
                    old_filename, new_filename, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation,
                datetime.now().isoformat(),
                str(source),
                str(destination),
                source.name,
                destination.name,
                status,
                error_message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")
    
    def rollback(self, hours: int = 24) -> int:
        """Rollback file moves within specified hours."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get recent successful moves
            cutoff = datetime.now().timestamp() - (hours * 3600)
            
            cursor.execute("""
                SELECT id, old_path, new_path, old_filename, new_filename
                FROM processing_log
                WHERE operation = 'move'
                AND status = 'success'
                AND timestamp > ?
                ORDER BY timestamp DESC
            """, (datetime.fromtimestamp(cutoff).isoformat(),))
            
            moves = cursor.fetchall()
            rollback_count = 0
            
            for move_id, old_path, new_path, old_filename, new_filename in moves:
                new_path_obj = Path(new_path)
                old_path_obj = Path(old_path)
                
                if new_path_obj.exists():
                    try:
                        # Move back to original location
                        old_path_obj.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(new_path_obj), str(old_path_obj))
                        
                        # Update log
                        cursor.execute("""
                            UPDATE processing_log
                            SET status = 'rolled_back'
                            WHERE id = ?
                        """, (move_id,))
                        
                        rollback_count += 1
                        logger.info(f"Rolled back: {new_filename} → {old_filename}")
                    
                    except Exception as e:
                        logger.error(f"Rollback failed for {new_filename}: {e}")
            
            conn.commit()
            conn.close()
            
            return rollback_count
        
        except Exception as e:
            logger.error(f"Rollback operation failed: {e}")
            return 0
