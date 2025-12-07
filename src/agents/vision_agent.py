"""Vision agent for analyzing screenshots using Claude Vision API."""
import base64
import time
import os
from pathlib import Path
from typing import Optional
import anthropic
from loguru import logger

from ..schemas.models import VisionAnalysis


class VisionAgent:
    """Analyze images using Claude Vision API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1000,
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Claude API key not found. Set ANTHROPIC_API_KEY environment variable.\n"
                "Get your key from: https://console.anthropic.com/"
            )
        
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def _encode_image(self, image_path: Path) -> tuple[str, str]:
        """Encode image to base64."""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Detect media type
        suffix = image_path.suffix.lower()
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        media_type = media_type_map.get(suffix, 'image/jpeg')
        
        encoded = base64.standard_b64encode(image_data).decode('utf-8')
        return encoded, media_type
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            
            except anthropic.RateLimitError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
            
            except anthropic.APITimeoutError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Timeout, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
            
            except anthropic.APIConnectionError as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Connection error, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait_time)
    
    def analyze_image(self, image_path: Path, ocr_text: Optional[str] = None) -> VisionAnalysis:
        """Analyze image using Claude Vision API."""
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Check file size
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            raise ValueError(f"Image too large: {file_size_mb:.1f}MB (max 50MB)")
        
        # Encode image
        image_data, media_type = self._encode_image(image_path)
        
        # Build prompt
        prompt = """Analyze this screenshot and provide a structured analysis.

Return a JSON object with:
- description: Brief description (1-2 sentences) of what the image shows
- content_type: One of: error, code, ui, design, document, screenshot, other
- objects_detected: List of main objects/elements visible
- keywords: List of 5-10 important keywords/topics
- has_text: Boolean indicating if image contains readable text
- confidence: Float 0.0-1.0 indicating analysis confidence

Be concise and accurate."""

        if ocr_text:
            prompt += f"\n\nOCR extracted text:\n{ocr_text[:500]}"
        
        # Call API with retry
        try:
            response = self._retry_with_backoff(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }],
                timeout=self.timeout
            )
            
            # Parse response
            content = response.content[0].text
            
            # Extract JSON from response
            import json
            import re
            
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback parsing
                result = {
                    "description": content[:200],
                    "content_type": "other",
                    "objects_detected": [],
                    "keywords": [],
                    "has_text": bool(ocr_text),
                    "confidence": 0.5
                }
            
            # Create VisionAnalysis object
            analysis = VisionAnalysis(
                description=result.get("description", ""),
                content_type=result.get("content_type", "other"),
                objects_detected=result.get("objects_detected", []),
                keywords=result.get("keywords", []),
                has_text=result.get("has_text", False),
                confidence=float(result.get("confidence", 0.5))
            )
            
            logger.info(f"Vision analysis complete: {analysis.content_type} (confidence: {analysis.confidence:.2f})")
            return analysis
        
        except anthropic.AuthenticationError:
            raise ValueError("Invalid Claude API key. Check your ANTHROPIC_API_KEY.")
        
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise
