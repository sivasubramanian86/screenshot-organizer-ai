# 📁 Naming & Organizer Agents Usage Guide

## Overview

Two agents for intelligent file naming and organization:
1. **Naming Agent** - Generate smart filenames
2. **Organizer Agent** - Move files to organized folders

## Naming Convention

### Format
```
[DATE]_[CATEGORY-CODE]_[KEYWORDS]_[HASH].png
```

### Examples
```
2025-12-07_Error-504_DatabaseTimeout_ConnectionFailed_a3f2.png
2025-12-07_Code-Python_AsyncAwait_Decorator_b1e9.png
2025-12-07_UI-Dashboard_Analytics_Export_c2d3.png
```

### Components

**1. DATE** - `YYYY-MM-DD`
- From file creation time
- Example: `2025-12-07`

**2. CATEGORY-CODE** - Short category identifier
- `Error-[Code]`: Error-404, Error-500, Error-DB
- `Code-[Lang]`: Code-Python, Code-JS, Code-Config
- `UI-[Component]`: UI-Dashboard, UI-Login, UI-Form
- `Docs-[Type]`: Docs-API, Docs-Architecture
- `Data-[Type]`: Data-Chart, Data-Report
- `Comm-[Type]`: Comm-Slack, Comm-Email

**3. KEYWORDS** - 2-4 main keywords
- Extracted from classification
- Capitalized, separated by underscores
- Example: `Database_Timeout_Connection`

**4. HASH** - 4-character file hash
- MD5 hash (first 4 chars)
- For duplicate detection
- Example: `a3f2`

## Naming Agent

### Basic Usage

```python
from pathlib import Path
from datetime import datetime
from src.agents.naming_agent import NamingAgent

namer = NamingAgent()

filename = namer.generate_filename(
    category="ERROR",
    keywords=["database", "timeout", "connection"],
    file_path=Path("screenshot.png"),
    created_date=datetime(2025, 12, 7)
)

print(filename)
# Output: 2025-12-07_Error-DB_Database_Timeout_Connection_a3f2.png
```

### Filename Sanitization

**Removed characters:**
- `/ \ : * ? " < > |`
- Spaces → underscores
- Multiple underscores → single underscore

**Windows reserved names:**
- CON, PRN, AUX, NUL, COM1-9, LPT1-9
- Automatically prefixed with `File_`

**Example:**
```python
# Input: "test<file>:name*.png"
# Output: "testfilename.png"
```

### Length Limits

**Max length:** 200 characters (Windows limit)

**Truncation:**
- Preserves extension
- Truncates at underscore boundary
- Keeps at least 70% of name

```python
namer = NamingAgent(max_length=50)
filename = namer.generate_filename(...)
# Automatically truncated if too long
```

### Duplicate Handling

```python
# If file exists, append (1), (2), etc
new_filename = namer.handle_duplicate(
    filename="test.png",
    target_dir=Path("./organized")
)

# test.png exists → returns "test(1).png"
# test(1).png exists → returns "test(2).png"
```

## Organizer Agent

### Basic Usage

```python
from pathlib import Path
from src.agents.organizer_agent import OrganizerAgent
from src.schemas.models import ClassificationResult

# Initialize
organizer = OrganizerAgent(
    base_folder=Path("./organized_screenshots"),
    db_path=Path("data/screenshots.db"),
    dry_run=False  # Set True to test without moving files
)

# Create classification
classification = ClassificationResult(
    category="ERROR",
    keywords=["database", "timeout"],
    suggested_folder="2025-12/ERROR/Database",
    confidence=0.9,
    tags=["database"]
)

# Organize file
result = organizer.organize(
    source_path=Path("screenshot.png"),
    classification=classification
)

if result.success:
    print(f"Moved to: {result.destination_path}")
else:
    print(f"Failed: {result.error_message}")
```

### Folder Structure

```
organized_screenshots/
├── 2025-12/
│   ├── Error/
│   │   ├── Database/
│   │   ├── Network/
│   │   ├── Runtime/
│   │   └── HTTP/
│   ├── Code/
│   │   ├── Python/
│   │   ├── JavaScript/
│   │   ├── TypeScript/
│   │   └── Config/
│   ├── Ui/
│   │   ├── Dashboard/
│   │   ├── Auth/
│   │   ├── Settings/
│   │   └── Forms/
│   ├── Data/
│   │   ├── Charts/
│   │   ├── Reports/
│   │   └── Tables/
│   ├── Documentation/
│   ├── Communication/
│   └── Other/
```

### Folder Suggestion

```python
# Get target folder without moving
folder = organizer.get_target_folder(
    category="ERROR",
    keywords=["database", "timeout"],
    date=datetime(2025, 12, 7)
)

print(folder)
# Output: organized_screenshots/2025-12/Error/Database
```

