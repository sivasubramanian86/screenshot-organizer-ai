# 📸 Monitor Agent Usage Guide

## Quick Start

### Basic Usage
```python
from pathlib import Path
from src.agents.monitor_agent import MonitorAgent
from src.utils.platform_utils import get_screenshot_folder, get_os_type

# Auto-detect screenshot folder
screenshot_folder = get_screenshot_folder()

# Create monitor
monitor = MonitorAgent(screenshot_folder)

# Define callback
def process_file(file_path: Path):
    print(f"New screenshot: {file_path}")

# Run monitor
monitor.run(callback=process_file)
```

## Features

### 1. File Completion Detection
The monitor waits until files are fully written before processing:

```python
monitor = MonitorAgent(
    folder_path=Path("./screenshots"),
    completion_wait=1.0  # Wait 1 second for stable file size
)
```

**How it works:**
- Detects new file creation
- Tracks file size every second
- When size is stable for 1 second → file is complete
- Adds to processing queue

### 2. Automatic Filtering

**Valid image formats:**
- `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`

**Ignored files:**
- `*.tmp` - Temporary files
- `*~` - Backup files
- `.DS_Store` - Mac metadata
- `Thumbs.db` - Windows thumbnails
- `*.crdownload` - Chrome downloads
- `*.part` - Partial downloads

### 3. Cross-Platform Paths

```python
from src.utils.platform_utils import get_os_type, get_screenshot_folder

os_type = get_os_type()  # "windows" | "mac" | "linux"

# Windows: C:\Users\USERNAME\Pictures\Screenshots
# Mac: ~/Pictures/Screenshots or ~/Desktop
# Linux: ~/Pictures
folder = get_screenshot_folder(os_type)
```

## Usage Patterns

### Pattern 1: Simple Callback
```python
def process_screenshot(file_path: Path):
    print(f"Processing: {file_path.name}")
    # Your processing logic here

monitor = MonitorAgent(screenshot_folder)
monitor.run(callback=process_screenshot)
```

### Pattern 2: Manual Control
```python
monitor = MonitorAgent(screenshot_folder)
monitor.start()

try:
    while True:
        # Check for completed files
        monitor.event_handler.check_file_completion()
        
        # Process queue
        while not monitor.file_queue.empty():
            file_path = monitor.file_queue.get()
            process_screenshot(file_path)
        
        time.sleep(1)
finally:
    monitor.stop()
```

### Pattern 3: Queue-Based Processing
```python
from queue import Queue

# Shared queue
file_queue = Queue()

# Monitor adds files to queue
monitor = MonitorAgent(screenshot_folder, file_queue=file_queue)
monitor.start()

# Separate thread processes queue
def worker():
    while True:
        file_path = file_queue.get()
        process_screenshot(file_path)
        file_queue.task_done()

import threading
threading.Thread(target=worker, daemon=True).start()
```

## Error Handling

### Folder Not Found
```python
try:
    monitor = MonitorAgent(Path("/nonexistent/folder"))
    monitor.start()
except FileNotFoundError as e:
    print(f"Folder doesn't exist: {e}")
    # Create folder or use different path
```

### Permission Denied

**Mac:**
```
System Preferences → Security & Privacy → Privacy → Files and Folders
→ Grant access to Terminal/IDE
```

**Windows:**
```
Run as administrator or check folder permissions
```

**Code:**
```python
try:
    monitor = MonitorAgent(screenshot_folder)
    monitor.validate_folder()  # Check before starting
    monitor.start()
except PermissionError as e:
    print(f"No permission: {e}")
```

### Graceful Shutdown
```python
import signal

monitor = MonitorAgent(screenshot_folder)

def signal_handler(sig, frame):
    print("Stopping monitor...")
    monitor.stop()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
monitor.start()
```

## Testing

### Test File Detection
```python
# Create test folder
test_folder = Path("./test_screenshots")
test_folder.mkdir(exist_ok=True)

# Start monitor
monitor = MonitorAgent(test_folder, completion_wait=0.5)
monitor.start()

# Create test file
test_file = test_folder / "test.png"
test_file.write_bytes(b"fake image data")

# Wait for detection
time.sleep(1)
monitor.event_handler.check_file_completion()

# Check queue
print(f"Files in queue: {monitor.get_queue_size()}")

monitor.stop()
```

### Run Unit Tests
```bash
pytest tests/test_monitor_agent.py -v
pytest tests/test_platform_utils.py -v
```

## Monitoring Status

```python
# Get pending files (still being written)
pending = monitor.get_pending_count()

# Get queued files (ready for processing)
queued = monitor.get_queue_size()

print(f"Pending: {pending}, Queued: {queued}")
```

## Performance Tips

1. **Adjust completion wait time:**
   - Small files: `completion_wait=0.5`
   - Large files: `completion_wait=2.0`

2. **Use separate processing thread:**
   - Monitor in main thread
   - Process files in worker thread
   - Prevents blocking

3. **Batch processing:**
   - Collect multiple files
   - Process in batches
   - More efficient for API calls

## Common Issues

### Issue: Files not detected
**Solution:** Check file extensions and temporary file patterns

### Issue: Files processed before fully written
**Solution:** Increase `completion_wait` parameter

### Issue: Permission denied on Mac
**Solution:** Grant folder access in System Preferences

### Issue: High CPU usage
**Solution:** Increase sleep interval in processing loop

## Integration Example

```python
from src.agents.monitor_agent import MonitorAgent
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent

# Setup agents
monitor = MonitorAgent(screenshot_folder)
ocr = OCRAgent()
vision = VisionAgent()

def process_pipeline(file_path: Path):
    # Extract text
    text = ocr.extract_text(file_path)
    
    # Analyze image
    analysis = vision.analyze_image(file_path)
    
    # Process results
    print(f"OCR: {text[:100]}...")
    print(f"Vision: {analysis.description}")

# Run monitor
monitor.run(callback=process_pipeline)
```

## Next Steps

1. Implement OCR Agent for text extraction
2. Implement Vision Agent for image analysis
3. Implement Classifier Agent for categorization
4. Implement Organizer Agent for file management
5. Implement Indexer Agent for database storage
