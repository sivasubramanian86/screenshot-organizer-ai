# 🧪 Screenshot Organizer - Testing Standards

## Testing Philosophy

- **Test behavior, not implementation**
- **Mock external dependencies (APIs, file system)**
- **Use fixtures for reusable test data**
- **Aim for 80%+ code coverage**
- **Fast tests (<5 seconds total)**

## Test Structure

### File Naming

```
tests/
├── test_monitor_agent.py
├── test_ocr_agent.py
├── test_vision_agent.py
├── test_classifier_agent.py
├── test_naming_agent.py
├── test_organizer_agent.py
├── test_indexer_agent.py
├── test_search_engine.py
└── test_main.py
```

### Test Class Organization

```python
# tests/test_ocr_agent.py
import pytest
from pathlib import Path
from src.agents.ocr_agent import OCRAgent

class TestOCRAgent:
    """Test OCRAgent class."""
    
    def test_init(self):
        """Test initialization."""
        pass
    
    def test_extract_text_success(self):
        """Test successful text extraction."""
        pass
    
    def test_extract_text_failure(self):
        """Test error handling."""
        pass

class TestOCRIntegration:
    """Integration tests for OCR agent."""
    
    def test_full_workflow(self):
        """Test complete OCR workflow."""
        pass
```

## Fixtures

### Common Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
from PIL import Image

