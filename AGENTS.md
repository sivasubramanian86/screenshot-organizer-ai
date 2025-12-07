# 🤖 Screenshot Organizer - Agent Architecture

## Overview

This project implements an autonomous multi-agent system for intelligent screenshot organization. Seven specialized agents work sequentially to detect, analyze, classify, organize, and index screenshots automatically.

## Agent Pipeline

```
Screenshot File
      ↓
[1] MonitorAgent → Detect new files
      ↓
[2] OCRAgent → Extract text
      ↓
[3] VisionAgent → Analyze image
      ↓
[4] ClassifierAgent → Categorize + keywords
      ↓
[5] NamingAgent → Generate filename
      ↓
[6] OrganizerAgent → Move to folder
      ↓
[7] IndexerAgent → Add to database
      ↓
Searchable Database
```

## Agents

### 1. MonitorAgent
**File:** `src/agents/monitor_agent.py`

**Purpose:** Detect new screenshot files in monitored folders

**Input:**
- Folder path to monitor
- File extensions to watch (.png, .jpg, etc.)

**Output:**
- Queue of new file paths ready for processing

**Key Responsibilities:**
- Watch screenshot folders using watchdog library
- Detect file creation events
- Wait for file completion (size stable for 1 second)
- Filter out temporary files (.tmp, .DS_Store, etc.)
- Queue valid image files for processing

**Dependencies:** None (first in pipeline)

---

### 2. OCRAgent
**File:** `src/agents/ocr_agent.py`

**Purpose:** Extract text content from screenshots using Tesseract OCR

**Input:**
- Image file path

**Output:**
- Extracted text string (empty if no text found)

**Key Responsibilities:**
- Extract text using Tesseract OCR
- Cache results by file hash (avoid reprocessing)
- Handle images with no text gracefully
- Support multiple languages
- Validate file size (<50MB)

**Dependencies:** MonitorAgent (receives file path)

---

### 3. VisionAgent
**File:** `src/agents/vision_agent.py`

**Purpose:** Analyze screenshot content using Claude Vision API

**Input:**
- Image file path
- OCR text (optional, for context)

**Output:**
- VisionAnalysis object containing:
  - Description (1-2 sentences)
  - Content type (error|code|ui|design|document|other)
  - Objects detected
  - Keywords
  - Has text (boolean)
  - Confidence score (0.0-1.0)

**Key Responsibilities:**
- Encode image to base64
- Call Claude Vision API
- Parse JSON response
- Handle rate limiting (429 errors)
- Retry with exponential backoff
- Validate response structure

**Dependencies:** OCRAgent (receives OCR text for context)

---

### 4. ClassifierAgent
**File:** `src/agents/classifier_agent.py`

**Purpose:** Categorize screenshots and extract relevant keywords

**Input:**
- OCR text
- VisionAnalysis object

**Output:**
- ClassificationResult object containing:
  - Category (ERROR|CODE|UI|DOCUMENTATION|DATA|COMMUNICATION|OTHER)
  - Keywords (5-10 important terms)
  - Suggested folder path
  - Confidence score (0.0-1.0)
  - Tags

**Key Responsibilities:**
- Classify into one of 7 categories
- Extract 5-10 relevant keywords
- Calculate confidence score
- Suggest folder path based on category + keywords
- Handle low confidence cases (<0.6)

**Dependencies:** OCRAgent, VisionAgent (receives both outputs)

---

### 5. NamingAgent
**File:** `src/agents/naming_agent.py`

**Purpose:** Generate intelligent, descriptive filenames

**Input:**
- Category
- Keywords list
- Original file path
- Creation date

**Output:**
- New filename string (format: `DATE_CATEGORY-CODE_KEYWORDS_HASH.ext`)

**Key Responsibilities:**
- Generate filename: `2025-12-07_Error-DB_Database_Timeout_a3f2.png`
- Sanitize special characters
- Truncate to 200 characters (Windows limit)
- Generate 4-character file hash (MD5)
- Handle Windows reserved names (CON, PRN, etc.)
- Resolve duplicate filenames (append (1), (2), etc.)

**Dependencies:** ClassifierAgent (receives category and keywords)

---

### 6. OrganizerAgent
**File:** `src/agents/organizer_agent.py`

**Purpose:** Move files to organized folder structure

