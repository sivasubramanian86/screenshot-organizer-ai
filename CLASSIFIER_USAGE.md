# 🎯 Classifier Agent Usage Guide

## Overview

The Classifier Agent categorizes screenshots into 7 categories and extracts relevant keywords using Claude AI.

## Categories

1. **ERROR** - Error messages, stack traces, exceptions
2. **CODE** - Source code, IDE, terminal, configs
3. **UI** - Web/app interfaces, designs, mockups
4. **DOCUMENTATION** - Docs, diagrams, flowcharts
5. **DATA** - Tables, charts, reports, analytics
6. **COMMUNICATION** - Slack, email, messages
7. **OTHER** - Everything else

## Basic Usage

```python
from src.agents.classifier_agent import ClassifierAgent

# Initialize
classifier = ClassifierAgent()

# Classify
result = classifier.classify(
    ocr_text="DatabaseConnectionTimeout: Failed to connect",
    vision_description="Terminal showing red error message"
)

print(f"Category: {result.category}")
print(f"Keywords: {result.keywords}")
print(f"Confidence: {result.confidence}")
print(f"Folder: {result.suggested_folder}")
```

## Classification Response

```python
ClassificationResult(
    category="ERROR",
    keywords=["database", "connection", "timeout", "retry", "failed"],
    suggested_folder="2025-12/ERROR/Database",
    confidence=0.92,
    tags=["database", "connection", "timeout", "retry", "failed"]
)
```

## Confidence Levels

### High Confidence (0.9 - 1.0)
- Clear, obvious category
- Distinctive keywords
- No ambiguity

**Example:**
```python
ocr_text = "TypeError: Cannot read property 'id' of null"
# → Category: ERROR, Confidence: 0.95
```

### Medium Confidence (0.6 - 0.9)
- Some clues but not 100% certain
- Could have multiple interpretations

**Example:**
```python
ocr_text = "function getData() { return data; }"
# → Category: CODE, Confidence: 0.75
```

### Low Confidence (< 0.6)
- Ambiguous content
- Could be multiple categories
- **Needs manual review**

**Example:**
```python
ocr_text = "Click here to continue"
# → Category: OTHER, Confidence: 0.45
```

## Folder Suggestions

### Format
```
{YEAR-MONTH}/{CATEGORY}/{SUBCATEGORY}
```

### Examples

**ERROR Screenshots:**
```
2025-12/ERROR/Database    # database, connection keywords
2025-12/ERROR/Network     # timeout, network keywords
2025-12/ERROR/Runtime     # null, undefined keywords
2025-12/ERROR/HTTP        # 404, 500 keywords
```

**CODE Screenshots:**
```
2025-12/CODE/Python       # python keyword
2025-12/CODE/JavaScript   # javascript keyword
2025-12/CODE/Config       # yaml, json keywords
```

**UI Screenshots:**
```
2025-12/UI/Dashboard      # dashboard keyword
2025-12/UI/Auth           # login, signup keywords
2025-12/UI/Settings       # settings keyword
```

**DATA Screenshots:**
```
2025-12/DATA/Charts       # chart, graph keywords
2025-12/DATA/Tables       # table keyword
2025-12/DATA/Reports      # report keyword
```

## Full Pipeline Integration

```python
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from src.agents.classifier_agent import ClassifierAgent

# Initialize agents
ocr = OCRAgent()
vision = VisionAgent()
classifier = ClassifierAgent()

# Process screenshot
image_path = "screenshot.png"

# Step 1: Extract text
ocr_text = ocr.extract_text(image_path)

# Step 2: Analyze image
vision_analysis = vision.analyze_image(image_path, ocr_text=ocr_text)

# Step 3: Classify
classification = classifier.classify(ocr_text, vision_analysis=vision_analysis)

# Use results
print(f"Category: {classification.category}")
print(f"Folder: {classification.suggested_folder}")
print(f"Confidence: {classification.confidence:.1%}")
```

## Claude Prompt Used

The classifier uses this prompt structure:

```
Analyze this screenshot and classify it into ONE category.

**Categories:**
- ERROR: Error messages, stack traces, exceptions, bug reports
- CODE: Source code, IDE, terminal, git diffs, configs
- UI: Web/app interfaces, designs, mockups, forms
- DOCUMENTATION: Docs, diagrams, flowcharts, architecture
- DATA: Tables, charts, reports, spreadsheets, analytics
- COMMUNICATION: Slack, email, messages, comments
- OTHER: Anything that doesn't fit above

**Input Data:**
OCR Text: {ocr_text}
Vision Description: {vision_description}

**Required Output (JSON):**
{
  "category": "ERROR|CODE|UI|DOCUMENTATION|DATA|COMMUNICATION|OTHER",
  "keywords": ["5-10", "important", "keywords"],
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}
```

