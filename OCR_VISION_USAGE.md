# 🤖 OCR & Vision Agents Usage Guide

## Overview

Two AI agents for screenshot analysis:
1. **OCR Agent** - Extract text using Tesseract
2. **Vision Agent** - Semantic understanding using Claude Vision API

## OCR Agent

### Setup

**Install Tesseract:**
```bash
# Windows
# Download: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR

# Mac
brew install tesseract

# Verify
tesseract --version
```

### Basic Usage

```python
from pathlib import Path
from src.agents.ocr_agent import OCRAgent

# Initialize
ocr = OCRAgent()

# Extract text
text = ocr.extract_text(Path("screenshot.png"))
print(text)
```

### Features

**1. Automatic Caching**
```python
ocr = OCRAgent()

# First call - processes image
text1 = ocr.extract_text(image_path)  # Takes time

# Second call - uses cache
text2 = ocr.extract_text(image_path)  # Instant!

# Clear cache if needed
ocr.clear_cache()
```

**2. Error Handling**
```python
try:
    text = ocr.extract_text(image_path)
except RuntimeError as e:
    print(f"Tesseract not installed: {e}")
except FileNotFoundError:
    print("Image not found")
except ValueError as e:
    print(f"Image too large: {e}")
```

**3. Empty Images**
```python
# Images without text return empty string
text = ocr.extract_text(blank_image)
assert text == ""
```

### Cache Location

Cache stored in: `data/ocr_cache/`
- Format: `{image_hash}.txt`
- Automatic deduplication by file hash

## Vision Agent

### Setup

**Get Claude API Key:**
1. Visit: https://console.anthropic.com/
2. Create API key
3. Set environment variable:

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Mac/Linux
export ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Or in config/.env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### Basic Usage

```python
from pathlib import Path
from src.agents.vision_agent import VisionAgent

# Initialize
vision = VisionAgent()

# Analyze image
analysis = vision.analyze_image(Path("screenshot.png"))

print(f"Description: {analysis.description}")
print(f"Type: {analysis.content_type}")
print(f"Keywords: {analysis.keywords}")
print(f"Confidence: {analysis.confidence}")
```

### Response Format

```python
VisionAnalysis(
    description="A code editor showing Python function",
    content_type="code",  # error|code|ui|design|document|screenshot|other
    objects_detected=["editor", "code", "syntax_highlighting"],
    keywords=["python", "function", "async", "await"],
    has_text=True,
    confidence=0.92
)
```

### Advanced Usage

**1. Include OCR Text**
```python
ocr = OCRAgent()
vision = VisionAgent()

# Extract text first
ocr_text = ocr.extract_text(image_path)

# Pass to vision for better analysis
analysis = vision.analyze_image(image_path, ocr_text=ocr_text)
```

**2. Custom Configuration**
```python
vision = VisionAgent(
    api_key="your-key",
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    timeout=60,
    max_retries=3
)
```

**3. Retry Logic**
```python
# Automatic retry with exponential backoff
# - Rate limit (429): Waits 1s, 2s, 4s
# - Timeout: Waits 1s, 2s, 4s
# - Connection error: Waits 1s, 2s, 4s

analysis = vision.analyze_image(image_path)
# Handles retries automatically
```

### Error Handling

```python
try:
    analysis = vision.analyze_image(image_path)
except ValueError as e:
    if "API key" in str(e):
        print("Set ANTHROPIC_API_KEY")
    elif "too large" in str(e):
        print("Image over 50MB")
except FileNotFoundError:
    print("Image not found")
except Exception as e:
    print(f"Analysis failed: {e}")
```

## Combined Usage

### Pattern 1: Sequential Processing

```python
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent

ocr = OCRAgent()
vision = VisionAgent()

# Step 1: OCR
ocr_text = ocr.extract_text(image_path)

# Step 2: Vision (with OCR context)
analysis = vision.analyze_image(image_path, ocr_text=ocr_text)

# Step 3: Use results
print(f"Found {len(ocr_text)} characters")
print(f"Type: {analysis.content_type}")
print(f"Keywords: {', '.join(analysis.keywords)}")
```

