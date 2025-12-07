# Project Structure

## Directory Organization

```
ScreenShot_Organizer/
├── src/                          # Core application code
│   ├── agents/                   # Processing pipeline agents
│   ├── schemas/                  # Data models and validation
│   ├── utils/                    # Shared utilities
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   └── __main__.py               # Module execution support
├── config/                       # Configuration files
│   ├── config.yaml               # Main application settings
│   ├── .env                      # API keys and secrets
│   ├── .env.example              # Environment template
│   ├── .env.gemini               # Gemini API configuration
│   └── .env.bedrock              # AWS Bedrock configuration
├── data/                         # Runtime data storage
│   ├── screenshots.db            # SQLite database
│   └── ocr_cache/                # Cached OCR results
├── logs/                         # Application logs
├── tests/                        # Unit and integration tests
├── examples/                     # Usage examples for each agent
└── .amazonq/rules/memory-bank/   # Project documentation
```

## Core Components

### Agent Pipeline Architecture
The application follows an agent-based pipeline pattern where each agent performs a specific task:

```
File Monitor → OCR Agent → Vision Agent → Classifier → Naming Agent → Organizer → Indexer
                                                                                      ↓
                                                                              SQLite Database
```

### src/agents/
**Processing Pipeline Agents**

- **monitor_agent.py**: File system monitoring using watchdog library
  - Detects new screenshots in configured directories
  - Handles file completion detection
  - Triggers processing pipeline for new files

- **ocr_agent.py**: Text extraction using Tesseract OCR
  - Extracts text content from screenshots
  - Implements caching to avoid redundant processing
  - Handles OCR errors gracefully

- **vision_agent.py**: AI vision analysis (Claude)
- **vision_agent_gemini.py**: AI vision analysis (Google Gemini - FREE)
- **vision_agent_bedrock.py**: AI vision analysis (AWS Bedrock)
  - Analyzes visual content beyond text
  - Generates descriptive summaries
  - Provides context for classification

- **classifier_agent.py**: Content categorization
  - Classifies screenshots into 7 categories
  - Provides confidence scores
  - Uses both OCR and vision analysis

- **naming_agent.py**: Intelligent filename generation
  - Creates descriptive filenames from content
  - Handles length limits and special characters
  - Ensures filename uniqueness

- **organizer_agent.py**: File organization and movement
  - Creates category-based folder structure
  - Moves/copies files to organized locations
  - Handles duplicate filenames

- **indexer_agent.py**: Database indexing
  - Stores metadata in SQLite database
  - Generates and stores thumbnails
  - Maintains processing audit log

### src/schemas/
**Data Models and Validation**

- **models.py**: Pydantic models for data validation
  - ScreenshotMetadata: Core screenshot data structure
  - ProcessingResult: Pipeline processing results
  - Category enumeration and validation
  - Ensures type safety throughout pipeline

### src/utils/
**Shared Utilities**

- **config.py**: Configuration loading and validation
  - Loads config.yaml and .env files
  - Provides typed configuration access
  - Handles environment variable substitution

- **database.py**: SQLite database management
  - Schema initialization and migrations
  - Connection pooling and management
  - FTS5 full-text search setup
  - Thumbnail BLOB storage

- **logger.py**: Centralized logging
  - Configurable log levels
  - File and console output
  - Log rotation and archiving

- **platform_utils.py**: Cross-platform compatibility
  - OS detection (Windows/Mac/Linux)
  - Platform-specific path resolution
  - Default screenshot folder detection

- **search_engine.py**: Full-text search functionality
  - FTS5-based text search
  - Ranking and relevance scoring
  - Filter by category, date, confidence

- **user_corrections.py**: User feedback handling
  - Allows manual category corrections
  - Improves classification over time
  - Maintains correction history

### config/
**Configuration Management**

- **config.yaml**: Main application configuration
  - Source folders (platform-specific)
  - Processing settings (OCR, vision, organization)
  - Database and logging configuration
  - Monitoring and file handling settings

- **.env files**: API keys and secrets
  - Separate configurations for Claude, Gemini, Bedrock
  - Environment-specific overrides
  - Not committed to version control

### data/
**Runtime Data Storage**

- **screenshots.db**: SQLite database
  - screenshots table: Metadata and content
  - search_index table: FTS5 virtual table
  - processing_log table: Audit trail

- **ocr_cache/**: Cached OCR results
  - Avoids redundant OCR processing
  - Keyed by file hash

### tests/
**Test Suite**

- Unit tests for each agent
- Integration tests for pipeline
- Platform-specific tests
- Database and search tests

### examples/
**Usage Examples**

- Standalone examples for each agent
- Demonstrates API usage
- Useful for testing and development

## Architectural Patterns

### Agent-Based Pipeline
- Each agent is independent and testable
- Agents communicate via Pydantic models
- Pipeline can be extended with new agents
- Supports parallel processing (configurable)

### Configuration-Driven
- All behavior controlled via config.yaml
- Environment-specific overrides via .env
- No hardcoded paths or settings
- Easy customization without code changes

### Database-Centric
- SQLite as single source of truth
- FTS5 for fast full-text search
- Audit log for rollback capability
- Thumbnail storage for quick previews

### Cross-Platform Design
- Platform detection at runtime
- OS-specific path handling
- Graceful fallbacks for missing features
- Consistent behavior across platforms

## Key Relationships

1. **main.py** orchestrates the entire pipeline
2. **monitor_agent** triggers processing for new files
3. **ocr_agent** and **vision_agent** run in parallel (optional)
4. **classifier_agent** uses outputs from OCR and vision
5. **naming_agent** generates filename from classification
6. **organizer_agent** moves file to category folder
7. **indexer_agent** stores all metadata in database
8. **search_engine** queries database for retrieval
