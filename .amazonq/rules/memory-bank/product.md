# Product Overview

## Purpose
AI-Powered Screenshot Organizer is an intelligent automation system that monitors, analyzes, and organizes screenshots using OCR and AI vision APIs. It automatically categorizes screenshots, extracts text content, generates descriptive filenames, and maintains a searchable database for efficient retrieval.

## Value Proposition
- **Eliminates Manual Organization**: Automatically processes and categorizes screenshots without user intervention
- **Intelligent Content Analysis**: Uses OCR (Tesseract) and AI vision (Claude/Gemini/Bedrock) to understand screenshot content
- **Smart Categorization**: Classifies screenshots into 7 categories (ERROR, CODE, UI, DOCUMENTATION, DATA, COMMUNICATION, OTHER)
- **Searchable Archive**: Full-text search across OCR text, AI descriptions, and metadata via SQLite FTS5
- **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux

## Key Features

### Automatic Monitoring
- Real-time file system monitoring of screenshot directories
- Configurable file extensions (.png, .jpg, .jpeg, .webp, .bmp, .gif)
- Handles file completion detection to avoid processing incomplete files
- Platform-specific default paths with customization support

### OCR Text Extraction
- Tesseract-based optical character recognition
- Caching system to avoid redundant processing
- Configurable language support (default: English)
- Extracts text from screenshots for searchability

### AI Vision Analysis
- Multiple API options: Claude (Anthropic), Gemini (FREE), AWS Bedrock
- Analyzes visual content beyond text (UI elements, diagrams, charts)
- Generates descriptive summaries and context
- Configurable models and token limits

### Smart Classification
- 7-category taxonomy for screenshot types
- Confidence scoring for classification accuracy
- Handles ambiguous cases with fallback to OTHER category
- Categories: ERROR, CODE, UI, DOCUMENTATION, DATA, COMMUNICATION, OTHER

### Intelligent File Organization
- Generates descriptive filenames based on content analysis
- Organizes files into category-based folder structure
- Preserves original files optionally
- Configurable filename length limits
- Handles duplicate filenames gracefully

### Database Indexing
- SQLite database with full-text search (FTS5)
- Stores metadata: filename, category, OCR text, AI analysis, timestamps
- Thumbnail generation and storage (BLOB)
- Processing audit log for rollback capability
- Search engine with ranking and filtering

## Target Users

### Developers
- Organize error screenshots and stack traces
- Archive code snippets and terminal outputs
- Maintain searchable documentation screenshots

### Designers
- Categorize UI mockups and design references
- Archive interface screenshots with descriptions
- Search design patterns and inspirations

### Technical Writers
- Organize documentation screenshots
- Maintain searchable image libraries
- Track diagram and flowchart versions

### General Users
- Automatically organize cluttered screenshot folders
- Search screenshots by content, not just filename
- Maintain clean, categorized screenshot archives

## Use Cases

1. **Error Tracking**: Automatically categorize and index error messages for debugging
2. **Code Reference Library**: Build searchable archive of code snippets and terminal commands
3. **UI Pattern Collection**: Organize interface screenshots for design reference
4. **Documentation Management**: Maintain categorized library of documentation screenshots
5. **Data Visualization Archive**: Store and search charts, graphs, and reports
6. **Communication Records**: Archive important messages and conversations
7. **General Screenshot Cleanup**: Automatically organize years of unsorted screenshots
