# Development Guidelines

## Code Quality Standards

### Formatting and Style
- **Line Length**: 100 characters maximum (enforced by black and ruff)
- **Target Python Version**: 3.11+ with modern type hints
- **Docstrings**: Triple-quoted strings at module and class level
  ```python
  """Module description."""
  
  class ClassName:
      """Class description."""
  ```
- **String Quotes**: Double quotes for docstrings, flexible for regular strings
- **Indentation**: 4 spaces (no tabs)

### Type Hints and Validation
- **Mandatory Type Hints**: All function parameters and return types must be annotated
  ```python
  def process_screenshot(self, file_path: Path) -> bool:
  ```
- **Optional Types**: Use `Optional[Type]` for nullable parameters
  ```python
  def organize(
      self,
      source_path: Path,
      classification: ClassificationResult,
      created_date: Optional[datetime] = None
  ) -> OrganizationResult:
  ```
- **Pydantic Models**: Use for all data structures requiring validation
  ```python
  class Config(BaseModel):
      source_folders: SourceFolders
      output_base: str = "./organized_screenshots"
      dry_run: bool = False
  ```
- **Field Validators**: Use Pydantic validators for complex validation
  ```python
  @field_validator('output_base', 'database', mode='before')
  @classmethod
  def expand_paths(cls, v):
      """Expand ~ and environment variables in paths."""
  ```

### Naming Conventions
- **Classes**: PascalCase with descriptive names ending in purpose
  - `MonitorAgent`, `OrganizerAgent`, `DatabaseManager`
- **Functions/Methods**: snake_case with verb prefixes
  - `process_screenshot()`, `generate_filename()`, `_sanitize_filename()`
- **Private Methods**: Prefix with single underscore
  - `_init_agents()`, `_get_file_hash()`, `_move_file()`
- **Constants**: UPPER_SNAKE_CASE
  - `WINDOWS_RESERVED`, `SCHEMA_SQL`
- **Variables**: snake_case, descriptive names
  - `file_path`, `ocr_text`, `vision_analysis`

### Import Organization
- **Standard Library**: First group
- **Third-Party**: Second group
- **Local Imports**: Third group with relative imports
  ```python
  import argparse
  import signal
  from pathlib import Path
  from typing import Optional, Dict, Any
  
  from loguru import logger
  from pydantic import BaseModel, Field
  
  from .config import load_config, Config
  from .agents.monitor_agent import MonitorAgent
  ```

## Architectural Patterns

### Agent-Based Design
- **Single Responsibility**: Each agent handles one specific task
  - `MonitorAgent`: File system watching only
  - `OCRAgent`: Text extraction only
  - `VisionAgent`: AI vision analysis only
- **Agent Initialization**: All agents initialized in orchestrator
  ```python
  def _init_agents(self) -> None:
      """Initialize all agents."""
      self.monitor = MonitorAgent(folder_path=source_folder)
      self.ocr = OCRAgent(cache_dir=Path(self.config.ocr.cache_dir))
      self.vision = VisionAgent(model=self.config.claude_vision.model)
  ```
- **Agent Communication**: Via Pydantic models, not direct coupling
  ```python
  classification = self.classifier.classify(ocr_text, vision_analysis=vision_analysis)
  org_result = self.organizer.organize(source_path, classification, created_date)
  ```

### Configuration-Driven Development
- **YAML Configuration**: All behavior controlled via `config.yaml`
- **Environment Variables**: Secrets and overrides via `.env` files
- **Pydantic Validation**: Type-safe configuration loading
  ```python
  config = load_config(args.config)
  if args.dry_run:
      config.dry_run = True
  ```
- **No Hardcoded Values**: All paths, thresholds, and settings configurable

### Error Handling Strategy
- **Try-Except Blocks**: Wrap all external operations
  ```python
  try:
      ocr_text = self.ocr.extract_text(file_path)
  except Exception as e:
      logger.warning(f"OCR failed: {e}")
  ```
- **Graceful Degradation**: Continue processing on non-critical failures
- **Result Objects**: Return success/failure status with error messages
  ```python
  return OrganizationResult(
      success=False,
      error_message="Source file not found"
  )
  ```
- **Logging**: Use loguru for structured logging at appropriate levels
  - `logger.info()`: Normal operations
  - `logger.warning()`: Recoverable issues
  - `logger.error()`: Failures requiring attention
  - `logger.debug()`: Detailed diagnostic information

### Database Patterns
- **Connection Management**: Explicit connect/close pattern
  ```python
  conn = sqlite3.connect(str(self.db_path))
  cursor = conn.cursor()
  # ... operations ...
  conn.commit()
  conn.close()
  ```
