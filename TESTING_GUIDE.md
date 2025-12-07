# 🧪 Testing Guide

## Quick Start Testing

### 1. Install Tesseract OCR (Required)

**Windows:**
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR
# Add to PATH or the app will auto-detect it
```

### 2. Setup Environment

```bash
# Activate virtual environment
venv\Scripts\activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Create .env file with your Claude API key
copy config\.env.example config\.env
# Edit config\.env and add: ANTHROPIC_API_KEY=your_key_here
```

### 3. Initialize Database

```bash
python -c "from src.utils.database import DatabaseManager; from pathlib import Path; db = DatabaseManager(Path('data/screenshots.db')); db.connect(); db.initialize_schema(); print('✅ Database initialized!')"
```

### 4. Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_monitor_agent.py -v

# Run with detailed output
pytest -v -s
```

### 5. Test Individual Agents

**Monitor Agent:**
```bash
python examples/monitor_example.py
```

**OCR + Vision:**
```bash
python examples/ocr_vision_example.py path/to/screenshot.png
```

**Classifier:**
```bash
python examples/classifier_example.py path/to/screenshot.png
```

**Organizer:**
```bash
python examples/organizer_example.py path/to/screenshot.png
```

**Search:**
```bash
python examples/search_example.py "error message"
```

### 6. Test Full Pipeline (Dry Run)

```bash
# Process without moving files
python src/main.py --dry-run --debug
```

### 7. Test with Real Screenshots

```bash
# Create test screenshot folder
mkdir test_screenshots

# Add some screenshots to test_screenshots/

# Process them
python src/main.py --folder test_screenshots --process-existing
```

## Common Issues

### Tesseract Not Found
```bash
# Windows: Add to PATH
set PATH=%PATH%;C:\Program Files\Tesseract-OCR
```

### Missing API Key
```bash
# Make sure config/.env exists with:
ANTHROPIC_API_KEY=sk-ant-...
```

### Database Locked
```bash
# Close any DB browser tools
# Delete data/screenshots.db and reinitialize
```

## Test Coverage Goals

- Overall: 80%+
- Critical agents (OCR, Vision, Classifier): 90%+
- Utils: 85%+

## Performance Benchmarks

- OCR (cached): <1s
- Vision API: 2-4s
- Classification: 1-2s
- Full pipeline: 5-8s per screenshot
- Search: <1s

## Next Steps

1. Run `pytest` to verify all tests pass
2. Try `python src/main.py --dry-run` to test without moving files
3. Process a few test screenshots
4. Check `logs/` for detailed execution logs
5. Query database with `python examples/search_example.py`
