# 🔍 Database & Search System Usage Guide

## Overview

Complete database and search system for screenshot indexing and retrieval.

**Components:**
1. **SQLite Database** - Store all screenshot metadata
2. **Indexer Agent** - Add screenshots to database
3. **Search Engine** - Find and filter screenshots

## Database Schema

### 1. screenshots Table

```sql
CREATE TABLE screenshots (
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
    keywords TEXT NOT NULL,          -- JSON array
    ocr_text TEXT,
    vision_description TEXT,
    content_type TEXT,
    confidence REAL NOT NULL,
    thumbnail BLOB,
    tags TEXT,                        -- JSON array
    is_indexed BOOLEAN DEFAULT 1,
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);
```

### 2. search_terms Table

```sql
CREATE TABLE search_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    screenshot_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    FOREIGN KEY (screenshot_id) REFERENCES screenshots(id) ON DELETE CASCADE
);

CREATE INDEX idx_search_terms_term ON search_terms(term);
CREATE INDEX idx_search_terms_screenshot ON search_terms(screenshot_id);
```

### 3. search_index Table (FTS5)

```sql
CREATE VIRTUAL TABLE search_index USING fts5(
    screenshot_id UNINDEXED,
    original_filename,
    ocr_text,
    vision_description,
    keywords,
    tags,
    content='screenshots',
    content_rowid='id'
);
```

### 4. processing_log Table

```sql
CREATE TABLE processing_log (
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
```

## Indexer Agent

### Basic Usage

```python
from pathlib import Path
from src.agents.indexer_agent import IndexerAgent

# Initialize
indexer = IndexerAgent(Path("data/screenshots.db"))

# Index screenshot
screenshot_id = indexer.index_screenshot(
    file_path=Path("screenshot.png"),
    processing_result=processing_result,
    classification=classification,
    new_filename="2025-12-07_Error-DB_Database_a3f2.png",
    new_path=Path("organized/2025-12/Error/Database/...")
)

print(f"Indexed with ID: {screenshot_id}")
```

### Thumbnail Generation

Automatically generates 150x150px thumbnails:

```python
# Automatic during indexing
thumbnail_blob = indexer._generate_thumbnail(file_path)

# Custom size
thumbnail_blob = indexer._generate_thumbnail(file_path, size=(200, 200))
```

### Rebuild Index

```python
# Rebuild search index from scratch
count = indexer.rebuild_index()
print(f"Rebuilt index for {count} screenshots")
```

### Update Screenshot

```python
# Update metadata
indexer.update_screenshot(
    screenshot_id=123,
    category="CODE",
    keywords=["python", "async"],
    tags=["important", "review"]
)
```

## Search Engine

### Basic Search

```python
from src.utils.search_engine import SearchEngine

search = SearchEngine(Path("data/screenshots.db"))

# Search all
results = search.search()

# Search by text
results = search.search(query="database")

# Search by category
results = search.search(category="ERROR")

# Search by date range
from datetime import datetime, timedelta
today = datetime.now()
week_ago = today - timedelta(days=7)
results = search.search(date_from=week_ago, date_to=today)
```

### Full-Text Search

```python
# Search OCR text and keywords with relevance scoring
results = search.full_text_search("database timeout")

for result in results:
    print(f"{result['current_filename']}")
    print(f"  Relevance: {result.get('relevance_score', 0)}")
    print(f"  Category: {result['category']}")
```

### Advanced Search

**Syntax:**
- `category:ERROR` - Filter by category
- `date:2025-12-01..2025-12-07` - Date range
- `tag:important` - Filter by tag
- Combine multiple filters

**Examples:**

```python
# Category filter
results = search.advanced_search("category:ERROR")

# Date range
results = search.advanced_search("date:2025-12-01..2025-12-07")

# Tag search
results = search.advanced_search("tag:important")

# Combined
results = search.advanced_search("database category:ERROR date:2025-12-01..2025-12-07")
```

### Filter Methods

```python
# By category
results = search.filter_by_category("ERROR")

# By date range
results = search.filter_by_date_range(start_date, end_date)

# Recent screenshots
results = search.get_recent(limit=20)

# By ID
screenshot = search.get_by_id(123)
```

### Search Suggestions

```python
# Get autocomplete suggestions
suggestions = search.get_suggestions("data")
# Returns: ["database", "data", "dataframe", ...]

suggestions = search.get_suggestions("err")
# Returns: ["error", "errno", ...]
```

### Statistics

```python
stats = search.get_stats()

print(f"Total: {stats['total_screenshots']}")
print(f"Avg confidence: {stats['average_confidence']}")

# By category
for category, count in stats['by_category'].items():
    print(f"{category}: {count}")

# By date (last 30 days)
for date, count in stats['by_date'].items():
    print(f"{date}: {count}")
```

