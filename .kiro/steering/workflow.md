# 🔄 Screenshot Organizer - Workflow & Architecture

## Project Overview

### Problem Statement

Users take hundreds of screenshots daily but struggle to:
- Find specific screenshots later
- Organize screenshots manually (time-consuming)
- Remember what each screenshot contains
- Search across screenshot content

### Solution

An autonomous AI system that automatically:
1. Monitors screenshot folders
2. Extracts text with OCR
3. Analyzes content with AI vision
4. Classifies and categorizes
5. Renames intelligently
6. Organizes into folders
7. Indexes for instant search

### Key Benefits

- **Zero manual work:** Fully automatic organization
- **Instant search:** Find any screenshot in <1 second
- **Smart categorization:** 7 categories with 90%+ accuracy
- **Cross-platform:** Works on Windows and Mac
- **Searchable:** Full-text search across OCR text and metadata

## Agent Pipeline Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Screenshot Created                        │
│                  (User takes screenshot)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  [1] MonitorAgent                                            │
│  • Detect new file                                           │
│  • Wait for completion (size stable)                         │
│  • Filter temporary files                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ file_path
┌─────────────────────────────────────────────────────────────┐
│  [2] OCRAgent                                                │
│  • Extract text with Tesseract                               │
│  • Cache by file hash                                        │
│  • Handle no-text images                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓ ocr_text
┌─────────────────────────────────────────────────────────────┐
│  [3] VisionAgent                                             │
│  • Analyze with Claude Vision API                            │
│  • Detect objects and content type                           │
│  • Extract keywords                                          │
│  • Calculate confidence                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ vision_analysis
┌─────────────────────────────────────────────────────────────┐
│  [4] ClassifierAgent                                         │
│  • Categorize (ERROR|CODE|UI|DOCS|DATA|COMM|OTHER)          │
│  • Extract 5-10 keywords                                     │
│  • Calculate confidence score                                │
│  • Suggest folder path                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓ classification
┌─────────────────────────────────────────────────────────────┐
│  [5] NamingAgent                                             │
│  • Generate filename: DATE_CATEGORY_KEYWORDS_HASH.ext        │
│  • Sanitize special characters                               │
│  • Truncate to 200 chars                                     │
│  • Handle duplicates                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ new_filename
┌─────────────────────────────────────────────────────────────┐
│  [6] OrganizerAgent                                          │
│  • Create folder: YYYY-MM/Category/Subcategory/              │
│  • Move file to destination                                  │
│  • Preserve timestamps                                       │
│  • Log operation for rollback                                │
└─────────────────────────────────────────────────────────────┘
                            ↓ org_result
┌─────────────────────────────────────────────────────────────┐
│  [7] IndexerAgent                                            │
│  • Insert into SQLite database                               │
│  • Generate 150x150px thumbnail                              │
│  • Create search index entries                               │
│  • Enable full-text search                                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Searchable Database                         │
│              (SQLite with FTS5 search)                       │
└─────────────────────────────────────────────────────────────┘
```

## Agent Responsibilities (Detailed)

### 1. MonitorAgent

**Primary Responsibility:** File system monitoring and detection

**Detailed Tasks:**
- Use watchdog library to monitor screenshot folders
- Detect `FileCreatedEvent` for new files
- Track file size every 1 second until stable (file fully written)
- Filter out temporary files: `*.tmp`, `*~`, `.DS_Store`, `Thumbs.db`
- Validate file extensions: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.gif`
- Add valid files to processing queue
- Handle permission errors gracefully

**Error Handling:**
- FileNotFoundError: Log and skip if folder doesn't exist
- PermissionError: Log with instructions for granting access
- Continue monitoring even if individual files fail

**Performance:**
- Poll interval: 1 second
- File completion wait: 1 second
- Memory: O(n) where n = pending files

---

### 2. OCRAgent

**Primary Responsibility:** Text extraction from images

**Detailed Tasks:**
- Open image with PIL
- Extract text using pytesseract
- Calculate SHA256 hash of image
- Check cache for existing result
- Store result in cache (file hash → text)
- Return empty string if no text found
- Validate file size (<50MB)

**Error Handling:**
- RuntimeError: Tesseract not installed → helpful error message
- FileNotFoundError: Image not found → skip
- ValueError: Image too large → skip
- Exception: OCR failed → return empty string, continue

**Performance:**
- First run: ~1-2 seconds per image
- Cached: <10ms
- Cache location: `data/ocr_cache/`

---

### 3. VisionAgent

**Primary Responsibility:** AI-powered image analysis

**Detailed Tasks:**
- Encode image to base64
- Detect media type (PNG, JPEG, etc.)
- Build prompt with OCR text context
- Call Claude Vision API (claude-3-5-sonnet-20241022)
- Parse JSON response
- Extract: description, content_type, objects, keywords, confidence
- Handle rate limiting (429 errors)
- Retry with exponential backoff (1s, 2s, 4s)

