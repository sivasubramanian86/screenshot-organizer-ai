# 🎯 Screenshot Organizer - Development Standards & Quality Gates

## Code Quality Standards

### Python Version & Style

- **Python:** 3.11+ required
- **Style Guide:** PEP 8
- **Formatter:** black (line length: 100)
- **Linter:** ruff
- **Type Checker:** mypy (strict mode)

### Type Hints

**ALL functions must have type hints:**

```python
# ✅ Good
def process_screenshot(file_path: Path, config: Config) -> ProcessingResult:
    """Process a screenshot through the pipeline."""
    pass

# ❌ Bad
def process_screenshot(file_path, config):
    pass
```

**Use Pydantic for data validation:**

```python
from pydantic import BaseModel, Field

class ScreenshotMetadata(BaseModel):
    file_path: Path
    file_size_bytes: int
    confidence: float = Field(ge=0.0, le=1.0)
```

### Code Organization

```python
# 1. Imports (grouped: stdlib, 3rd party, local)
import os
from pathlib import Path
from typing import Optional

import anthropic
from PIL import Image

from ..schemas.models import ProcessingResult
from ..utils.logger import logger

# 2. Constants
MAX_FILE_SIZE_MB = 50
DEFAULT_CONFIDENCE = 0.5

# 3. Classes/Functions
class OCRAgent:
    pass

# 4. Main execution
if __name__ == "__main__":
    main()
```

## Testing Strategy

### Test Coverage

- **Target:** 80%+ code coverage for `src/`
- **Tool:** pytest with pytest-cov
- **Report:** HTML coverage report

### Test Structure

```python
# tests/test_ocr_agent.py
import pytest
from pathlib import Path
from src.agents.ocr_agent import OCRAgent

@pytest.fixture
def test_image(tmp_path):
    """Create a test image."""
    # Setup code
    return image_path

class TestOCRAgent:
    """Test OCRAgent class."""
    
    def test_extract_text_success(self, test_image):
        """Test successful text extraction."""
        ocr = OCRAgent()
        text = ocr.extract_text(test_image)
        assert isinstance(text, str)
    
    def test_extract_text_no_text(self, empty_image):
        """Test image with no text."""
        ocr = OCRAgent()
        text = ocr.extract_text(empty_image)
        assert text == ""
```

### Mock Strategy

**Mock external APIs:**

```python
from unittest.mock import Mock, patch

@patch('anthropic.Anthropic')
def test_vision_analysis(mock_anthropic_class):
    """Test vision analysis with mocked API."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = '{"description": "test"}'
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_class.return_value = mock_client
    
    agent = VisionAgent(api_key="test-key")
    agent.client = mock_client
    result = agent.analyze_image(test_image)
    
    assert result.description == "test"
```

### Integration Tests

```python
def test_full_pipeline(tmp_path):
    """Test complete processing pipeline."""
    # Create test image
    # Run through all agents
    # Verify final result
    pass
```

## Error Handling

### Exception Hierarchy

```python
class ScreenshotOrganizerError(Exception):
    """Base exception for all errors."""
    pass

class OCRError(ScreenshotOrganizerError):
    """OCR processing failed."""
    pass

class VisionAPIError(ScreenshotOrganizerError):
    """Vision API call failed."""
    pass

class ClassificationError(ScreenshotOrganizerError):
    """Classification failed."""
    pass
```

### Graceful Degradation

```python
def process_screenshot(file_path: Path) -> bool:
    """Process screenshot with graceful error handling."""
    try:
        # Step 1: OCR
        try:
            ocr_text = ocr.extract_text(file_path)
        except OCRError as e:
            logger.warning(f"OCR failed: {e}")
            ocr_text = ""  # Continue without OCR
        
        # Step 2: Vision
        try:
            vision_analysis = vision.analyze_image(file_path, ocr_text)
        except VisionAPIError as e:
            logger.error(f"Vision failed: {e}")
            return False  # Cannot continue without vision
        
        # Continue with remaining steps...
        return True
    
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return False
```

### Retry Logic

```python
def _retry_with_backoff(self, func, *args, **kwargs):
    """Retry with exponential backoff."""
    for attempt in range(self.max_retries):
        try:
            return func(*args, **kwargs)
        except anthropic.RateLimitError:
            if attempt == self.max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.warning(f"Rate limited, waiting {wait_time}s")
            time.sleep(wait_time)
```

## Logging

### Format

```
[2025-12-07 14:30:15] [INFO] [ocr_agent:extract_text:45] Extracted 150 characters
[2025-12-07 14:30:18] [ERROR] [vision_agent:analyze_image:78] API call failed: timeout
```

### Levels

- **DEBUG:** Development only (verbose)
- **INFO:** Production (important events)
- **WARNING:** Recoverable errors
- **ERROR:** Failures that need attention

### Implementation

```python
from loguru import logger

# Setup
logger.add(
    "logs/organizer.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level="INFO",
    rotation="10 MB",
    retention=5
)

# Usage
logger.info(f"Processing: {file_path.name}")
logger.warning(f"Low confidence: {confidence:.2f}")
logger.error(f"Failed: {error}")
```

### What NOT to Log

```python
# ❌ Don't log sensitive data
logger.info(f"API key: {api_key}")  # NO!
logger.info(f"Full file path: {file_path}")  # NO!

# ✅ Log safely
logger.info(f"Processing file: {file_path.name}")
logger.info("API key configured")
```

## Database

### SQLite Best Practices

**Use parameterized queries:**

