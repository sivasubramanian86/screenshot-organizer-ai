"""Tests for platform utilities."""
import pytest
from pathlib import Path
from src.utils.platform_utils import (
    get_os_type,
    get_home_directory,
    get_screenshot_folder,
    is_valid_image_file,
    is_temporary_file,
    ensure_directory_exists
)


class TestOSDetection:
    """Test OS detection functions."""
    
    def test_get_os_type(self):
        """Test OS type detection."""
        os_type = get_os_type()
        assert os_type in ["windows", "mac", "linux"]
    
    def test_get_home_directory(self):
        """Test home directory detection."""
        home = get_home_directory()
        assert home.exists()
        assert home.is_dir()


class TestScreenshotFolder:
    """Test screenshot folder detection."""
    
    def test_get_screenshot_folder_windows(self):
        """Test Windows screenshot folder path."""
        folder = get_screenshot_folder("windows")
        assert "Pictures" in str(folder)
        assert "Screenshots" in str(folder)
    
    def test_get_screenshot_folder_mac(self):
        """Test Mac screenshot folder path."""
        folder = get_screenshot_folder("mac")
        assert "Pictures" in str(folder) or "Desktop" in str(folder)
    
    def test_get_screenshot_folder_auto(self):
        """Test auto-detection of screenshot folder."""
        folder = get_screenshot_folder()
        assert isinstance(folder, Path)


class TestFileValidation:
    """Test file validation functions."""
    
    @pytest.mark.parametrize("filename,expected", [
        ("screenshot.png", True),
        ("image.jpg", True),
        ("photo.jpeg", True),
        ("pic.webp", True),
        ("bitmap.bmp", True),
        ("animation.gif", True),
        ("document.pdf", False),
        ("text.txt", False),
        ("video.mp4", False),
        ("Screenshot.PNG", True),  # Case insensitive
    ])
    def test_is_valid_image_file(self, filename: str, expected: bool):
        """Test image file validation."""
        assert is_valid_image_file(filename) == expected
    
    @pytest.mark.parametrize("filename,expected", [
        ("screenshot.png", False),
        ("file.tmp", True),
        ("backup~", True),
        (".DS_Store", True),
        ("Thumbs.db", True),
        ("download.crdownload", True),
        ("transfer.part", True),
        ("normal_file.jpg", False),
    ])
    def test_is_temporary_file(self, filename: str, expected: bool):
        """Test temporary file detection."""
        assert is_temporary_file(filename) == expected


class TestDirectoryOperations:
    """Test directory operations."""
    
    def test_ensure_directory_exists(self, tmp_path):
        """Test directory creation."""
        test_dir = tmp_path / "test" / "nested" / "folder"
        ensure_directory_exists(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()
    
    def test_ensure_directory_exists_already_exists(self, tmp_path):
        """Test that existing directory doesn't raise error."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        ensure_directory_exists(test_dir)  # Should not raise
        assert test_dir.exists()


class TestIntegration:
    """Integration tests."""
    
    def test_full_path_detection(self):
        """Test complete path detection workflow."""
        os_type = get_os_type()
        home = get_home_directory()
        screenshot_folder = get_screenshot_folder(os_type)
        
        assert os_type in ["windows", "mac", "linux"]
        assert home.exists()
        assert isinstance(screenshot_folder, Path)
        assert str(home) in str(screenshot_folder)