@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create temporary directory."""
    return tmp_path_factory.mktemp("test")

@pytest.fixture
def test_image(tmp_path):
    """Create a test image with text."""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Test Screenshot", fill='black')
    
    image_path = tmp_path / "test.png"
    img.save(image_path)
    return image_path

@pytest.fixture
def empty_image(tmp_path):
    """Create an image without text."""
    img = Image.new('RGB', (200, 200), color='blue')
    image_path = tmp_path / "empty.png"
    img.save(image_path)
    return image_path

@pytest.fixture
def mock_config():
    """Create mock configuration."""
    from src.config import Config
    return Config(
        source_folders={"windows": "C:\\test", "mac": "~/test"},
        output_base="./test_output",
        dry_run=True
    )
```

## Mock Strategy

### Mocking Claude API

```python
from unittest.mock import Mock, patch

@pytest.fixture
def mock_claude_response():
    """Mock Claude API response."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = """{
        "description": "Test screenshot",
        "content_type": "ui",
        "objects_detected": ["button"],
        "keywords": ["test"],
        "has_text": true,
        "confidence": 0.9
    }"""
    return mock_response

@patch('anthropic.Anthropic')
def test_vision_analysis(mock_anthropic_class, mock_claude_response, test_image):
    """Test vision analysis with mocked API."""
    # Setup mock
    mock_client = Mock()
    mock_client.messages.create.return_value = mock_claude_response
    mock_anthropic_class.return_value = mock_client
    
    # Test
    agent = VisionAgent(api_key="test-key")
    agent.client = mock_client
    result = agent.analyze_image(test_image)
    
    # Assertions
    assert result.description == "Test screenshot"
    assert result.content_type == "ui"
    assert result.confidence == 0.9
```

### Mocking Tesseract

```python
@patch('pytesseract.image_to_string')
def test_ocr_extraction(mock_tesseract, test_image):
    """Test OCR with mocked Tesseract."""
    mock_tesseract.return_value = "Extracted text"
    
    ocr = OCRAgent()
    text = ocr.extract_text(test_image)
    
    assert text == "Extracted text"
    mock_tesseract.assert_called_once()
```

### Mocking File Operations

```python
@patch('shutil.move')
def test_file_organization(mock_move, test_image):
    """Test file organization without actual moves."""
    organizer = OrganizerAgent(
        base_folder=Path("./test"),
        db_path=Path("./test.db"),
        dry_run=False
    )
    
    result = organizer.organize(test_image, classification)
    
    # Verify move was called
    mock_move.assert_called_once()
    assert result.success
```

## Unit Test Examples

### Example 1: OCR Agent

```python
class TestOCRAgent:
    """Test OCRAgent class."""
    
    def test_extract_text_success(self, test_image, tmp_path):
        """Test successful text extraction."""
        ocr = OCRAgent(cache_dir=tmp_path / "cache")
        text = ocr.extract_text(test_image)
        
        assert isinstance(text, str)
        assert len(text) >= 0
    
    def test_extract_text_caching(self, test_image, tmp_path):
        """Test OCR result caching."""
        ocr = OCRAgent(cache_dir=tmp_path / "cache")
        
        # First call
        text1 = ocr.extract_text(test_image)
        
        # Second call (should use cache)
        text2 = ocr.extract_text(test_image)
        
        assert text1 == text2
        
        # Verify cache file exists
        cache_files = list(ocr.cache_dir.glob("*.txt"))
        assert len(cache_files) > 0
    
    def test_file_not_found(self, tmp_path):
        """Test error handling for non-existent file."""
        ocr = OCRAgent(cache_dir=tmp_path / "cache")
        
        with pytest.raises(FileNotFoundError):
            ocr.extract_text(Path("/nonexistent/file.png"))
    
    def test_file_too_large(self, tmp_path):
        """Test error handling for large files."""
        ocr = OCRAgent(cache_dir=tmp_path / "cache")
        
        # Create mock large file
        large_file = tmp_path / "large.png"
        with open(large_file, 'wb') as f:
            f.write(b'0' * (51 * 1024 * 1024))  # 51MB
        
        with pytest.raises(ValueError, match="too large"):
            ocr.extract_text(large_file)
```

### Example 2: Vision Agent

```python
class TestVisionAgent:
    """Test VisionAgent class."""
    
    @patch('anthropic.Anthropic')
    def test_analyze_image_success(
        self,
        mock_anthropic_class,
        mock_claude_response,
        test_image
    ):
        """Test successful image analysis."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key")
        agent.client = mock_client
        
        result = agent.analyze_image(test_image)
        
        assert isinstance(result, VisionAnalysis)
        assert result.confidence > 0.0
    
    @patch('anthropic.Anthropic')
    def test_rate_limit_retry(self, mock_anthropic_class, test_image):
        """Test retry logic for rate limiting."""
        import anthropic
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"description": "test", ...}'
        
        # First call raises rate limit, second succeeds
        mock_client.messages.create.side_effect = [
            anthropic.RateLimitError("Rate limited"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key", max_retries=2)
        agent.client = mock_client
        
        with patch('time.sleep'):  # Skip actual sleep
            result = agent.analyze_image(test_image)
        
        assert isinstance(result, VisionAnalysis)
        assert mock_client.messages.create.call_count == 2
```

### Example 3: Classifier Agent

```python
class TestClassifierAgent:
    """Test ClassifierAgent class."""
    
    @patch('anthropic.Anthropic')
    def test_classify_error_screenshot(
        self,
        mock_anthropic_class,
        mock_claude_response
    ):
        """Test classification of error screenshot."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """{
            "category": "ERROR",
            "keywords": ["database", "timeout"],
            "confidence": 0.92
        }"""
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        result = agent.classify(
            ocr_text="DatabaseTimeout: Connection failed",
            vision_description="Error message on red background"
        )
        
        assert result.category == "ERROR"
        assert "database" in [k.lower() for k in result.keywords]
        assert result.confidence >= 0.9
```

## Integration Tests

### Example: Full Pipeline

```python
class TestFullPipeline:
    """Integration tests for complete pipeline."""
    
    def test_complete_workflow(self, test_image, tmp_path, mock_config):
        """Test complete processing pipeline."""
        # Initialize all agents
        ocr = OCRAgent(cache_dir=tmp_path / "cache")
        
        with patch('anthropic.Anthropic'):
            vision = VisionAgent(api_key="test-key")
            classifier = ClassifierAgent(api_key="test-key")
        
        organizer = OrganizerAgent(
            base_folder=tmp_path / "organized",
            db_path=tmp_path / "test.db",
            dry_run=True
        )
        
        indexer = IndexerAgent(db_path=tmp_path / "test.db")
        
        # Process screenshot
        ocr_text = ocr.extract_text(test_image)
        assert isinstance(ocr_text, str)
        
        # Continue with remaining agents...
```

## End-to-End Tests

### Example: Monitor to Database

```python
def test_end_to_end(tmp_path):
    """Test from file detection to database indexing."""
    # Setup
    source_folder = tmp_path / "screenshots"
    source_folder.mkdir()
    
    output_folder = tmp_path / "organized"
    db_path = tmp_path / "test.db"
    
    # Create test image
    test_image = source_folder / "test.png"
    img = Image.new('RGB', (200, 100), color='white')
    img.save(test_image)
    
    # Run organizer
    from src.main import ScreenshotOrganizer
    
    config = create_test_config(source_folder, output_folder, db_path)
    organizer = ScreenshotOrganizer(config)
    
    # Process
    success = organizer.process_screenshot(test_image)
    
    # Verify
    assert success
    assert not test_image.exists()  # Moved
    
    # Check database
    from src.utils.search_engine import SearchEngine
    search = SearchEngine(db_path)
    results = search.get_recent(limit=1)
    assert len(results) == 1
```

## Test Coverage

### Target Coverage

- **Overall:** 80%+ for `src/`
- **Critical paths:** 90%+ (main.py, agents/)
- **Utils:** 70%+ (platform_utils, config)

### Running Coverage

```bash
# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Coverage Report Example

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
src/agents/ocr_agent.py              45      3    93%
src/agents/vision_agent.py           67      8    88%
src/agents/classifier_agent.py       89     12    87%
src/agents/organizer_agent.py        78      9    88%
src/agents/indexer_agent.py          56      7    88%
src/main.py                         123     18    85%
-----------------------------------------------------
TOTAL                               458     57    88%
```

## Testing Dry-Run Mode

### Example

```python
def test_dry_run_mode(test_image, tmp_path):
    """Test that dry-run doesn't move files."""
    organizer = OrganizerAgent(
        base_folder=tmp_path / "organized",
        db_path=tmp_path / "test.db",
        dry_run=True  # Enable dry-run
    )
    
    result = organizer.organize(test_image, classification)
    
    # File should still exist (not moved)
    assert test_image.exists()
    
    # Result should indicate success
    assert result.success
    
    # Destination should not exist
    assert not result.destination_path.exists()
```

## Performance Tests

### Example: Search Performance

```python
def test_search_performance(tmp_path):
    """Test search performance with 1000 screenshots."""
    import time
    
    # Setup database with 1000 entries
    db_path = tmp_path / "test.db"
    indexer = IndexerAgent(db_path)
    
    for i in range(1000):
        # Index screenshot
        pass
    
    # Test search
    search = SearchEngine(db_path)
    
    start = time.time()
    results = search.full_text_search("database")
    duration = time.time() - start
    
    # Should be fast (<1 second)
    assert duration < 1.0
    assert len(results) > 0
```

## Test Utilities

### Helper Functions

```python
# tests/utils.py

def create_test_image(tmp_path, text="Test", size=(200, 100)):
    """Create a test image with text."""
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill='black')
    
    image_path = tmp_path / f"test_{text}.png"
    img.save(image_path)
    return image_path

def create_test_config(**overrides):
    """Create test configuration."""
    defaults = {
        'source_folders': {'windows': 'C:\\test', 'mac': '~/test'},
        'output_base': './test_output',
        'dry_run': True
    }
    defaults.update(overrides)
    return Config(**defaults)
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Check coverage
      run: |
        coverage report --fail-under=80
```

## Related Documentation

- **Agent Details:** `AGENTS.md`
- **Workflow:** `.kiro/steering/workflow.md`
- **Standards:** `.kiro/steering/steering.md`
- **Conventions:** `.kiro/steering/code-conventions.md`