- **Schema Initialization**: Idempotent CREATE IF NOT EXISTS statements
- **Foreign Keys**: Enable with `PRAGMA foreign_keys = ON`
- **Indexes**: Create indexes for all frequently queried columns
  ```python
  cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON screenshots(category)")
  ```
- **FTS5 Integration**: Virtual tables with automatic sync via triggers
  ```python
  CREATE TRIGGER IF NOT EXISTS screenshots_ai AFTER INSERT ON screenshots BEGIN
      INSERT INTO search_index(...) VALUES (...);
  END
  ```

### Path Handling
- **pathlib.Path**: Use exclusively, never string concatenation
  ```python
  source_path = Path(source_path)
  destination_path = target_folder / new_filename
  ```
- **Path Validation**: Check existence before operations
  ```python
  if not source_path.exists():
      return OrganizationResult(success=False, error_message="Source file not found")
  ```
- **Cross-Platform**: Use Path methods for OS-agnostic operations
  ```python
  folder_path.mkdir(parents=True, exist_ok=True)
  ```

## Common Implementation Patterns

### File Hash Generation
```python
def _get_file_hash(self, file_path: Path) -> str:
    """Generate 4-character hash from file content."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()[:4]
```

### Filename Sanitization
```python
def _sanitize_filename(self, filename: str) -> str:
    """Remove invalid characters and handle reserved names."""
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    return filename.strip('_')
```

### Duplicate Handling
```python
def handle_duplicate(self, filename: str, target_dir: Path) -> str:
    """Handle duplicate filenames by appending (1), (2), etc."""
    if not (target_dir / filename).exists():
        return filename
    
    path = Path(filename)
    name = path.stem
    ext = path.suffix
    
    counter = 1
    while True:
        new_name = f"{name}({counter}){ext}"
        if not (target_dir / new_name).exists():
            return new_name
        counter += 1
        if counter > 1000:  # Safety limit
            raise ValueError("Too many duplicate files")
```

### Statistics Tracking
```python
self.stats = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'skipped': 0,
    'by_category': {}
}

# Update stats
self.stats['success'] += 1
category = classification.category
self.stats['by_category'][category] = self.stats['by_category'].get(category, 0) + 1
```

### Checkpoint/Resume Pattern
```python
def _save_checkpoint(self) -> None:
    """Save checkpoint."""
    self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    with open(self.checkpoint_file, 'w') as f:
        json.dump({
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)

def _load_checkpoint(self) -> None:
    """Load checkpoint for resume capability."""
    if self.checkpoint_file.exists():
        with open(self.checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        self.stats = checkpoint.get('stats', self.stats)
```

### Signal Handling for Graceful Shutdown
```python
def run(self) -> None:
    """Main loop."""
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    
    try:
        while self.running:
            # ... processing ...
    finally:
        self.shutdown()

def _signal_handler(self, signum, frame) -> None:
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    self.running = False
```

## Testing Standards

### Test File Naming
- Pattern: `test_<module_name>.py`
- Examples: `test_classifier_agent.py`, `test_naming_agent.py`

### Test Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=src --cov-report=html --cov-report=term"
```

### Coverage Target
- Minimum: 80% code coverage
- Focus on critical paths: file operations, database, classification

## Code Quality Tools

### Black (Formatter)
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

### Ruff (Linter)
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
```

### MyPy (Type Checker)
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true
```

## Best Practices

### Logging
- Use loguru logger, not print statements
- Include context in log messages
  ```python
  logger.info(f"Processing [{self.stats['total']}]: {file_path.name}")
  logger.error(f"Organization failed: {e}")
  ```
- Log at appropriate levels based on severity

### Resource Management
- Use context managers for file operations
  ```python
  with Image.open(file_path) as img:
      metadata.width = img.width
  ```
- Close database connections explicitly
- Clean up temporary files

### Dry Run Support
- Check `dry_run` flag before destructive operations
  ```python
  if not self.dry_run:
      success = self._move_file(source_path, destination_path)
  else:
      logger.info(f"[DRY RUN] Would move: {source_path.name}")
  ```

### Progress Reporting
- Periodic checkpoint saves (every 10 files)
- Progress statistics logging
- User-friendly output formatting

### Security
- Never commit API keys (use .env files)
- Validate file paths to prevent directory traversal
- Sanitize filenames to prevent injection
- Use parameterized SQL queries (implicit with sqlite3)

### Performance
- Cache expensive operations (OCR results)
- Use chunked file reading for hashing
- Batch database operations when possible
- Implement configurable parallel processing

### Cross-Platform Compatibility
- Use pathlib.Path for all file operations
- Detect OS and use platform-specific defaults
  ```python
  os_type = get_os_type()
  if os_type == "windows":
      source_folder = Path(config.source_folders.windows)
  ```
- Handle Windows reserved filenames
- Test on multiple platforms
