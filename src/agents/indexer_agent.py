"""Indexer agent for adding screenshots to database."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from io import BytesIO
from PIL import Image
from loguru import logger

from ..schemas.models import ProcessingResult, ClassificationResult


class IndexerAgent:
    """Index screenshots in database with search support."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._ensure_database()
    
    def _ensure_database(self) -> None:
        """Ensure database and tables exist."""
        from ..utils.database import DatabaseManager
        db = DatabaseManager(self.db_path)
        db.connect()
        db.initialize_schema()
        db.close()
    
    def index_screenshot(
        self,
        file_path: Path,
        processing_result: ProcessingResult,
        classification: ClassificationResult,
        new_filename: str,
        new_path: Path
    ) -> int:
        """Add screenshot to database and return ID."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Generate thumbnail
            thumbnail_blob = self._generate_thumbnail(file_path)
            
            # Prepare data
            metadata = processing_result.metadata
            keywords_json = json.dumps(classification.keywords)
            tags_json = json.dumps(classification.tags)
            
            # Insert screenshot
            cursor.execute("""
                INSERT INTO screenshots (
                    original_filename, current_filename, file_path,
                    file_size_bytes, width, height, format,
                    created_date, processed_date,
                    category, keywords, ocr_text, vision_description,
                    confidence, thumbnail, tags, file_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.original_filename,
                new_filename,
                str(new_path),
                metadata.file_size_bytes,
                metadata.width,
                metadata.height,
                metadata.format,
                metadata.created_timestamp.isoformat(),
                datetime.now().isoformat(),
                classification.category,
                keywords_json,
                processing_result.ocr_text or "",
                processing_result.vision_analysis.description if processing_result.vision_analysis else "",
                classification.confidence,
                thumbnail_blob,
                tags_json,
                metadata.file_hash
            ))
            
            screenshot_id = cursor.lastrowid
            
            # Create search index entries
            self._create_search_index(
                cursor,
                screenshot_id,
                processing_result.ocr_text or "",
                classification.keywords
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Indexed: {new_filename} (ID: {screenshot_id})")
            return screenshot_id
        
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            raise
    
    def _generate_thumbnail(self, file_path: Path, size: tuple = (150, 150)) -> bytes:
        """Generate thumbnail and return as bytes."""
        try:
            img = Image.open(file_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")
            return b""
    
    def _create_search_index(
        self,
        cursor: sqlite3.Cursor,
        screenshot_id: int,
        ocr_text: str,
        keywords: list[str]
    ) -> None:
        """Create search index entries for fast searching."""
        # Index keywords with high weight
        for keyword in keywords:
            cursor.execute("""
                INSERT INTO search_terms (screenshot_id, term, weight)
                VALUES (?, ?, ?)
            """, (screenshot_id, keyword.lower(), 1.0))
        
        # Index OCR text words with lower weight
        if ocr_text:
            words = set(ocr_text.lower().split())
            for word in words:
                if len(word) > 2:  # Skip very short words
                    cursor.execute("""
                        INSERT INTO search_terms (screenshot_id, term, weight)
                        VALUES (?, ?, ?)
                    """, (screenshot_id, word, 0.5))
    
    def rebuild_index(self) -> int:
        """Rebuild search index from scratch."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Clear existing search index
            cursor.execute("DELETE FROM search_terms")
            
            # Get all screenshots
            cursor.execute("""
                SELECT id, keywords, ocr_text
                FROM screenshots
            """)
            
            count = 0
            for row in cursor.fetchall():
                screenshot_id, keywords_json, ocr_text = row
                keywords = json.loads(keywords_json) if keywords_json else []
                
                self._create_search_index(cursor, screenshot_id, ocr_text or "", keywords)
                count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Rebuilt search index for {count} screenshots")
            return count
        
        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")
            return 0
    
    def update_screenshot(
        self,
        screenshot_id: int,
        category: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        tags: Optional[list[str]] = None
    ) -> bool:
        """Update screenshot metadata."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if category:
                updates.append("category = ?")
                params.append(category)
            
            if keywords:
                updates.append("keywords = ?")
                params.append(json.dumps(keywords))
            
            if tags:
                updates.append("tags = ?")
                params.append(json.dumps(tags))
            
            if updates:
                params.append(screenshot_id)
                cursor.execute(f"""
                    UPDATE screenshots
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
            
            conn.close()
            return True
        
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
