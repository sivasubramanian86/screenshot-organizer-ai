# 📝 Screenshot Organizer - Code Conventions

## File Organization

### Project Structure

```
src/
├── agents/              # One agent per file
│   ├── __init__.py
│   ├── monitor_agent.py
│   ├── ocr_agent.py
│   ├── vision_agent.py
│   ├── classifier_agent.py
│   ├── naming_agent.py
│   ├── organizer_agent.py
│   └── indexer_agent.py
├── utils/               # Utility modules
│   ├── __init__.py
│   ├── database.py
│   ├── config.py
│   ├── platform_utils.py
│   ├── logger.py
│   └── search_engine.py
├── schemas/             # Data models
│   ├── __init__.py
│   └── models.py
├── __init__.py
├── config.py            # Configuration loader
└── main.py              # Main orchestrator
```

### One Agent Per File

```python
# src/agents/ocr_agent.py
"""OCR agent for text extraction."""

class OCRAgent:
    """Extract text from images using Tesseract."""
    pass
```

## Naming Conventions

### Classes

**PascalCase:**

```python
class OCRAgent:
    pass

class VisionAgent:
    pass

class ScreenshotMetadata:
    pass
```

### Functions and Methods

**snake_case:**

```python
def extract_text(image_path: Path) -> str:
    pass

def analyze_image(file_path: Path) -> VisionAnalysis:
    pass

def get_screenshot_folder() -> Path:
    pass
```

### Constants

**UPPER_SNAKE_CASE:**

```python
MAX_FILE_SIZE_MB = 50
DEFAULT_CONFIDENCE = 0.6
VALID_EXTENSIONS = [".png", ".jpg", ".jpeg"]
```

### Private Methods

**Leading underscore:**

```python
class OCRAgent:
    def extract_text(self, image_path: Path) -> str:
        """Public method."""
        return self._process_image(image_path)
    
    def _process_image(self, image_path: Path) -> str:
        """Private helper method."""
        pass
```

### Variables

**snake_case:**

```python
file_path = Path("screenshot.png")
ocr_text = "Extracted text"
confidence_score = 0.92
```

## Docstring Format

### Module Docstrings

```python
"""OCR agent for extracting text from screenshots using Tesseract.

This module provides the OCRAgent class which handles text extraction
from images with caching support.
"""
```

### Class Docstrings

```python
class OCRAgent:
    """Extract text from images using Tesseract OCR.
    
    Features:
    - Text extraction with Tesseract
    - Result caching by file hash
    - Support for multiple languages
    - Graceful handling of images without text
    
    Example:
        >>> ocr = OCRAgent()
        >>> text = ocr.extract_text(Path("screenshot.png"))
        >>> print(text)
        'Extracted text content'
    """
```

### Function Docstrings

```python
def extract_text(self, image_path: Path) -> str:
    """Extract text from image using OCR.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Extracted text string (empty if no text found)
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image file is too large (>50MB)
        RuntimeError: If Tesseract is not installed
        
    Example:
        >>> ocr = OCRAgent()
        >>> text = ocr.extract_text(Path("screenshot.png"))
    """
```

### Type Hints in Docstrings

```python
def classify(
    self,
    ocr_text: str,
    vision_analysis: VisionAnalysis
) -> ClassificationResult:
    """Classify screenshot and extract keywords.
    
    Args:
        ocr_text: Text extracted from OCR
        vision_analysis: Vision API analysis result
        
    Returns:
        ClassificationResult with category, keywords, and confidence
    """
```

## Import Organization

### Order

1. Standard library
2. Third-party packages
3. Local imports

```python
# 1. Standard library
import os
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# 2. Third-party packages
import anthropic
from PIL import Image
from loguru import logger
import pytesseract

# 3. Local imports
from ..schemas.models import VisionAnalysis, ClassificationResult
from ..utils.logger import setup_logging
from ..utils.config import load_config
```

### Import Style

```python
# ✅ Good: Specific imports
from pathlib import Path
from typing import Optional

# ❌ Bad: Wildcard imports
from pathlib import *
from typing import *

# ✅ Good: Grouped imports
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from src.agents.classifier_agent import ClassifierAgent

# ❌ Bad: One per line when related
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from src.agents.classifier_agent import ClassifierAgent
```

## Line Length

**Maximum: 100 characters**

```python
# ✅ Good: Within 100 characters
def process_screenshot(file_path: Path, config: Config) -> ProcessingResult:
    pass

# ❌ Bad: Over 100 characters
def process_screenshot_with_very_long_function_name_that_exceeds_limit(file_path: Path, config: Config) -> ProcessingResult:
    pass

# ✅ Good: Break long lines
result = classifier.classify(
    ocr_text=ocr_text,
    vision_analysis=vision_analysis
)

# ✅ Good: Break long strings
error_message = (
    "Tesseract OCR is not installed. "
    "Windows: Download from GitHub. "
    "Mac: brew install tesseract"
)
```

## Error Messages

### Specific and Actionable

```python
# ✅ Good: Specific with solution
raise FileNotFoundError(
    f"Screenshot folder does not exist: {folder_path}\n"
    f"Please create the folder or specify a different path."
)

# ❌ Bad: Generic
raise FileNotFoundError("Folder not found")

# ✅ Good: Actionable
raise ValueError(
    "Claude API key not found. Set ANTHROPIC_API_KEY environment variable.\n"
    "Get your key from: https://console.anthropic.com/"
)

# ❌ Bad: Not actionable
raise ValueError("API key missing")
```

### Include Context

```python
# ✅ Good: Include context
logger.error(f"OCR failed for {image_path.name}: {error}")

# ❌ Bad: No context
logger.error(f"OCR failed: {error}")

# ✅ Good: Include values
logger.warning(
    f"Low confidence ({confidence:.2f}), skipping auto-organization"
)

# ❌ Bad: No values
logger.warning("Low confidence, skipping")
```

