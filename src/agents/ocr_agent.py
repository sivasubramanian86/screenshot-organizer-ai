"""OCR agent for extracting text from screenshots using Tesseract."""
import hashlib
from pathlib import Path
from typing import Optional
import pytesseract
from PIL import Image
from loguru import logger


class OCRAgent:
    """Extract text from images using Tesseract OCR."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path("data/ocr_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._verify_tesseract()
    
    def _verify_tesseract(self) -> None:
        """Verify Tesseract is installed."""
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            raise RuntimeError(
                "Tesseract OCR is not installed or not in PATH.\n"
                "Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                "Mac: brew install tesseract\n"
                "Linux: sudo apt-get install tesseract-ocr"
            )
    
    def _get_image_hash(self, image_path: Path) -> str:
        """Calculate SHA256 hash of image file."""
        sha256 = hashlib.sha256()
        with open(image_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _get_cached_text(self, image_hash: str) -> Optional[str]:
        """Retrieve cached OCR result."""
        cache_file = self.cache_dir / f"{image_hash}.txt"
        if cache_file.exists():
            logger.debug(f"Cache hit for {image_hash[:8]}")
            return cache_file.read_text(encoding='utf-8')
        return None
    
    def _cache_text(self, image_hash: str, text: str) -> None:
        """Cache OCR result."""
        cache_file = self.cache_dir / f"{image_hash}.txt"
        cache_file.write_text(text, encoding='utf-8')
    
    def extract_text(self, image_path: Path) -> str:
        """Extract text from image using OCR."""
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Check file size (50MB limit)
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            raise ValueError(f"Image too large: {file_size_mb:.1f}MB (max 50MB)")
        
        # Check cache
        image_hash = self._get_image_hash(image_path)
        cached_text = self._get_cached_text(image_hash)
        if cached_text is not None:
            return cached_text
        
        # Extract text
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='eng')
            text = text.strip()
            
            # Cache result
            self._cache_text(image_hash, text)
            
            logger.info(f"OCR extracted {len(text)} characters from {image_path.name}")
            return text
        
        except Exception as e:
            logger.error(f"OCR failed for {image_path.name}: {e}")
            return ""
    
    def clear_cache(self) -> None:
        """Clear OCR cache."""
        for cache_file in self.cache_dir.glob("*.txt"):
            cache_file.unlink()
        logger.info("OCR cache cleared")