**Error Handling:**
- AuthenticationError: Invalid API key → clear error message
- RateLimitError: Wait and retry (3 attempts)
- APITimeoutError: Retry with backoff
- APIConnectionError: Retry with backoff
- ValueError: Invalid response → use fallback classification

**Performance:**
- API call: ~2-3 seconds
- Max tokens: 1000
- Timeout: 60 seconds
- Retries: 3 with exponential backoff

---

### 4. ClassifierAgent

**Primary Responsibility:** Categorization and keyword extraction

**Detailed Tasks:**
- Combine OCR text + vision description
- Call Claude API with classification prompt
- Parse JSON response
- Validate category (must be one of 7 valid categories)
- Extract 5-10 keywords
- Calculate confidence score (0.0-1.0)
- Determine subcategory from keywords
- Suggest folder path: `YYYY-MM/Category/Subcategory/`
- Handle low confidence (<0.6) → flag for review

**Categories:**
- ERROR: Error messages, stack traces, exceptions
- CODE: Source code, IDE, terminal, configs
- UI: Web/app interfaces, designs, mockups
- DOCUMENTATION: Docs, diagrams, flowcharts
- DATA: Tables, charts, reports, analytics
- COMMUNICATION: Slack, email, messages
- OTHER: Everything else

**Error Handling:**
- API failure → use fallback rule-based classification
- Invalid category → default to OTHER
- Low confidence → skip auto-organization
- Exception → log and mark as failed

**Performance:**
- API call: ~1-2 seconds
- Max tokens: 500
- Fallback: <10ms

---

### 5. NamingAgent

**Primary Responsibility:** Intelligent filename generation

**Detailed Tasks:**
- Extract date from file creation time (YYYY-MM-DD)
- Generate category code: Error-DB, Code-Python, UI-Dashboard
- Select 2-4 top keywords
- Calculate 4-character MD5 hash
- Combine: `DATE_CATEGORY-CODE_KEYWORDS_HASH.ext`
- Sanitize: Remove `/ \ : * ? " < > |`
- Replace spaces with underscores
- Remove multiple underscores
- Check Windows reserved names (CON, PRN, AUX, etc.)
- Truncate to 200 characters (preserve extension)
- Handle duplicates: append (1), (2), etc.

**Error Handling:**
- Invalid characters → sanitize
- Too long → truncate at underscore boundary
- Reserved name → prefix with `File_`
- Duplicate → append counter

**Performance:**
- <10ms per filename
- Deterministic (same input → same output)

---

### 6. OrganizerAgent

**Primary Responsibility:** File organization and movement

**Detailed Tasks:**
- Determine target folder: `base/YYYY-MM/Category/Subcategory/`
- Create folder structure if doesn't exist
- Check for duplicate filename
- Move file from source to destination
- Preserve file timestamps (creation, modification)
- Log operation to database (for rollback)
- Support dry-run mode (show what would happen)
- Handle permission errors

**Folder Structure:**
```
organized_screenshots/
├── 2025-12/
│   ├── Error/
│   │   ├── Database/
│   │   ├── Network/
│   │   └── Runtime/
│   ├── Code/
│   │   ├── Python/
│   │   ├── JavaScript/
│   │   └── Config/
│   └── Ui/
│       └── Dashboard/
```

**Error Handling:**
- PermissionError → log and skip
- FileExistsError → append (1), (2), etc.
- OSError → log and skip
- Continue processing other files

**Performance:**
- File move: <100ms
- Folder creation: <50ms

---

### 7. IndexerAgent

**Primary Responsibility:** Database indexing and search

**Detailed Tasks:**
- Open image with PIL
- Generate 150x150px thumbnail
- Convert thumbnail to PNG bytes
- Insert into `screenshots` table
- Insert keywords into `search_terms` table (weight: 1.0)
- Insert OCR words into `search_terms` table (weight: 0.5)
- Commit transaction
- Return screenshot ID

**Database Schema:**
- screenshots: Main metadata table
- search_terms: Fast text search (indexed)
- search_index: FTS5 virtual table
- processing_log: Audit trail

**Error Handling:**
- IntegrityError: Duplicate → skip
- OperationalError: Database locked → retry
- Exception → log and continue

**Performance:**
- Insert: <200ms
- Thumbnail generation: <100ms
- Search: <1 second (even with 10,000+ screenshots)

## Data Flow Through Agents

### Input/Output Chain