## Search Features

### 1. Text Search

Searches across:
- OCR extracted text
- Keywords
- Vision descriptions
- Filenames

```python
results = search.search(query="database timeout")
```

### 2. Category Filter

```python
results = search.search(category="ERROR")
# Returns only ERROR screenshots
```

### 3. Date Range

```python
from datetime import datetime

results = search.search(
    date_from=datetime(2025, 12, 1),
    date_to=datetime(2025, 12, 7)
)
```

### 4. Confidence Filter

```python
results = search.search(min_confidence=0.8)
# Returns only high-confidence classifications
```

### 5. Tag Filter

```python
results = search.search(tags=["important", "review"])
```

### 6. Combined Filters

```python
results = search.search(
    query="database",
    category="ERROR",
    date_from=week_ago,
    date_to=today,
    min_confidence=0.8,
    tags=["critical"],
    limit=50
)
```

## Search Ranking

Results ranked by:
1. **Relevance score** - Term weight from search_terms table
2. **Recency** - Newer screenshots ranked higher
3. **Confidence** - Higher confidence ranked higher

```python
# Full-text search includes relevance_score
results = search.full_text_search("database")

for result in results:
    score = result.get('relevance_score', 0)
    print(f"Score: {score:.2f} - {result['current_filename']}")
```

## Performance Tips

### 1. Use Indexes

All search columns are indexed:
- `search_terms.term` - Fast text search
- `screenshots.category` - Fast category filter
- `screenshots.created_date` - Fast date range
- `screenshots.file_hash` - Fast duplicate detection

### 2. Limit Results

```python
# Limit to reasonable number
results = search.search(query="database", limit=100)
```

### 3. Rebuild Index Periodically

```python
# If search becomes slow
indexer.rebuild_index()
```

### 4. Vacuum Database

```python
import sqlite3
conn = sqlite3.connect("data/screenshots.db")
conn.execute("VACUUM")
conn.close()
```

## Database Backup

### Manual Backup

```python
import shutil
from pathlib import Path

# Backup database
shutil.copy(
    "data/screenshots.db",
    f"data/backups/screenshots_{datetime.now():%Y%m%d}.db"
)
```

### Automated Backup

```python
from datetime import datetime
import shutil

def backup_database(db_path: Path, backup_dir: Path):
    """Backup database with timestamp."""
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"screenshots_{timestamp}.db"
    shutil.copy(db_path, backup_path)
    return backup_path

# Use
backup_path = backup_database(
    Path("data/screenshots.db"),
    Path("data/backups")
)
```

## Complete Pipeline

```python
from pathlib import Path
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from src.agents.classifier_agent import ClassifierAgent
from src.agents.organizer_agent import OrganizerAgent
from src.agents.indexer_agent import IndexerAgent
from src.utils.search_engine import SearchEngine

# Initialize agents
ocr = OCRAgent()
vision = VisionAgent()
classifier = ClassifierAgent()
organizer = OrganizerAgent(
    base_folder=Path("./organized"),
    db_path=Path("data/screenshots.db")
)
indexer = IndexerAgent(Path("data/screenshots.db"))
search = SearchEngine(Path("data/screenshots.db"))

# Process screenshot
image_path = Path("screenshot.png")

# 1. Extract text
ocr_text = ocr.extract_text(image_path)

# 2. Analyze image
vision_analysis = vision.analyze_image(image_path, ocr_text=ocr_text)

# 3. Classify
classification = classifier.classify(ocr_text, vision_analysis=vision_analysis)

# 4. Organize
org_result = organizer.organize(image_path, classification)

# 5. Index
screenshot_id = indexer.index_screenshot(
    image_path,
    processing_result,
    classification,
    org_result.new_filename,
    org_result.destination_path
)

# 6. Search
results = search.search(query="database")
print(f"Found {len(results)} similar screenshots")
```

## Testing

```bash
# Run tests
pytest tests/test_indexer_agent.py -v
pytest tests/test_search_engine.py -v

# Run examples
python examples/search_example.py
```

## Troubleshooting

### Issue: Search returns no results
**Solution:** Rebuild search index

### Issue: Database locked
**Solution:** Close all connections, check for long-running queries

### Issue: Slow searches
**Solution:** Rebuild index, vacuum database, add more indexes

### Issue: Large database size
**Solution:** Remove old thumbnails, vacuum database

## Next Steps

1. Build main orchestrator
2. Add web UI for search
3. Implement export functionality
4. Add batch operations
