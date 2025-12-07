"""User correction tracking for classification improvements."""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional


class UserCorrectionManager:
    """Manage user corrections to classification results."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._initialize_table()
    
    def _initialize_table(self) -> None:
        """Create user corrections table."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screenshot_id INTEGER,
                original_category TEXT NOT NULL,
                corrected_category TEXT NOT NULL,
                original_keywords TEXT,
                corrected_keywords TEXT,
                correction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ocr_text_sample TEXT,
                vision_description TEXT,
                FOREIGN KEY (screenshot_id) REFERENCES screenshots(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_corrections_category 
            ON user_corrections(corrected_category)
        """)
        
        conn.commit()
        conn.close()
    
    def add_correction(
        self,
        screenshot_id: int,
        original_category: str,
        corrected_category: str,
        original_keywords: list[str],
        corrected_keywords: list[str],
        ocr_text: Optional[str] = None,
        vision_description: Optional[str] = None
    ) -> None:
        """Record a user correction."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_corrections (
                screenshot_id, original_category, corrected_category,
                original_keywords, corrected_keywords,
                ocr_text_sample, vision_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            screenshot_id,
            original_category,
            corrected_category,
            ",".join(original_keywords),
            ",".join(corrected_keywords),
            ocr_text[:500] if ocr_text else None,
            vision_description[:500] if vision_description else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_correction_patterns(self) -> dict:
        """Get common correction patterns for learning."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get most common corrections
        cursor.execute("""
            SELECT 
                original_category,
                corrected_category,
                COUNT(*) as count
            FROM user_corrections
            GROUP BY original_category, corrected_category
            ORDER BY count DESC
            LIMIT 20
        """)
        
        patterns = {}
        for row in cursor.fetchall():
            orig, corrected, count = row
            patterns[f"{orig}->{corrected}"] = count
        
        conn.close()
        return patterns
    
    def get_correction_count(self) -> int:
        """Get total number of corrections."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_corrections")
        count = cursor.fetchone()[0]
        conn.close()
        return count
