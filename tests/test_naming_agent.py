"""Tests for Naming agent."""
import pytest
from pathlib import Path
from datetime import datetime
from PIL import Image
from src.agents.naming_agent import NamingAgent


@pytest.fixture
def test_image(tmp_path):
    """Create a test image."""
    img = Image.new('RGB', (100, 100), color='red')
    image_path = tmp_path / "test.png"
    img.save(image_path)
    return image_path


class TestNamingAgent:
    """Test NamingAgent class."""
    
    def test_init(self):
        """Test initialization."""
        agent = NamingAgent()
        assert agent.max_length == 200
    
    def test_generate_filename_error(self, test_image):
        """Test filename generation for error screenshot."""
        agent = NamingAgent()
        
        filename = agent.generate_filename(
            category="ERROR",
            keywords=["database", "timeout", "connection"],
            file_path=test_image,
            created_date=datetime(2025, 12, 7)
        )
        
        assert filename.startswith("2025-12-07_")
        assert "Error" in filename
        assert filename.endswith(".png")
        assert len(filename) <= 200
    
    def test_generate_filename_code(self, test_image):
        """Test filename generation for code screenshot."""
        agent = NamingAgent()
        
        filename = agent.generate_filename(
            category="CODE",
            keywords=["python", "async", "await"],
            file_path=test_image,
            created_date=datetime(2025, 12, 7)
        )
        
        assert "2025-12-07" in filename
        assert "Code-Python" in filename or "Code" in filename
        assert ".png" in filename
    
    def test_generate_filename_ui(self, test_image):
        """Test filename generation for UI screenshot."""
        agent = NamingAgent()
        
        filename = agent.generate_filename(
            category="UI",
            keywords=["dashboard", "analytics"],
            file_path=test_image,
            created_date=datetime(2025, 12, 7)
        )
        
        assert "UI" in filename
        assert "Dashboard" in filename or "Analytics" in filename
    
    def test_category_code_error_with_http(self, test_image):
        """Test category code for HTTP error."""
        agent = NamingAgent()
        
        code = agent._get_category_code("ERROR", ["404", "not_found"])
        assert code == "Error-404" or code == "Error"
    
    def test_category_code_code_with_language(self, test_image):
        """Test category code for code with language."""
        agent = NamingAgent()
        
        code = agent._get_category_code("CODE", ["python", "function"])
        assert code == "Code-Python"
    
    def test_format_keywords(self):
        """Test keyword formatting."""
        agent = NamingAgent()
        
        result = agent._format_keywords(["database", "timeout", "connection"])
        assert result == "Database_Timeout_Connection"
    
    def test_format_keywords_limit(self):
        """Test keyword limit to 4."""
        agent = NamingAgent()
        
        result = agent._format_keywords(["k1", "k2", "k3", "k4", "k5", "k6"])
        parts = result.split("_")
        assert len(parts) <= 4
    
    def test_format_keywords_sanitize(self):
        """Test keyword sanitization."""
        agent = NamingAgent()
        
        result = agent._format_keywords(["data-base", "time/out", "con:nect"])
        assert "-" not in result
        assert "/" not in result
        assert ":" not in result
    
    def test_file_hash_consistency(self, test_image):
        """Test that same file produces same hash."""
        agent = NamingAgent()
        
        hash1 = agent._get_file_hash(test_image)
        hash2 = agent._get_file_hash(test_image)
        
        assert hash1 == hash2
        assert len(hash1) == 4
    
    def test_sanitize_filename_special_chars(self):
        """Test sanitization of special characters."""
        agent = NamingAgent()
        
        filename = 'test<>:"/\\|?*.png'
        sanitized = agent._sanitize_filename(filename)
        
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert '"' not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert "|" not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized
    
    def test_sanitize_filename_spaces(self):
        """Test space replacement."""
        agent = NamingAgent()
        
        filename = "test file name.png"
        sanitized = agent._sanitize_filename(filename)
        
        assert " " not in sanitized
        assert "_" in sanitized
    
    def test_sanitize_filename_multiple_underscores(self):
        """Test removal of multiple underscores."""
        agent = NamingAgent()
        
        filename = "test___file___name.png"
        sanitized = agent._sanitize_filename(filename)
        
        assert "___" not in sanitized
        assert "__" not in sanitized
    
    def test_sanitize_filename_reserved_names(self):
        """Test handling of Windows reserved names."""
        agent = NamingAgent()
        
        reserved_names = ["CON.png", "PRN.png", "AUX.png", "COM1.png"]
        
        for name in reserved_names:
            sanitized = agent._sanitize_filename(name)
            assert sanitized.startswith("File_")
    
    def test_truncate_filename_short(self):
        """Test that short filenames are not truncated."""
        agent = NamingAgent()
        
        filename = "short_name.png"
        truncated = agent._truncate_filename(filename, ".png")
        
        assert truncated == filename
    
    def test_truncate_filename_long(self):
        """Test truncation of long filenames."""
        agent = NamingAgent(max_length=50)
        
        filename = "a" * 100 + ".png"
        truncated = agent._truncate_filename(filename, ".png")
        
        assert len(truncated) <= 50
        assert truncated.endswith(".png")
    
    def test_truncate_filename_at_boundary(self):
        """Test truncation at underscore boundary."""
        agent = NamingAgent(max_length=30)
        
        filename = "part1_part2_part3_part4_part5.png"
        truncated = agent._truncate_filename(filename, ".png")
        
        assert len(truncated) <= 30
        assert truncated.endswith(".png")
        # Should truncate at underscore
        assert not truncated[:-4].endswith("_")
    
    def test_handle_duplicate_no_conflict(self, tmp_path):
        """Test duplicate handling when no conflict."""
        agent = NamingAgent()
        
        filename = "test.png"
        result = agent.handle_duplicate(filename, tmp_path)
        
        assert result == filename
    
    def test_handle_duplicate_with_conflict(self, tmp_path):
        """Test duplicate handling with existing file."""
        agent = NamingAgent()
        
        # Create existing file
        existing = tmp_path / "test.png"
        existing.touch()
        
        filename = "test.png"
        result = agent.handle_duplicate(filename, tmp_path)
        
        assert result == "test(1).png"
    
    def test_handle_duplicate_multiple_conflicts(self, tmp_path):
        """Test duplicate handling with multiple existing files."""
        agent = NamingAgent()
        
        # Create existing files
        (tmp_path / "test.png").touch()
        (tmp_path / "test(1).png").touch()
        (tmp_path / "test(2).png").touch()
        
        filename = "test.png"
        result = agent.handle_duplicate(filename, tmp_path)
        
        assert result == "test(3).png"


