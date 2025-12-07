"""Cross-platform utilities for OS detection and path handling."""
import platform
from pathlib import Path
from typing import Literal


OSType = Literal["windows", "mac", "linux"]


def get_os_type() -> OSType:
    """Detect operating system."""
    system = platform.system().lower()
    if system == "darwin":
        return "mac"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def get_home_directory() -> Path:
    """Get user home directory cross-platform."""
    return Path.home()


def get_screenshot_folder(os_type: OSType | None = None) -> Path:
    """Get default screenshot folder for the OS."""
    if os_type is None:
        os_type = get_os_type()
    
    home = get_home_directory()
    
    if os_type == "windows":
        # Windows: C:\Users\[USERNAME]\Pictures\Screenshots
        return home / "Pictures" / "Screenshots"
    elif os_type == "mac":
        # Mac: ~/Pictures/Screenshots or ~/Desktop (default)
        screenshots_path = home / "Pictures" / "Screenshots"
        if not screenshots_path.exists():
            # Fallback to Desktop where Mac saves screenshots by default
            return home / "Desktop"
        return screenshots_path
    else:
        # Linux: ~/Pictures or ~/Pictures/Screenshots
        return home / "Pictures"


def is_valid_image_file(filename: str) -> bool:
    """Check if filename is a valid image format."""
    valid_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
    return Path(filename).suffix.lower() in valid_extensions


def is_temporary_file(filename: str) -> bool:
    """Check if file is temporary/cache file to ignore."""
    temp_patterns = {".tmp", "~", ".DS_Store", "Thumbs.db", ".crdownload", ".part"}
    name = filename.lower()
    
    # Check exact matches
    if name in {".ds_store", "thumbs.db"}:
        return True
    
    # Check extensions and patterns
    for pattern in temp_patterns:
        if name.endswith(pattern) or pattern in name:
            return True
    
    return False


def ensure_directory_exists(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