```python
# MonitorAgent
file_path: Path
    ↓
# OCRAgent
ocr_text: str = ocr.extract_text(file_path)
    ↓
# VisionAgent
vision_analysis: VisionAnalysis = vision.analyze_image(file_path, ocr_text)
    ↓
# ClassifierAgent
classification: ClassificationResult = classifier.classify(ocr_text, vision_analysis)
    ↓
# NamingAgent
new_filename: str = namer.generate_filename(
    category=classification.category,
    keywords=classification.keywords,
    file_path=file_path
)
    ↓
# OrganizerAgent
org_result: OrganizationResult = organizer.organize(
    source_path=file_path,
    classification=classification,
    new_filename=new_filename
)
    ↓
# IndexerAgent
screenshot_id: int = indexer.index_screenshot(
    file_path=file_path,
    processing_result=processing_result,
    classification=classification,
    new_filename=new_filename,
    new_path=org_result.destination_path
)
```

### Shared State

- **ProcessingResult:** Accumulates data from all agents
- **Statistics:** Tracks success/failure counts
- **Checkpoint:** Saves progress every 10 files
- **Database:** Persistent storage for all metadata

## Checkpoints and Resume Capability

### Checkpoint Strategy

**Save checkpoint every 10 files:**
```json
{
  "stats": {
    "total": 50,
    "success": 45,
    "failed": 3,
    "skipped": 2,
    "by_category": {
      "ERROR": 15,
      "CODE": 20,
      "UI": 10
    }
  },
  "timestamp": "2025-12-07T14:30:00"
}
```

**Checkpoint file:** `data/checkpoint.json`

### Resume Process

1. Load checkpoint on startup
2. Restore statistics
3. Continue from last processed file
4. No duplicate processing (database tracks processed files)

### Crash Recovery

- All file operations logged to `processing_log` table
- Can rollback moves within 24 hours
- Database transactions ensure consistency
- No data loss even on crash

## Error Handling Strategy

### Per-Agent Error Handling

**Pattern:**
```python
try:
    result = agent.process(input_data)
    stats['success'] += 1
except SpecificError as e:
    logger.error(f"Agent failed: {e}")
    stats['failed'] += 1
    # Continue with next file
```

### Error Categories

1. **Recoverable:** Retry with backoff (API errors)
2. **Skippable:** Log and continue (invalid files)
3. **Fatal:** Stop processing (database corruption)

### Graceful Degradation

- OCR fails → Continue with vision-only
- Vision fails → Use fallback classification
- Classification low confidence → Skip auto-organization
- One file fails → Continue with next file

## Performance Optimization

### Caching Strategy

- **OCR Cache:** File hash → text (persistent)
- **API Cache:** Could add response caching (future)
- **Database Indexes:** All search columns indexed

### Parallel Processing

**Current:** Sequential (one file at a time)
**Reason:** Simplicity, easier debugging, API rate limits

**Future:** Could parallelize OCR (no API calls)

### Database Optimization

- Indexes on: category, created_date, file_hash, search terms
- FTS5 for full-text search
- Vacuum periodically
- Connection pooling (future)

### API Rate Limiting

- Exponential backoff on 429 errors
- Configurable delay between requests
- Track API usage and costs

## Extension Points

### Adding New Agents

1. Create `src/agents/new_agent.py`
2. Implement `process()` method
3. Add to pipeline in `src/main.py`
4. Update `AGENTS.md`
5. Add tests in `tests/test_new_agent.py`

### Adding New Categories

1. Update `ClassifierAgent` prompt
2. Update `NamingAgent` category codes
3. Update `OrganizerAgent` folder structure
4. Update documentation

### Adding New Search Features

1. Add columns to database schema
2. Update `IndexerAgent` to populate
3. Update `SearchEngine` with new filters
4. Add tests

### Integration Points

- **Web UI:** Could add Flask/FastAPI frontend
- **Mobile App:** Could add API endpoints
- **Cloud Storage:** Could sync to S3/Google Drive
- **Notifications:** Could add Slack/email alerts

## Success Criteria

### Functional Requirements

- ✅ Detect 100% of new screenshots
- ✅ Extract text from 95%+ of screenshots with text
- ✅ Classify with 90%+ accuracy
- ✅ Organize 95%+ automatically (confidence >= 0.6)
- ✅ Search returns results in <1 second
- ✅ Zero data loss (all files tracked)

### Non-Functional Requirements

- ✅ Process 5-8 seconds per screenshot (first time)
- ✅ Process 3-5 seconds per screenshot (cached OCR)
- ✅ Handle 10,000+ screenshots without performance degradation
- ✅ Graceful error recovery (no crashes)
- ✅ Resume from checkpoints (no duplicate work)
- ✅ Cross-platform (Windows + Mac)

### Quality Metrics

- ✅ 80%+ code coverage
- ✅ All functions type-hinted
- ✅ Zero security vulnerabilities
- ✅ PEP 8 compliant
- ✅ Comprehensive documentation

## Related Documentation

- **Agent Details:** `AGENTS.md`
- **Code Standards:** `.kiro/steering/steering.md`
- **Testing:** `.kiro/steering/testing-standards.md`
- **Conventions:** `.kiro/steering/code-conventions.md`