### Pattern 2: Batch Processing

```python
from pathlib import Path

ocr = OCRAgent()
vision = VisionAgent()

images = Path("screenshots").glob("*.png")

for image_path in images:
    # Process each image
    text = ocr.extract_text(image_path)
    analysis = vision.analyze_image(image_path, ocr_text=text)
    
    # Store results
    print(f"{image_path.name}: {analysis.content_type}")
```

### Pattern 3: Pipeline Integration

```python
def process_screenshot(image_path: Path):
    """Complete processing pipeline."""
    ocr = OCRAgent()
    vision = VisionAgent()
    
    # Extract text
    text = ocr.extract_text(image_path)
    
    # Analyze image
    analysis = vision.analyze_image(image_path, ocr_text=text)
    
    return {
        'ocr_text': text,
        'description': analysis.description,
        'type': analysis.content_type,
        'keywords': analysis.keywords,
        'confidence': analysis.confidence
    }

# Use with monitor
from src.agents.monitor_agent import MonitorAgent

monitor = MonitorAgent(screenshot_folder)
monitor.run(callback=process_screenshot)
```

## Performance Tips

### 1. OCR Caching
- First run: ~1-2 seconds per image
- Cached: Instant
- Cache persists across runs

### 2. Vision API Rate Limits
- Add delay between requests:
```python
import time

for image in images:
    analysis = vision.analyze_image(image)
    time.sleep(1)  # Respect rate limits
```

### 3. Batch Optimization
```python
# Process in batches
batch_size = 10
for i in range(0, len(images), batch_size):
    batch = images[i:i+batch_size]
    for image in batch:
        process_screenshot(image)
    time.sleep(2)  # Pause between batches
```

## Testing

### Test OCR
```bash
pytest tests/test_ocr_agent.py -v
```

### Test Vision (Mocked)
```bash
pytest tests/test_vision_agent.py -v
```

### Manual Testing
```python
# Create test image
from PIL import Image, ImageDraw

img = Image.new('RGB', (400, 100), color='white')
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Test Screenshot", fill='black')
img.save("test.png")

# Test OCR
ocr = OCRAgent()
text = ocr.extract_text(Path("test.png"))
print(f"OCR: {text}")

# Test Vision (requires API key)
vision = VisionAgent()
analysis = vision.analyze_image(Path("test.png"))
print(f"Vision: {analysis.content_type}")
```

## Troubleshooting

### OCR Issues

**Tesseract not found:**
```
RuntimeError: Tesseract OCR is not installed
```
Solution: Install Tesseract and add to PATH

**Poor OCR quality:**
- Ensure image has good contrast
- Check image resolution (higher is better)
- Verify text is not too small

**Empty results:**
- Normal for images without text
- Check if text is visible in image

### Vision Issues

**API key error:**
```
ValueError: Claude API key not found
```
Solution: Set ANTHROPIC_API_KEY environment variable

**Rate limiting:**
```
anthropic.RateLimitError: Rate limited
```
Solution: Automatic retry with backoff (built-in)

**Timeout:**
```
anthropic.APITimeoutError: Timeout
```
Solution: Automatic retry (built-in) or increase timeout

## Cost Estimation

### Claude Vision API
- Model: claude-3-5-sonnet-20241022
- ~$3 per 1000 images (approximate)
- Max tokens: 1000 per request

### OCR (Tesseract)
- Free and open source
- No API costs
- Local processing

## Next Steps

1. Implement Classifier Agent (categorization)
2. Implement Organizer Agent (file management)
3. Implement Indexer Agent (database storage)
4. Build complete pipeline

## Examples

Run example code:
```bash
python examples/ocr_vision_example.py
```

See working examples for:
- Basic OCR extraction
- Vision analysis
- Combined processing
- Error handling
- Batch processing