## Keyword Extraction

### Priority Order
1. **Error codes** - 404, 500, ETIMEDOUT
2. **Programming languages** - python, javascript, rust
3. **Technical terms** - async, await, decorator
4. **Component names** - dashboard, login, chart
5. **Action verbs** - fetch, connect, render

### Examples

**ERROR Screenshot:**
```python
keywords = ["database", "connection_timeout", "504", "retry_logic", "failed"]
```

**CODE Screenshot:**
```python
keywords = ["python", "async", "await", "decorator", "function"]
```

**UI Screenshot:**
```python
keywords = ["dashboard", "analytics", "chart", "export_button", "settings"]
```

## Edge Cases

### Mixed Content
```python
# Code + Documentation
ocr_text = """
# API Documentation
```python
def fetch_data():
    return requests.get('/api/data')
```
"""

result = classifier.classify(ocr_text)
# → Likely: DOCUMENTATION (docs take precedence)
# → Confidence: 0.7-0.8 (medium)
```

### Ambiguous Content
```python
ocr_text = "Loading..."
vision_desc = "Spinner on white background"

result = classifier.classify(ocr_text, vision_description=vision_desc)
# → Category: OTHER
# → Confidence: < 0.6 (needs review)
```

### Empty Content
```python
result = classifier.classify("", vision_description="Blank screen")
# → Category: OTHER
# → Confidence: 0.3 (fallback)
```

## Handling Low Confidence

```python
result = classifier.classify(ocr_text, vision_description=vision_desc)

if result.confidence < 0.6:
    print("⚠️  Low confidence - needs manual review")
    print(f"Suggested: {result.category}")
    print("Please verify classification")
    
    # Prompt user for correction
    user_category = input("Correct category: ")
    
    # Store correction (see User Corrections section)
```

## User Corrections

### Recording Corrections

```python
from src.utils.user_corrections import UserCorrectionManager

corrections = UserCorrectionManager(Path("data/screenshots.db"))

# User corrects classification
corrections.add_correction(
    screenshot_id=123,
    original_category="OTHER",
    corrected_category="ERROR",
    original_keywords=["generic", "text"],
    corrected_keywords=["database", "error", "timeout"],
    ocr_text=ocr_text,
    vision_description=vision_desc
)
```

### Learning from Corrections

```python
# Get correction patterns
patterns = corrections.get_correction_patterns()

for pattern, count in patterns.items():
    print(f"{pattern}: {count} corrections")

# Output:
# OTHER->ERROR: 15 corrections
# CODE->DOCUMENTATION: 8 corrections
```

## Error Handling

```python
try:
    result = classifier.classify(ocr_text, vision_description=vision_desc)
except ValueError as e:
    if "API key" in str(e):
        print("Set ANTHROPIC_API_KEY environment variable")
except Exception as e:
    print(f"Classification failed: {e}")
    # Use fallback classification
    result = classifier._fallback_classification(ocr_text, vision_desc)
```

## Fallback Classification

When Claude API fails, rule-based classification is used:

```python
# Automatic fallback on API failure
result = classifier.classify(ocr_text, vision_description=vision_desc)
# If API fails → Uses keyword matching
# Confidence will be < 0.6
```

## Performance Tips

### 1. Batch Processing
```python
results = []
for image in images:
    result = classifier.classify(ocr_text, vision_desc)
    results.append(result)
    time.sleep(0.5)  # Rate limiting
```

### 2. Cache Classifications
```python
# Store in database to avoid re-classification
if not already_classified(image_hash):
    result = classifier.classify(ocr_text, vision_desc)
    store_classification(image_hash, result)
```

### 3. Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

def classify_image(image_data):
    return classifier.classify(image_data['ocr'], image_data['vision'])

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(classify_image, image_data_list)
```

## Testing

```bash
# Run tests
pytest tests/test_classifier_agent.py -v

# Run examples
python examples/classifier_example.py
```

## Next Steps

1. Implement Organizer Agent (file naming & moving)
2. Implement Indexer Agent (database storage)
3. Build complete pipeline
4. Add web UI for manual corrections

## Cost Estimation

- Model: claude-3-5-sonnet-20241022
- ~500 tokens per classification
- ~$0.003 per 1000 tokens
- **~$0.0015 per screenshot** (approximate)
