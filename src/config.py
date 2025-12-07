"""Configuration management with Pydantic validation."""
import os
from pathlib import Path
from typing import List, Dict, Optional
import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path("config/.env"))


class SourceFolders(BaseModel):
    """Source folder paths by OS."""
    windows: str
    mac: str
    linux: str = "~/Pictures"


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    file_extensions: List[str] = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]
    file_completion_wait_seconds: float = 1.0
    poll_interval_seconds: float = 1.0


class OCRConfig(BaseModel):
    """OCR configuration."""
    enabled: bool = True
    language: str = "eng"
    cache_dir: str = "./data/ocr_cache"


class ClaudeVisionConfig(BaseModel):
    """Claude Vision API configuration."""
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 1000
    timeout_seconds: int = 60
    max_retries: int = 3


class ProcessingConfig(BaseModel):
    """Processing configuration."""
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    parallel_processing: bool = False
    max_retries: int = 3
    timeout_seconds: int = 60
    max_image_size_mb: int = 50
    thumbnail_size: List[int] = [150, 150]


class OrganizationConfig(BaseModel):
    """Organization configuration."""
    max_filename_length: int = 200
    preserve_original: bool = False


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "./data/screenshots.db"
    auto_backup: bool = True
    backup_dir: str = "./data/backups"
    enable_thumbnails: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "./logs/organizer.log"
    max_size_mb: int = 10
    backup_count: int = 5
    console: bool = True


class Config(BaseModel):
    """Main configuration."""
    source_folders: SourceFolders
    output_base: str = "./organized_screenshots"
    dry_run: bool = False
    recursive: bool = False
    exclude_patterns: List[str] = ["*.tmp", "*cache*", ".DS_Store", "Thumbs.db"]
    
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    claude_vision: ClaudeVisionConfig = Field(default_factory=ClaudeVisionConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    organization: OrganizationConfig = Field(default_factory=OrganizationConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @field_validator('output_base', 'database', mode='before')
    @classmethod
    def expand_paths(cls, v):
        """Expand ~ and environment variables in paths."""
        if isinstance(v, str):
            return os.path.expanduser(os.path.expandvars(v))
        elif isinstance(v, dict) and 'path' in v:
            v['path'] = os.path.expanduser(os.path.expandvars(v['path']))
        return v


def load_config(config_path: Path) -> Config:
    """Load and validate configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # Apply environment variable overrides
    if 'ANTHROPIC_API_KEY' in os.environ:
        # API key handled separately
        pass
    
    if 'OUTPUT_BASE' in os.environ:
        config_dict['output_base'] = os.environ['OUTPUT_BASE']
    
    if 'DRY_RUN' in os.environ:
        config_dict['dry_run'] = os.environ['DRY_RUN'].lower() == 'true'
    
    try:
        config = Config(**config_dict)
        return config
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")