### Dry Run Mode

```python
# Test without actually moving files
organizer = OrganizerAgent(
    base_folder=Path("./organized"),
    db_path=Path("data/screenshots.db"),
    dry_run=True
)

result = organizer.organize(source, classification)
# Shows what would happen, but doesn't move files
```

### Timestamp Preservation

Files maintain their original timestamps after moving:
- Creation time preserved
- Modification time preserved
- Access time preserved

## Rollback Mechanism

### Rollback Recent Moves

```python
# Rollback moves from last 24 hours
count = organizer.rollback(hours=24)
print(f"Rolled back {count} files")
```

### How It Works

1. All moves logged to `processing_log` table
2. Stores: source path, destination path, timestamp
3. Rollback restores files to original location
4. Updates log status to `rolled_back`

### Rollback Example

```python
# Organize file
result = organizer.organize(source, classification)
# File moved: source.png → organized/2025-12/Error/Database/new_name.png

# Oops, made a mistake!
organizer.rollback(hours=1)
# File restored: new_name.png → source.png
```

## Complete Pipeline

```python
from pathlib import Path
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from src.agents.classifier_agent import ClassifierAgent
from src.agents.organizer_agent import OrganizerAgent

# Initialize agents
ocr = OCRAgent()
vision = VisionAgent()
classifier = ClassifierAgent()
organizer = OrganizerAgent(
    base_folder=Path("./organized_screenshots"),
    db_path=Path("data/screenshots.db")
)

# Process screenshot
image_path = Path("screenshot.png")

# Step 1: Extract text
ocr_text = ocr.extract_text(image_path)

# Step 2: Analyze image
vision_analysis = vision.analyze_image(image_path, ocr_text=ocr_text)

# Step 3: Classify
classification = classifier.classify(ocr_text, vision_analysis=vision_analysis)

# Step 4: Organize
result = organizer.organize(image_path, classification)

print(f"Category: {classification.category}")
print(f"New name: {result.new_filename}")
print(f"Location: {result.destination_path}")
```

## Error Handling

### File Not Found
```python
result = organizer.organize(Path("nonexistent.png"), classification)
assert not result.success
assert "not found" in result.error_message
```

### Permission Denied
```python
try:
    result = organizer.organize(source, classification)
except PermissionError as e:
    print(f"Permission denied: {e}")
```

### Filename Too Long
```python
# Automatically truncated to 200 characters
namer = NamingAgent(max_length=200)
filename = namer.generate_filename(...)
assert len(filename) <= 200
```

## Advanced Features

### Custom Max Length
```python
# For systems with different limits
namer = NamingAgent(max_length=150)
```

### Batch Organization
```python
images = Path("screenshots").glob("*.png")

for image in images:
    # Process each
    classification = classify_image(image)
    result = organizer.organize(image, classification)
    
    if result.success:
        print(f"✅ {image.name} → {result.new_filename}")
    else:
        print(f"❌ {image.name}: {result.error_message}")
```

### Conflict Resolution
```python
# Automatic duplicate handling
# If file exists: appends (1), (2), etc
# Tracked in database for rollback
```

## Database Logging

All operations logged to `processing_log` table:

```sql
CREATE TABLE processing_log (
    id INTEGER PRIMARY KEY,
    operation TEXT,           -- "move", "rename"
    timestamp TIMESTAMP,
    old_path TEXT,
    new_path TEXT,
    old_filename TEXT,
    new_filename TEXT,
    status TEXT,              -- "success", "failed", "rolled_back"
    error_message TEXT
);
```

## Testing

```bash
# Run tests
pytest tests/test_naming_agent.py -v
pytest tests/test_organizer_agent.py -v

# Run examples
python examples/organizer_example.py
```

## Performance Tips

### 1. Use Dry Run First
```python
# Test organization without moving files
organizer = OrganizerAgent(..., dry_run=True)
```

### 2. Batch Processing
```python
# Process multiple files efficiently
for image in images:
    result = organizer.organize(image, classification)
```

### 3. Monitor Disk Space
```python
# Check available space before organizing
import shutil
stats = shutil.disk_usage(organizer.base_folder)
print(f"Free space: {stats.free / (1024**3):.1f} GB")
```

## Troubleshooting

### Issue: Filename too long
**Solution:** Automatically truncated to 200 characters

### Issue: Duplicate filenames
**Solution:** Automatically appends (1), (2), etc

### Issue: Permission denied
**Solution:** Check folder permissions, run as administrator

### Issue: File not moved
**Solution:** Check logs in `processing_log` table for error details

## Next Steps

1. Implement Indexer Agent (database storage)
2. Add search functionality
3. Build web UI for browsing organized screenshots
4. Add thumbnail generation
