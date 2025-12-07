# 🖼️ AI-Powered Screenshot Organizer

Automatically organize, rename, and index screenshots using OCR and Claude Vision API.

## Features

- **Automatic Monitoring**: Watch screenshot folders for new files (Windows & Mac)
- **OCR Text Extraction**: Extract text using Tesseract
- **AI Vision Analysis**: Analyze image content with Claude Vision API
- **Smart Classification**: Categorize into ERROR, CODE, UI, DOCUMENTATION, DATA, COMMUNICATION, OTHER
- **Intelligent Organization**: Rename and move files to organized folders
- **Searchable Database**: SQLite with full-text search
- **Cross-Platform**: Works on Windows and macOS

## Architecture

```
File Monitor → OCR Agent → Vision Agent → Classifier → Organizer → Indexer
                                                                      ↓
                                                              SQLite Database
```

## Prerequisites

### 1. Python 3.11+
```bash
python --version  # Should be 3.11 or higher
```

### 2. Tesseract OCR
**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR
# Add to PATH: C:\Program Files\Tesseract-OCR
```

**Mac:**
```bash
brew install tesseract
```

### 3. Claude API Key
Get your API key from: https://console.anthropic.com/

## Installation

### 1. Clone/Download Project
```bash
cd screenshot-organizer-ai
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy example env file
copy config\.env.example config\.env  # Windows
cp config/.env.example config/.env    # Mac/Linux

# Edit config/.env and add your Claude API key
ANTHROPIC_API_KEY=your_actual_api_key_here
```

### 5. Initialize Database
```bash
python -c "from src.utils.database import DatabaseManager; from pathlib import Path; db = DatabaseManager(Path('data/screenshots.db')); db.connect(); db.initialize_schema(); print('Database initialized!')"
```

## Configuration

Edit `config/config.yaml` to customize:

- **Watch folders**: Screenshot directories to monitor
- **File extensions**: Supported image formats
- **Organization**: Folder structure and naming
- **Processing**: OCR/Vision settings, retries
- **Claude API**: Model, tokens, timeout

## Usage

### Basic Usage
```bash
python src/main.py
```

### Custom Screenshot Folder
```bash
python src/main.py --folder "C:\Users\YourName\Pictures\Screenshots"
```

### Process Existing Screenshots
```bash
python src/main.py --process-existing
```

## Project Structure

```
screenshot-organizer-ai/
├── src/
│   ├── agents/           # Processing agents
│   │   ├── monitor_agent.py      # File monitoring
│   │   ├── ocr_agent.py          # Text extraction
│   │   ├── vision_agent.py       # Claude Vision
│   │   ├── classifier_agent.py   # Categorization
│   │   ├── organizer_agent.py    # File organization
│   │   └── indexer_agent.py      # Database indexing
│   ├── schemas/
│   │   └── models.py     # Pydantic data models
│   ├── utils/
│   │   ├── platform_utils.py     # OS detection
│   │   ├── database.py           # SQLite schema
│   │   └── config.py             # Config loader
│   └── main.py           # Entry point
├── tests/                # Unit tests
├── config/
│   ├── config.yaml       # Main configuration
│   └── .env              # API keys (not in git)
├── data/
│   └── screenshots.db    # SQLite database
├── logs/                 # Application logs
└── requirements.txt      # Python dependencies
```

## Database Schema

### screenshots table
- Stores all screenshot metadata, OCR text, vision analysis
- Full-text search enabled via FTS5
- Thumbnail storage (BLOB)

### search_index table
- Virtual FTS5 table for fast text search
- Auto-synced with screenshots table via triggers

### processing_log table
- Audit trail for all operations
- Enables rollback functionality

## Development

### Run Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Coverage Report
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
```

## Troubleshooting

### Tesseract Not Found
```bash
# Windows: Add to PATH
set PATH=%PATH%;C:\Program Files\Tesseract-OCR

# Mac: Install via Homebrew
brew install tesseract
```

### Permission Denied (Mac)
Grant Terminal/IDE access to Desktop/Pictures in:
System Preferences → Security & Privacy → Privacy → Files and Folders

### API Rate Limiting
Adjust `rate_limit_delay_seconds` in config.yaml

## Categories

- **ERROR**: Error messages, stack traces, exceptions
- **CODE**: Source code, IDE, terminal, configs
- **UI**: Web/app interfaces, designs, mockups
- **DOCUMENTATION**: Docs, diagrams, flowcharts
- **DATA**: Tables, charts, reports, analytics
- **COMMUNICATION**: Slack, email, messages
- **OTHER**: Everything else

## License

MIT License - See LICENSE file

## Support

For issues and questions, please open a GitHub issue.
