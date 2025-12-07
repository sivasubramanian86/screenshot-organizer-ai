# 🚀 Screenshot Organizer - Complete Usage Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR
**Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
**Mac:** `brew install tesseract`

### 3. Configure API Key
```bash
# Copy example env file
copy config\.env.example config\.env  # Windows
cp config/.env.example config/.env    # Mac

# Edit config/.env
ANTHROPIC_API_KEY=your_api_key_here
```

### 4. Initialize Database
```bash
python -c "from src.utils.database import DatabaseManager; from pathlib import Path; db = DatabaseManager(Path('data/screenshots.db')); db.connect(); db.initialize_schema(); print('✅ Database ready!')"
```

### 5. Run
```bash
# Dry run first (see what would happen)
python -m src.main --dry-run

# Actually run
python -m src.main
```

## Command-Line Options

### Basic Usage
```bash
python -m src.main
```

### Dry Run Mode
```bash
# Show what would happen without moving files
python -m src.main --dry-run
```

### Debug Mode
```bash
# Enable detailed logging
python -m src.main --debug
```

### Custom Config
```bash
# Use different config file
python -m src.main --config path/to/config.yaml
```

### Show Statistics
```bash
# Display database statistics
python -m src.main --stats
```

### Search
```bash
# Search indexed screenshots
python -m src.main --search "database error"
```

## Configuration

Edit `config/config.yaml`:

```yaml
# Paths
source_folders:
  windows: 'C:\Users\{USERNAME}\Pictures\Screenshots'
  mac: '~/Pictures/Screenshots'
output_base: './organized_screenshots'

# Processing
dry_run: false
min_confidence: 0.6  # Only auto-organize if >= this

# AI Settings
ocr:
  enabled: true
claude_vision:
  model: 'claude-3-5-sonnet-20241022'
  max_tokens: 1000

# Database
database:
  path: './data/screenshots.db'
  auto_backup: true
```

## Processing Pipeline

For each new screenshot:

1. **Monitor** - Detect new file
2. **OCR** - Extract text (Tesseract)
3. **Vision** - Analyze image (Claude Vision API)
4. **Classify** - Categorize and extract keywords
5. **Organize** - Rename and move to folder
6. **Index** - Add to searchable database

## Output Structure

```
organized_screenshots/
├── 2025-12/
│   ├── Error/
│   │   ├── Database/
│   │   │   └── 2025-12-07_Error-DB_Database_Timeout_a3f2.png
│   │   └── Network/
│   ├── Code/
│   │   ├── Python/
│   │   │   └── 2025-12-07_Code-Python_Async_Await_b1e9.png
│   │   └── JavaScript/
│   ├── Ui/
│   │   └── Dashboard/
│   └── Data/
```

## Features

### Automatic Monitoring
- Watches screenshot folder for new files
- Waits for file to be fully written
- Filters out temporary files

### Intelligent Classification
- 7 categories: ERROR, CODE, UI, DOCUMENTATION, DATA, COMMUNICATION, OTHER
- Confidence scoring (0.0-1.0)
- Keyword extraction

### Smart Naming
- Format: `DATE_CATEGORY-CODE_KEYWORDS_HASH.ext`
- Example: `2025-12-07_Error-504_DatabaseTimeout_a3f2.png`
- Windows-safe (200 char limit)

### Searchable Database
- Full-text search across OCR text and keywords
- Filter by category, date, tags
- Relevance scoring

### Error Handling
- Graceful error recovery
- Continues processing on failures
- Detailed logging

### Checkpointing
- Saves progress every 10 files
- Resume from last checkpoint if crashed
- State stored in `data/checkpoint.json`

### Graceful Shutdown
- Press Ctrl+C to stop
- Saves checkpoint before exit
- Shows final statistics

## Statistics

View statistics:
```bash
python -m src.main --stats
```

Output:
```
📊 Statistics:
Total screenshots: 150
Average confidence: 0.87

By category:
  ERROR: 45
  CODE: 38
  UI: 32
  DATA: 20
  OTHER: 15
```

## Search

Search indexed screenshots:
```bash
# Basic search
python -m src.main --search "database"

# Advanced search
python -m src.main --search "category:ERROR date:2025-12-01..2025-12-07"
```

## Troubleshooting

### Tesseract Not Found
```bash
# Windows
set PATH=%PATH%;C:\Program Files\Tesseract-OCR

# Mac
brew install tesseract
```

### Permission Denied (Mac)
Grant access in: System Preferences → Security & Privacy → Files and Folders

### API Rate Limiting
Adjust `rate_limit_delay_seconds` in config.yaml

### Low Confidence Classifications
Increase `min_confidence` in config.yaml to skip uncertain classifications

## Performance Tips

### 1. Adjust Confidence Threshold
```yaml
processing:
  min_confidence: 0.8  # Higher = more selective
```

### 2. Disable OCR if Not Needed
```yaml
ocr:
  enabled: false
```

### 3. Process Existing Screenshots
```bash
# Process all files in folder once
python -m src.main --reprocess
```

### 4. Backup Database
```yaml
database:
  auto_backup: true
  backup_dir: './data/backups'
```

## Logs

Logs stored in: `logs/organizer.log`

View logs:
```bash
# Windows
type logs\organizer.log

# Mac/Linux
tail -f logs/organizer.log
```

## Database

Location: `data/screenshots.db`

Backup:
```bash
# Manual backup
copy data\screenshots.db data\backups\screenshots_backup.db
```

Search:
```python
from src.utils.search_engine import SearchEngine
from pathlib import Path

search = SearchEngine(Path("data/screenshots.db"))
results = search.search(query="database", category="ERROR")
```

## Rollback

Undo recent file moves:
```python
from src.agents.organizer_agent import OrganizerAgent
from pathlib import Path

organizer = OrganizerAgent(
    base_folder=Path("./organized_screenshots"),
    db_path=Path("data/screenshots.db")
)

# Rollback last 24 hours
count = organizer.rollback(hours=24)
print(f"Rolled back {count} files")
```

## Testing

Run tests:
```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_main.py -v

# With coverage
pytest --cov=src --cov-report=html
```

## Development

### Code Quality
```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Add New Category
1. Update `classifier_agent.py` categories
2. Update `naming_agent.py` category codes
3. Update `organizer_agent.py` folder structure

## Support

For issues:
1. Check logs: `logs/organizer.log`
2. Run with `--debug` flag
3. Check database: `data/screenshots.db`
4. Review checkpoint: `data/checkpoint.json`

## License

MIT License - See LICENSE file
