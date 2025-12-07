# Technology Stack

## Programming Language
- **Python 3.11+**: Core language with modern type hints and features
- Target version: Python 3.11 (specified in pyproject.toml)

## Core Dependencies

### AI & Vision APIs
- **anthropic**: Claude API client for vision analysis
- **google-generativeai**: Gemini API client (FREE option)
- **boto3**: AWS SDK for Bedrock integration
- Multiple vision backends supported via adapter pattern

### OCR & Image Processing
- **pytesseract**: Python wrapper for Tesseract OCR
- **Pillow (PIL)**: Image manipulation and thumbnail generation
- **Tesseract OCR**: External dependency (system-level installation required)

### File System Monitoring
- **watchdog**: Cross-platform file system event monitoring
- Supports Windows, macOS, and Linux
- Real-time detection of new screenshots

### Data Management
- **SQLite3**: Built-in Python database (no external installation)
- **FTS5**: Full-text search extension (built into SQLite)
- **Pydantic**: Data validation and settings management
- Type-safe data models throughout application

### Configuration & Environment
- **PyYAML**: YAML configuration file parsing
- **python-dotenv**: Environment variable management
- Supports multiple .env files for different API backends

### Utilities
- **pathlib**: Modern path handling (Python standard library)
- **logging**: Structured logging with rotation
- **argparse**: Command-line argument parsing

## Development Tools

### Code Quality
- **black**: Code formatter (line-length: 100)
- **ruff**: Fast Python linter (replaces flake8, isort)
- **mypy**: Static type checker with strict settings

### Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- Coverage reports: HTML and terminal output

### Build & Packaging
- **pyproject.toml**: Modern Python project configuration
- **requirements.txt**: Production dependencies
- **requirements_gemini.txt**: Gemini-specific dependencies
- **requirements_bedrock.txt**: AWS Bedrock dependencies

## Configuration Files

### pyproject.toml
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=src --cov-report=html --cov-report=term"
```

### config.yaml Structure
- **Paths**: Source folders, output directories
- **Monitoring**: File extensions, polling intervals
- **AI Settings**: OCR, Claude/Gemini/Bedrock configuration
- **Processing**: Confidence thresholds, retries, timeouts
- **Organization**: Filename rules, preservation options
- **Database**: Path, backups, thumbnails
- **Logging**: Levels, file rotation, console output

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt          # Claude
pip install -r requirements_gemini.txt   # Gemini (FREE)
pip install -r requirements_bedrock.txt  # AWS Bedrock
```

### Running the Application
```bash
# Basic usage
python src/main.py

# Custom screenshot folder
python src/main.py --folder "C:\Users\YourName\Pictures\Screenshots"

# Process existing screenshots
python src/main.py --process-existing

# Module execution
python -m src
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_classifier_agent.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/

# Fix linting issues automatically
ruff check --fix src/ tests/
```

### Database Management
```bash
# Initialize database
python -c "from src.utils.database import DatabaseManager; from pathlib import Path; db = DatabaseManager(Path('data/screenshots.db')); db.connect(); db.initialize_schema(); print('Database initialized!')"

# Run search example
python examples/search_example.py
```

## External Dependencies

### System Requirements
1. **Tesseract OCR** (required)
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Mac: `brew install tesseract`
   - Linux: `apt-get install tesseract-ocr`

2. **Python 3.11+** (required)
   - Download from https://www.python.org/downloads/

3. **API Keys** (choose one)
   - Claude: https://console.anthropic.com/
   - Gemini: https://makersuite.google.com/app/apikey (FREE)
   - AWS Bedrock: AWS account with Bedrock access

## Platform Support

### Windows
- Default screenshot path: `C:\Users\{USERNAME}\Pictures\Screenshots`
- Batch scripts for setup: `setup_gemini.bat`, `setup_bedrock.bat`
- Tested on Windows 10/11

### macOS
- Default screenshot path: `~/Pictures/Screenshots`
- Homebrew for Tesseract installation
- Requires file system permissions for monitoring

### Linux
- Default screenshot path: `~/Pictures`
- Package manager for Tesseract installation
- Tested on Ubuntu/Debian

## Architecture Patterns

### Type Safety
- Pydantic models for all data structures
- mypy strict mode enabled
- Type hints throughout codebase

### Configuration Management
- YAML for structured configuration
- Environment variables for secrets
- Platform-specific defaults with overrides

### Error Handling
- Graceful degradation for missing features
- Retry logic with exponential backoff
- Comprehensive logging for debugging

### Testing Strategy
- Unit tests for individual agents
- Integration tests for pipeline
- Mock external dependencies (APIs, file system)
- Coverage target: >80%

## Performance Considerations

### Caching
- OCR results cached by file hash
- Avoids redundant processing
- Configurable cache directory

### Parallel Processing
- Optional parallel OCR and vision analysis
- Configurable via config.yaml
- Trade-off: speed vs. API rate limits

### Database Optimization
- FTS5 for fast full-text search
- Indexed columns for common queries
- Thumbnail storage as BLOB (not separate files)

### Resource Limits
- Max image size: 50MB (configurable)
- Thumbnail size: 150x150 (configurable)
- Max filename length: 200 characters (configurable)
