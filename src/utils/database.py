"""SQLite database schema and initialization."""
import sqlite3
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Manage SQLite database for screenshot indexing."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """Connect to database and enable foreign keys."""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection
    
    def initialize_schema(self) -> None:
        """Create all database tables."""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        # Main screenshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                current_filename TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL UNIQUE,
                file_size_bytes INTEGER NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                format TEXT NOT NULL,
                created_date TIMESTAMP NOT NULL,
                processed_date TIMESTAMP NOT NULL,
                category TEXT NOT NULL,
                keywords TEXT NOT NULL,  -- JSON array
                ocr_text TEXT,
                vision_description TEXT,
                content_type TEXT,
                confidence REAL NOT NULL,
                thumbnail BLOB,
                tags TEXT,  -- JSON array
                is_indexed BOOLEAN DEFAULT 1,
                CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
            )
        """)
        
        # Search terms table for fast searching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screenshot_id INTEGER NOT NULL,
                term TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_terms_term 
            ON search_terms(term)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_search_terms_screenshot 
            ON search_terms(screenshot_id)
        """)
        
        # Full-text search index
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                screenshot_id UNINDEXED,
                original_filename,
                ocr_text,
                vision_description,
                keywords,
                tags,
                content='screenshots',
                content_rowid='id'
            )
        """)
        
        # Triggers to keep FTS index in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS screenshots_ai AFTER INSERT ON screenshots BEGIN
                INSERT INTO search_index(screenshot_id, original_filename, ocr_text, vision_description, keywords, tags)
                VALUES (new.id, new.original_filename, new.ocr_text, new.vision_description, new.keywords, new.tags);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS screenshots_ad AFTER DELETE ON screenshots BEGIN
                DELETE FROM search_index WHERE screenshot_id = old.id;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS screenshots_au AFTER UPDATE ON screenshots BEGIN
                UPDATE search_index SET 
                    original_filename = new.original_filename,
                    ocr_text = new.ocr_text,
                    vision_description = new.vision_description,
                    keywords = new.keywords,
                    tags = new.tags
                WHERE screenshot_id = new.id;
            END
        """)
        
        # Processing log for rollback capability
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screenshot_id INTEGER,
                operation TEXT NOT NULL,  -- insert|update|move|rename|delete
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                old_path TEXT,
                new_path TEXT,
                old_filename TEXT,
                new_filename TEXT,
                status TEXT NOT NULL,  -- success|failed|rolled_back
                error_message TEXT,
                metadata TEXT,  -- JSON for additional info
                FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
            )
        """)
        
        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON screenshots(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_date ON screenshots(created_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed_date ON screenshots(processed_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence ON screenshots(confidence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON screenshots(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_screenshot ON processing_log(screenshot_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_timestamp ON processing_log(timestamp)")
        
        self.connection.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


# SQL Schema as standalone script
SCHEMA_SQL = """
-- Main screenshots table
CREATE TABLE IF NOT EXISTS screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_filename TEXT NOT NULL,
    current_filename TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL UNIQUE,
    file_size_bytes INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    format TEXT NOT NULL,
    created_date TIMESTAMP NOT NULL,
    processed_date TIMESTAMP NOT NULL,
    category TEXT NOT NULL,
    keywords TEXT NOT NULL,  -- JSON array
    ocr_text TEXT,
    vision_description TEXT,
    content_type TEXT,
    confidence REAL NOT NULL,
    thumbnail BLOB,
    tags TEXT,  -- JSON array
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

-- Full-text search virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    screenshot_id UNINDEXED,
    original_filename,
    ocr_text,
    vision_description,
    keywords,
    tags,
    content='screenshots',
    content_rowid='id'
);

-- Processing log for audit trail and rollback
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screenshot_id INTEGER,
    operation TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_path TEXT,
    new_path TEXT,
    old_filename TEXT,
    new_filename TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    metadata TEXT,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_category ON screenshots(category);
CREATE INDEX IF NOT EXISTS idx_created_date ON screenshots(created_date);
CREATE INDEX IF NOT EXISTS idx_processed_date ON screenshots(processed_date);
CREATE INDEX IF NOT EXISTS idx_confidence ON screenshots(confidence);
CREATE INDEX IF NOT EXISTS idx_file_hash ON screenshots(file_hash);
CREATE INDEX IF NOT EXISTS idx_log_screenshot ON processing_log(screenshot_id);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON processing_log(timestamp);

-- Triggers to maintain FTS index
CREATE TRIGGER IF NOT EXISTS screenshots_ai AFTER INSERT ON screenshots BEGIN
    INSERT INTO search_index(screenshot_id, original_filename, ocr_text, vision_description, keywords, tags)
    VALUES (new.id, new.original_filename, new.ocr_text, new.vision_description, new.keywords, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS screenshots_ad AFTER DELETE ON screenshots BEGIN
    DELETE FROM search_index WHERE screenshot_id = old.id;
END;

CREATE TRIGGER IF NOT EXISTS screenshots_au AFTER UPDATE ON screenshots BEGIN
    UPDATE search_index SET 
        original_filename = new.original_filename,
        ocr_text = new.ocr_text,
        vision_description = new.vision_description,
        keywords = new.keywords,
        tags = new.tags
    WHERE screenshot_id = new.id;
END;
"""
