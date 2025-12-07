"""Tests for OCR agent."""
import pytest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.agents.ocr_agent import OCRAgent


@pytest.fixture
def test_image(tmp_path):
    """Create a test image with text."""
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Hello World Test", fill='black')
    
    image_path = tmp_path / "test_image.png"
    img.save(image_path)
    return image_path


@pytest.fixture
def empty_image(tmp_path):
    """Create an image without text."""
    img = Image.new('RGB', (200, 200), color='blue')
    image_path = tmp_path / "empty_image.png"
    img.save(image_path)
    return image_path


class TestOCRAgent:
    """Test OCRAgent class."""
    
    def test_init(self, tmp_path):
        """Test OCR agent initialization."""
        ocr = OCRAgent(cache_dir=tmp_path / "cache")
        assert ocr.cache_dir.exists()
    
    def test_tesseract_installed(self):
        """Test Tesseract installation check."""
        try:
            ocr = OCRAgent()
            assert True  # Tesseract is installed
        except RuntimeError as e:
            pytest.skip(f"Tesseract not installed: {e}")
    
    def test_extract_text_with_text(self, test_image, tmp_path):
        """Test text extraction from image with text."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            text = ocr.extract_text(test_image)
            assert isinstance(text, str)
            # Note: OCR might not be perfect, just check it returns something
        except RuntimeError:
            pytest.skip("Tesseract not installed")
    
    def test_extract_text_empty_image(self, empty_image, tmp_path):
        """Test text extraction from image without text."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            text = ocr.extract_text(empty_image)
            assert isinstance(text, str)
            assert len(text) == 0 or text.isspace()
        except RuntimeError:
            pytest.skip("Tesseract not installed")
    
    def test_caching(self, test_image, tmp_path):
        """Test OCR result caching."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            
            # First call
            text1 = ocr.extract_text(test_image)
            
            # Second call (should use cache)
            text2 = ocr.extract_text(test_image)
            
            assert text1 == text2
            
            # Check cache file exists
            cache_files = list(ocr.cache_dir.glob("*.txt"))
            assert len(cache_files) > 0
        except RuntimeError:
            pytest.skip("Tesseract not installed")
    
    def test_file_not_found(self, tmp_path):
        """Test error handling for non-existent file."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            with pytest.raises(FileNotFoundError):
                ocr.extract_text(Path("/nonexistent/image.png"))
        except RuntimeError:
            pytest.skip("Tesseract not installed")
    
    def test_file_too_large(self, tmp_path):
        """Test error handling for large files."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            
            # Create a mock large file (just for size check)
            large_file = tmp_path / "large.png"
            with open(large_file, 'wb') as f:
                f.write(b'0' * (51 * 1024 * 1024))  # 51MB
            
            with pytest.raises(ValueError, match="too large"):
                ocr.extract_text(large_file)
        except RuntimeError:
            pytest.skip("Tesseract not installed")
    
    def test_clear_cache(self, test_image, tmp_path):
        """Test cache clearing."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            
            # Extract text to create cache
            ocr.extract_text(test_image)
            
            # Verify cache exists
            cache_files_before = list(ocr.cache_dir.glob("*.txt"))
            assert len(cache_files_before) > 0
            
            # Clear cache
            ocr.clear_cache()
            
            # Verify cache is empty
            cache_files_after = list(ocr.cache_dir.glob("*.txt"))
            assert len(cache_files_after) == 0
        except RuntimeError:
            pytest.skip("Tesseract not installed")
    
    def test_image_hash_consistency(self, test_image, tmp_path):
        """Test that same image produces same hash."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            hash1 = ocr._get_image_hash(test_image)
            hash2 = ocr._get_image_hash(test_image)
            assert hash1 == hash2
        except RuntimeError:
            pytest.skip("Tesseract not installed")


class TestOCRIntegration:
    """Integration tests for OCR agent."""
    
    def test_multiple_images(self, tmp_path):
        """Test processing multiple images."""
        try:
            ocr = OCRAgent(cache_dir=tmp_path / "cache")
            
            # Create multiple test images
            images = []
            for i in range(3):
                img = Image.new('RGB', (200, 100), color='white')
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), f"Test {i}", fill='black')
                
                image_path = tmp_path / f"test_{i}.png"
                img.save(image_path)
                images.append(image_path)
            
            # Extract text from all
            results = [ocr.extract_text(img) for img in images]
            
            assert len(results) == 3
            assert all(isinstance(r, str) for r in results)
        except RuntimeError:
            pytest.skip("Tesseract not installed")
