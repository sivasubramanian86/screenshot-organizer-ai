# 🚀 Setup Instructions - Screenshot Organizer

## Quick Start (5 minutes)

### Step 1: Install Python Dependencies
```bash
cd screenshot-organizer-ai
pip install -r requirements.txt
```

### Step 2: Install Tesseract OCR

**Windows:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (install to default location)
3. Add to PATH:
   ```bash
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```
4. Verify:
   ```bash
   tesseract --version
   ```

**Mac:**
```bash
brew install tesseract
tesseract --version
```

### Step 3: Configure API Key
```bash
# Copy example file
copy config\.env.example config\.env  # Windows
cp config/.env.example config/.env    # Mac

# Edit config/.env and add your Claude API key
notepad config\.env  # Windows
nano config/.env     # Mac
```

Add your key:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

Get API key: https://console.anthropic.com/

### Step 4: Initialize Database
```bash
python -c "from src.utils.database import DatabaseManager; from pathlib import Path; db = DatabaseManager(Path('data/screenshots.db')); db.connect(); db.initialize_schema(); print('✅ Database ready!')"
```

### Step 5: Test Installation
```bash
python -c "from src.utils.platform_utils import get_screenshot_folder, get_os_type; print(f'OS: {get_os_type()}'); print(f'Screenshot folder: {get_screenshot_folder()}')"
```

## File Structure Created

```
screenshot-organizer-ai/
├── src/
│   ├── __init__.py ✅
│   ├── agents/
│   │   └── __init__.py ✅
│   ├── schemas/
│   │   ├── __init__.py ✅
│   │   └── models.py ✅ (Pydantic models)
│   └── utils/
│       ├── __init__.py ✅
│       ├── platform_utils.py ✅ (OS detection)
│       └── database.py ✅ (SQLite schema)
├── tests/
│   └── __init__.py ✅
├── config/
│   ├── config.yaml ✅
│   └── .env.example ✅
├── data/ (database will be created here)
├── logs/ (logs will be written here)
├── requirements.txt ✅
├── pyproject.toml ✅
├── .gitignore ✅
└── README.md ✅
```

## What Each File Does

### Core Files
- **requirements.txt**: All Python dependencies
- **src/schemas/models.py**: Pydantic data models with type hints
- **src/utils/database.py**: SQLite schema and database manager
- **src/utils/platform_utils.py**: Cross-platform OS detection and paths

### Configuration
- **config/config.yaml**: Main settings (folders, processing options)
- **config/.env**: API keys (create from .env.example)

### Development
- **pyproject.toml**: Code quality tools (black, ruff, mypy)
- **.gitignore**: Files to exclude from git

## Database Schema

The database has 3 tables:

### 1. screenshots
Stores all screenshot data:
- File metadata (path, size, dimensions)
- OCR extracted text
- Vision API analysis
- Classification (category, keywords)
- Thumbnail (BLOB)

### 2. search_index (FTS5)
Full-text search virtual table:
- Automatically synced with screenshots table
- Search across filenames, OCR text, descriptions

### 3. processing_log
Audit trail:
- All operations (insert, move, rename, delete)
- Enables rollback functionality
- Error tracking

## Next Steps

Now you're ready to implement the agents:

1. **Monitor Agent** - Watch for new screenshots
2. **OCR Agent** - Extract text with Tesseract
3. **Vision Agent** - Analyze with Claude Vision API
4. **Classifier Agent** - Categorize and extract keywords
5. **Organizer Agent** - Rename and move files
6. **Indexer Agent** - Store in database

Use the prompts in your `amazon-q-prompts.md` file to generate each agent!

## Troubleshooting

### Tesseract not found
```bash
# Windows - Check PATH
where tesseract

# Mac - Check installation
which tesseract
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database errors
```bash
# Delete and recreate
del data\screenshots.db  # Windows
rm data/screenshots.db   # Mac

# Then run initialization again
```

## Testing Your Setup

```python
# Test 1: Platform detection
from src.utils.platform_utils import get_os_type, get_screenshot_folder
print(f"OS: {get_os_type()}")
print(f"Screenshots: {get_screenshot_folder()}")

# Test 2: Database
from src.utils.database import DatabaseManager
from pathlib import Path
db = DatabaseManager(Path("data/screenshots.db"))
db.connect()
print("✅ Database connected")

# Test 3: Pydantic models
from src.schemas.models import ScreenshotMetadata
from datetime import datetime
metadata = ScreenshotMetadata(
    file_path="test.png",
    original_filename="test.png",
    file_size_bytes=1024,
    width=1920,
    height=1080,
    format="PNG",
    created_timestamp=datetime.now(),
    modified_timestamp=datetime.now(),
    file_hash="abc123"
)
print(f"✅ Model created: {metadata.original_filename}")
```

All tests passing? You're ready to build the agents! 🎉