## Comment Style

### Explain WHY, Not WHAT

```python
# ✅ Good: Explains why
# Wait for file to be fully written before processing
time.sleep(1)

# ❌ Bad: States the obvious
# Sleep for 1 second
time.sleep(1)

# ✅ Good: Explains reasoning
# Use exponential backoff to avoid overwhelming the API
wait_time = 2 ** attempt

# ❌ Bad: Restates code
# Calculate wait time
wait_time = 2 ** attempt
```

### When to Comment

```python
# ✅ Good: Complex logic
# Truncate at underscore boundary to keep words intact
last_underscore = truncated_name.rfind('_')
if last_underscore > available * 0.7:
    truncated_name = truncated_name[:last_underscore]

# ✅ Good: Non-obvious behavior
# PIL thumbnail modifies image in-place, so we need to copy
img_copy = img.copy()
img_copy.thumbnail(size)

# ❌ Bad: Obvious code
# Create a Path object
file_path = Path("screenshot.png")
```

## Module Structure

### Standard Order

```python
"""Module docstring."""

# 1. Imports
import os
from pathlib import Path
from typing import Optional

# 2. Constants
MAX_FILE_SIZE_MB = 50
DEFAULT_TIMEOUT = 60

# 3. Classes
class OCRAgent:
    """OCR agent class."""
    pass

# 4. Functions
def helper_function() -> None:
    """Helper function."""
    pass

# 5. Main execution
if __name__ == "__main__":
    main()
```

## Type Hints

### Always Use Type Hints

```python
# ✅ Good: Full type hints
def extract_text(self, image_path: Path) -> str:
    pass

def classify(
    self,
    ocr_text: str,
    vision_analysis: Optional[VisionAnalysis] = None
) -> ClassificationResult:
    pass

# ❌ Bad: No type hints
def extract_text(self, image_path):
    pass
```

### Complex Types

```python
from typing import List, Dict, Optional, Union, Tuple

# List of strings
keywords: List[str] = ["error", "database"]

# Dictionary
stats: Dict[str, int] = {"total": 100, "success": 95}

# Optional
ocr_text: Optional[str] = None

# Union
result: Union[str, None] = get_text()

# Tuple
dimensions: Tuple[int, int] = (1920, 1080)
```

## Code Formatting

### Black Formatter

```bash
# Format all code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Example Formatting

```python
# ✅ Good: Black formatted
def process_screenshot(
    file_path: Path,
    config: Config,
    dry_run: bool = False
) -> ProcessingResult:
    """Process screenshot."""
    result = ProcessingResult(
        metadata=metadata,
        ocr_text=ocr_text,
        vision_analysis=vision_analysis
    )
    return result

# ❌ Bad: Not formatted
def process_screenshot(file_path: Path, config: Config, dry_run: bool=False)->ProcessingResult:
    result=ProcessingResult(metadata=metadata,ocr_text=ocr_text,vision_analysis=vision_analysis)
    return result
```

## Error Handling Patterns

### Try-Except-Finally

```python
# ✅ Good: Specific exceptions
try:
    text = ocr.extract_text(image_path)
except FileNotFoundError:
    logger.error(f"File not found: {image_path}")
    return None
except ValueError as e:
    logger.error(f"Invalid file: {e}")
    return None
finally:
    # Cleanup
    pass

# ❌ Bad: Bare except
try:
    text = ocr.extract_text(image_path)
except:
    return None
```

### Context Managers

```python
# ✅ Good: Use context managers
with open(file_path, 'r') as f:
    content = f.read()

# ✅ Good: Database connections
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM screenshots")
```

## Function Length

### Keep Functions Short

```python
# ✅ Good: Short, focused function
def extract_text(self, image_path: Path) -> str:
    """Extract text from image."""
    self._validate_file(image_path)
    image_hash = self._get_file_hash(image_path)
    
    cached_text = self._get_cached_text(image_hash)
    if cached_text is not None:
        return cached_text
    
    text = self._extract_with_tesseract(image_path)
    self._cache_text(image_hash, text)
    return text

# ❌ Bad: Too long (>50 lines)
def extract_text(self, image_path: Path) -> str:
    # 100+ lines of code
    pass
```

## Class Design

### Single Responsibility

```python
# ✅ Good: Single responsibility
class OCRAgent:
    """Extract text from images."""
    
    def extract_text(self, image_path: Path) -> str:
        pass

class CacheManager:
    """Manage OCR result cache."""
    
    def get(self, key: str) -> Optional[str]:
        pass
    
    def set(self, key: str, value: str) -> None:
        pass

# ❌ Bad: Multiple responsibilities
class OCRAgent:
    """Extract text and manage cache and validate files."""
    pass
```

## Testing Conventions

### Test Function Names

```python
# ✅ Good: Descriptive test names
def test_extract_text_success():
    pass

def test_extract_text_with_no_text():
    pass

def test_extract_text_file_not_found():
    pass

# ❌ Bad: Generic names
def test_1():
    pass

def test_ocr():
    pass
```

### Arrange-Act-Assert

```python
def test_extract_text_success(test_image):
    """Test successful text extraction."""
    # Arrange
    ocr = OCRAgent()
    
    # Act
    text = ocr.extract_text(test_image)
    
    # Assert
    assert isinstance(text, str)
    assert len(text) > 0
```

## Related Documentation

- **Agent Details:** `AGENTS.md`
- **Workflow:** `.kiro/steering/workflow.md`
- **Standards:** `.kiro/steering/steering.md`
- **Testing:** `.kiro/steering/testing-standards.md`
