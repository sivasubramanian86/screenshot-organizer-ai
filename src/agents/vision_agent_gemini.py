"""Vision Agent using Google Gemini (FREE tier available)"""
import base64
import time
from pathlib import Path
from typing import Optional
import google.generativeai as genai
from loguru import logger
from ..schemas.models import VisionAnalysis


class VisionAgentGemini:
    """Analyze screenshots using Google Gemini Vision (FREE tier: 15 req/min)"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"Initialized Gemini Vision Agent with model: {self.model_name}")
    
    def analyze_image(self, image_path: Path, ocr_text: Optional[str] = None) -> VisionAnalysis:
        """Analyze screenshot with Gemini Vision API"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                prompt = """Analyze this screenshot and provide:
1. Main subject (what is shown)
2. Context (application, website, or environment)
3. Key elements (UI components, text, graphics)
4. Purpose (what the user was doing)

Format as JSON:
{
  "main_subject": "brief description",
  "context": "application/environment",
  "key_elements": ["element1", "element2"],
  "purpose": "likely user intent"
}"""
                
                # Use PIL to load image for Gemini
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_data))
                response = self.model.generate_content([prompt, img])
                
                # Parse response
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3].strip()
                
                import json
                data = json.loads(text)
                
                # Map to VisionAnalysis format
                description = data.get("main_subject", "") + ". " + data.get("purpose", "")
                return VisionAnalysis(
                    description=description,
                    content_type="other",
                    objects_detected=data.get("key_elements", []),
                    keywords=data.get("key_elements", [])[:10],
                    has_text=bool(ocr_text),
                    confidence=0.85
                )
                
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All Gemini API attempts failed for {image_path}")
                    # Return fallback
                    return VisionAnalysis(
                        description="Screenshot analysis unavailable",
                        content_type="other",
                        objects_detected=[],
                        keywords=[],
                        has_text=bool(ocr_text),
                        confidence=0.3
                    )
        
        return VisionAnalysis(
            description="Screenshot analysis unavailable",
            content_type="other",
            objects_detected=[],
            keywords=[],
            has_text=bool(ocr_text),
            confidence=0.3
        )