class TestNamingIntegration:
    """Integration tests for naming agent."""
    
    def test_full_filename_generation(self, test_image):
        """Test complete filename generation pipeline."""
        agent = NamingAgent()
        
        filename = agent.generate_filename(
            category="ERROR",
            keywords=["database", "connection", "timeout", "failed"],
            file_path=test_image,
            created_date=datetime(2025, 12, 7, 14, 30)
        )
        
        # Verify structure
        assert filename.startswith("2025-12-07_")
        assert "Error" in filename
        assert filename.endswith(".png")
        assert len(filename) <= 200
        
        # Verify no invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            assert char not in filename
    
    def test_different_categories(self, test_image):
        """Test filename generation for all categories."""
        agent = NamingAgent()
        
        categories = [
            ("ERROR", ["database", "timeout"]),
            ("CODE", ["python", "async"]),
            ("UI", ["dashboard", "analytics"]),
            ("DOCUMENTATION", ["api", "docs"]),
            ("DATA", ["chart", "report"]),
            ("COMMUNICATION", ["slack", "message"]),
            ("OTHER", ["misc"])
        ]
        
        for category, keywords in categories:
            filename = agent.generate_filename(
                category=category,
                keywords=keywords,
                file_path=test_image,
                created_date=datetime(2025, 12, 7)
            )
            
            assert len(filename) > 0
            assert filename.endswith(".png")
            assert len(filename) <= 200
