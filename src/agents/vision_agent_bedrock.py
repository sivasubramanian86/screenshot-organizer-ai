"""Vision Agent using AWS Bedrock (Claude via AWS - no minimum charge)"""
import base64
import json
import time
from pathlib import Path
from typing import Optional
import boto3
from loguru import logger
from ..schemas.models import VisionAnalysis


class VisionAgentBedrock:
    """Analyze screenshots using AWS Bedrock Claude (pay-per-use, no minimum)"""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.region = region
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)
        logger.info(f"Initialized Bedrock Vision Agent: {model_id}")
    
    def analyze_image(self, image_path: Path, max_retries: int = 3) -> Optional[VisionAnalysis]:
        """Analyze screenshot with AWS Bedrock Claude"""
        for attempt in range(max_retries):
            try:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1024,
                    "messages": [{
                        "role": "user",
                        "content": [{
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64
                            }
                        }, {
                            "type": "text",
                            "text": """Analyze this screenshot and provide JSON:
{
  "main_subject": "brief description",
  "context": "application/environment",
  "key_elements": ["element1", "element2"],
  "purpose": "likely user intent"
}"""
                        }]
                    }]
                })
                
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=body
                )
                
                result = json.loads(response["body"].read())
                text = result["content"][0]["text"].strip()
                
                if text.startswith("```json"):
                    text = text[7:-3].strip()
                
                data = json.loads(text)
                
                return VisionAnalysis(
                    main_subject=data.get("main_subject", ""),
                    context=data.get("context", ""),
                    key_elements=data.get("key_elements", []),
                    purpose=data.get("purpose", ""),
                    confidence=0.95
                )
                
            except Exception as e:
                logger.warning(f"Bedrock attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All Bedrock attempts failed for {image_path}")
                    return None
        
        return None