**Input:**
- Source file path
- ClassificationResult
- New filename

**Output:**
- OrganizationResult object containing:
  - Original filename
  - New filename
  - Source path
  - Destination path
  - Success status
  - Error message (if failed)

**Key Responsibilities:**
- Create folder structure: `YYYY-MM/Category/Subcategory/`
- Move file to destination
- Preserve file timestamps
- Handle permission errors
- Log all operations to database
- Support dry-run mode (no actual moves)
- Enable rollback (undo moves within 24 hours)

**Dependencies:** ClassifierAgent, NamingAgent (receives classification and new filename)

---

### 7. IndexerAgent
**File:** `src/agents/indexer_agent.py`

**Purpose:** Add screenshots to searchable SQLite database

**Input:**
- File path
- ProcessingResult (metadata + OCR + vision)
- ClassificationResult
- New filename
- New path

**Output:**
- Screenshot ID (database primary key)

**Key Responsibilities:**
- Insert screenshot metadata into database
- Generate 150x150px thumbnail (stored as BLOB)
- Create search index entries (keywords + OCR text)
- Support full-text search
- Enable filtering by category, date, tags
- Track processing history

**Dependencies:** All previous agents (receives complete processing result)

---

## Agent Communication

### Data Flow

```
MonitorAgent
    ↓ file_path: Path
OCRAgent
    ↓ ocr_text: str
VisionAgent
    ↓ vision_analysis: VisionAnalysis
ClassifierAgent
    ↓ classification: ClassificationResult
NamingAgent
    ↓ new_filename: str
OrganizerAgent
    ↓ org_result: OrganizationResult
IndexerAgent
    ↓ screenshot_id: int
Database
```

### Shared Data Models

All agents use Pydantic models from `src/schemas/models.py`:

- **ScreenshotMetadata:** File properties (size, dimensions, timestamps, hash)
- **VisionAnalysis:** Claude Vision API response
- **ClassificationResult:** Category, keywords, confidence, folder
- **ProcessingResult:** Complete processing pipeline result
- **OrganizationResult:** File move operation result

### Error Handling

Each agent implements try-catch with logging:
- Errors logged but don't stop pipeline
- Failed screenshots tracked in statistics
- Low confidence classifications can be skipped
- Retry logic for API calls (3 attempts with exponential backoff)

### Execution Order

Agents execute **sequentially** (not parallel) because:
1. Each agent depends on previous agent's output
2. Simplifies error handling and debugging
3. Easier to track progress and resume from checkpoints
4. Avoids race conditions with file operations
5. Reduces API rate limiting issues

## Agent Detection Format

For Kiro IDE to auto-detect agents, each agent file follows this pattern:

```python
class AgentNameAgent:
    """Agent purpose and description."""
    
    def __init__(self, config):
        """Initialize agent with configuration."""
        pass
    
    def process(self, input_data):
        """Main processing method.
        
        Args:
            input_data: Input from previous agent
            
        Returns:
            Output for next agent
        """
        pass
```

## Performance Metrics

- **MonitorAgent:** <100ms file detection
- **OCRAgent:** ~1-2s per image (cached: instant)
- **VisionAgent:** ~2-3s per image (API call)
- **ClassifierAgent:** ~1-2s per image (API call)
- **NamingAgent:** <10ms filename generation
- **OrganizerAgent:** <100ms file move
- **IndexerAgent:** <200ms database insert

**Total:** ~5-8 seconds per screenshot (first time), ~3-5 seconds (cached OCR)

## Success Criteria

- ✅ 95%+ screenshots automatically organized
- ✅ <1 second search response time
- ✅ 90%+ classification accuracy
- ✅ Zero data loss (all files tracked)
- ✅ Graceful error recovery
- ✅ Resume from crashes (checkpointing)

## Extension Points

To add new agents:
1. Create new file in `src/agents/`
2. Inherit from base pattern
3. Implement `process()` method
4. Add to pipeline in `src/main.py`
5. Update this AGENTS.md file
6. Add tests in `tests/test_new_agent.py`

## Related Documentation

- **Architecture:** `.kiro/steering/workflow.md`
- **Code Standards:** `.kiro/steering/steering.md`
- **Testing:** `.kiro/steering/testing-standards.md`
- **Conventions:** `.kiro/steering/code-conventions.md`