```python
# ✅ Good (prevents SQL injection)
cursor.execute(
    "SELECT * FROM screenshots WHERE category = ?",
    (category,)
)

# ❌ Bad (SQL injection risk)
cursor.execute(
    f"SELECT * FROM screenshots WHERE category = '{category}'"
)
```

**Use transactions:**

```python
conn = sqlite3.connect(db_path)
try:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO screenshots ...")
    cursor.execute("INSERT INTO search_terms ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

**Create indexes:**

```python
cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON screenshots(category)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_date ON screenshots(created_date)")
```

**Use FTS5 for full-text search:**

```python
cursor.execute("""
    CREATE VIRTUAL TABLE search_index USING fts5(
        screenshot_id UNINDEXED,
        ocr_text,
        keywords
    )
""")
```

## API Integration

### Claude Vision API

**Rate limiting:**

```python
# Handle 429 errors
try:
    response = client.messages.create(...)
except anthropic.RateLimitError:
    time.sleep(2)  # Wait and retry
```

**Timeouts:**

```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    timeout=60,  # 60 second timeout
    messages=[...]
)
```

**Cost tracking:**

```python
# Track API usage
stats = {
    'api_calls': 0,
    'tokens_used': 0,
    'estimated_cost': 0.0
}

# After each call
stats['api_calls'] += 1
stats['tokens_used'] += response.usage.total_tokens
stats['estimated_cost'] += calculate_cost(response.usage)
```

### Tesseract OCR

**Language settings:**

```python
text = pytesseract.image_to_string(image, lang='eng')
```

**Error handling:**

```python
try:
    text = pytesseract.image_to_string(image)
except pytesseract.TesseractNotFoundError:
    raise RuntimeError(
        "Tesseract not installed. "
        "Windows: Download from GitHub. "
        "Mac: brew install tesseract"
    )
```

## Security

### API Keys

```python
# ✅ Good: Load from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

# ❌ Bad: Hardcoded
api_key = "sk-ant-api03-xxxxx"  # NEVER DO THIS
```

### File Path Validation

```python
def validate_path(file_path: Path) -> None:
    """Validate file path to prevent directory traversal."""
    # Resolve to absolute path
    abs_path = file_path.resolve()
    
    # Check if within allowed directory
    if not str(abs_path).startswith(str(base_dir.resolve())):
        raise ValueError("Invalid file path")
```

### Sanitize Filenames

```python
def sanitize_filename(filename: str) -> str:
    """Remove dangerous characters."""
    # Remove: / \ : * ? " < > |
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '', filename)
```

## Architecture Patterns

### Agent Pattern

```python
class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def process(self, input_data):
        """Process input and return output."""
        raise NotImplementedError

class OCRAgent(BaseAgent):
    """Concrete agent implementation."""
    
    def process(self, file_path: Path) -> str:
        """Extract text from image."""
        return self.extract_text(file_path)
```

### Config Pattern

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class Config(BaseModel):
    """Application configuration."""
    source_folder: Path
    output_folder: Path
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.6)
    
    @field_validator('source_folder')
    @classmethod
    def validate_folder_exists(cls, v):
        if not v.exists():
            raise ValueError(f"Folder not found: {v}")
        return v
```

### Database Pattern

```python
class DatabaseManager:
    """Manage database connections and transactions."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
    
    def connect(self):
        """Connect to database."""
        self.connection = sqlite3.connect(str(self.db_path))
        return self.connection
    
    def close(self):
        """Close connection."""
        if self.connection:
            self.connection.close()
```

## Key Architectural Decisions

### Sequential vs Parallel Execution

**Decision:** Sequential

**Rationale:**
- Each agent depends on previous agent's output
- Simpler error handling and debugging
- Easier progress tracking and checkpointing
- Avoids race conditions with file operations
- Reduces API rate limiting issues
- Performance acceptable (5-8s per screenshot)

### SQLite vs PostgreSQL/MongoDB

**Decision:** SQLite

**Rationale:**
- Zero configuration (no server setup)
- Single file database (easy backup)
- Fast for <100K screenshots
- FTS5 for full-text search
- ACID transactions
- Cross-platform
- Sufficient for personal use

### Claude Vision vs Open Source Models

**Decision:** Claude Vision API

**Rationale:**
- State-of-the-art accuracy (90%+)
- No GPU required
- No model management
- Handles diverse screenshot types
- Cost acceptable (~$0.003 per image)
- Reliable API with good uptime

### Tesseract vs Cloud OCR

**Decision:** Tesseract (local)

**Rationale:**
- Free (no API costs)
- Privacy (no data sent to cloud)
- Fast (local processing)
- Caching reduces repeated work
- Good accuracy for screenshots
- Cross-platform support

### Watchdog vs OS-Specific APIs

**Decision:** Watchdog library

**Rationale:**
- Cross-platform (Windows, Mac, Linux)
- Well-maintained library
- Simple API
- Handles edge cases (file locks, etc.)
- Better than polling

## Quality Gates

### Pre-Commit Checks

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest tests/ --cov=src --cov-report=html
```

### CI/CD Pipeline

1. **Lint:** ruff check
2. **Format:** black --check
3. **Type Check:** mypy
4. **Test:** pytest with coverage
5. **Coverage:** Must be >= 80%

### Code Review Checklist

- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Tests added for new code
- [ ] No hardcoded secrets
- [ ] Error handling implemented
- [ ] Logging added
- [ ] Documentation updated

## Related Documentation

- **Agent Details:** `AGENTS.md`
- **Workflow:** `.kiro/steering/workflow.md`
- **Testing:** `.kiro/steering/testing-standards.md`
- **Conventions:** `.kiro/steering/code-conventions.md`
