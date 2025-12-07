"""Configuration loader for Screenshot Organizer."""
import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """Load and manage application configuration."""
    
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path("config/config.yaml")
        self.config: Dict[str, Any] = {}
        self._load_env()
        self._load_yaml()
    
    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path("config/.env")
        if env_path.exists():
            load_dotenv(env_path)
    
    def _load_yaml(self) -> None:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: str | None = None) -> str | None:
        """Get environment variable."""
        return os.getenv(key, default)
