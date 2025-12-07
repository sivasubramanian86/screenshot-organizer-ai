"""Classifier agent for categorizing screenshots and extracting keywords."""
import os
import json
import re
from datetime import datetime
from typing import Optional
import anthropic
from loguru import logger

from ..schemas.models import ClassificationResult, VisionAnalysis


CLASSIFICATION_PROMPT = """Analyze this screenshot and classify it into ONE category.

**Categories:**
- ERROR: Error messages, stack traces, exceptions, bug reports
- CODE: Source code, IDE, terminal, git diffs, configs
- UI: Web/app interfaces, designs, mockups, forms
- DOCUMENTATION: Docs, diagrams, flowcharts, architecture
- DATA: Tables, charts, reports, spreadsheets, analytics
- COMMUNICATION: Slack, email, messages, comments
- OTHER: Anything that doesn't fit above

**Input Data:**
OCR Text: {ocr_text}
Vision Description: {vision_description}

**Required Output (JSON):**
{{
  "category": "ERROR|CODE|UI|DOCUMENTATION|DATA|COMMUNICATION|OTHER",
  "keywords": ["5-10", "important", "keywords", "sorted", "by", "relevance"],
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of classification"
}}

**Confidence Guidelines:**
- 0.9-1.0: Clear, obvious category with distinctive keywords
- 0.6-0.9: Some clues but not 100% certain
- <0.6: Ambiguous, could be multiple categories

**Keyword Guidelines:**
- Extract error codes, function names, technical terms
- Include programming languages if CODE
- Include error types if ERROR
- Include UI components if UI
- Prioritize specific over generic terms

Return ONLY valid JSON."""


class ClassifierAgent:
    """Classify screenshots into categories and extract keywords."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 500,
        use_api: bool = True
    ):
        self.use_api = use_api
        self.model = model
        self.max_tokens = max_tokens
        
        if use_api:
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.warning("Claude API key not found, using rule-based classification")
                self.use_api = False
            else:
                self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def classify(
        self,
        ocr_text: str,
        vision_analysis: Optional[VisionAnalysis] = None,
        vision_description: Optional[str] = None
    ) -> ClassificationResult:
        """Classify screenshot and extract keywords."""
        
        # Get vision description
        if vision_analysis:
            vision_desc = vision_analysis.description
        elif vision_description:
            vision_desc = vision_description
        else:
            vision_desc = "No visual description available"
        
        # Truncate inputs if too long
        ocr_preview = ocr_text[:1000] if ocr_text else "No text detected"
        vision_preview = vision_desc[:500]
        
        # Build prompt
        prompt = CLASSIFICATION_PROMPT.format(
            ocr_text=ocr_preview,
            vision_description=vision_preview
        )
        
        try:
            # Use API or fallback to rule-based
            if self.use_api and self.client:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = response.content[0].text
                result = self._parse_response(content)
            else:
                # Use rule-based classification
                return self._fallback_classification(ocr_text, vision_desc)
            
            # Generate folder suggestion
            folder = self._suggest_folder(result["category"], result["keywords"])
            
            # Create classification result
            classification = ClassificationResult(
                category=result["category"],
                keywords=result["keywords"],
                suggested_folder=folder,
                confidence=result["confidence"],
                tags=result["keywords"][:5]  # Top 5 as tags
            )
            
            logger.info(
                f"Classification: {classification.category} "
                f"(confidence: {classification.confidence:.2f})"
            )
            
            return classification
        
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            # Return fallback classification
            return self._fallback_classification(ocr_text, vision_desc)
    
    def _parse_response(self, content: str) -> dict:
        """Parse Claude's JSON response."""
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
        
        # Validate and normalize
        category = result.get("category", "OTHER").upper()
        valid_categories = {"ERROR", "CODE", "UI", "DOCUMENTATION", "DATA", "COMMUNICATION", "OTHER"}
        if category not in valid_categories:
            category = "OTHER"
        
        keywords = result.get("keywords", [])[:10]  # Max 10 keywords
        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        
        return {
            "category": category,
            "keywords": keywords,
            "confidence": confidence
        }
    
    def _suggest_folder(self, category: str, keywords: list[str]) -> str:
        """Suggest folder path based on category and keywords."""
        # Get current year-month
        date_folder = datetime.now().strftime("%Y-%m")
        
        # Base folder structure
        base = f"{date_folder}/{category}"
        
        # Add subcategory based on keywords
        subcategory = self._determine_subcategory(category, keywords)
        if subcategory:
            return f"{base}/{subcategory}"
        
        return base
    
    def _determine_subcategory(self, category: str, keywords: list[str]) -> Optional[str]:
        """Determine subcategory from keywords."""
        if not keywords:
            return None
        
        # Category-specific subcategory logic
        if category == "ERROR":
            # Look for error types
            error_types = {
                "database": "Database",
                "network": "Network",
                "timeout": "Network",
                "connection": "Network",
                "memory": "Runtime",
                "null": "Runtime",
                "undefined": "Runtime",
                "404": "HTTP",
                "500": "HTTP",
                "503": "HTTP"
            }
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for key, subcat in error_types.items():
                    if key in keyword_lower:
                        return subcat
        
        elif category == "CODE":
            # Look for programming languages
            languages = {
                "python": "Python",
                "javascript": "JavaScript",
                "typescript": "TypeScript",
                "java": "Java",
                "cpp": "CPP",
                "c++": "CPP",
                "rust": "Rust",
                "go": "Go",
                "config": "Config",
                "yaml": "Config",
                "json": "Config"
            }
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in languages:
                    return languages[keyword_lower]
        
        elif category == "UI":
            # Look for UI components
            ui_types = {
                "dashboard": "Dashboard",
                "login": "Auth",
                "signup": "Auth",
                "settings": "Settings",
                "form": "Forms",
                "table": "Tables"
            }
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in ui_types:
                    return ui_types[keyword_lower]
        
        elif category == "DATA":
            # Look for data types
            data_types = {
                "chart": "Charts",
                "graph": "Charts",
                "table": "Tables",
                "report": "Reports",
                "analytics": "Analytics"
            }
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in data_types:
                    return data_types[keyword_lower]
        
        return None
    
    def _fallback_classification(self, ocr_text: str, vision_desc: str) -> ClassificationResult:
        """Enhanced rule-based classification using OCR and vision."""
        text = (ocr_text + " " + vision_desc).lower()
        
        category = "OTHER"
        keywords = []
        confidence = 0.5
        
        # Extract meaningful keywords from text
        import re
        words = re.findall(r'\b[a-z]{3,}\b', text)
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'been', 'will', 'are', 'was', 'were'}
        keywords = [w.title() for w in words if w not in common_words][:10]
        
        # Enhanced keyword-based detection
        # Error detection (highest priority)
        if any(word in text for word in ['error', 'exception', 'failed', 'failure', 'timeout', '404', '500', '503', 'traceback', 'stack trace', 'fatal', 'crash']):
            category = "ERROR"
            confidence = 0.8
        
        # Code/Programming detection
        elif any(word in text for word in ['def ', 'function', 'import', 'class ', 'async', 'const ', 'var ', 'let ', 'return', 'python', 'javascript', 'java', 'c++', 'c#', 'html', 'css', 'sql', 'api', 'variable', 'typescript', 'react', 'node', 'npm', 'git', 'github']):
            category = "CODE"
            confidence = 0.75
        
        # AI/ML detection (new category mapped to CODE)
        elif any(word in text for word in ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 'chatgpt', 'openai', 'copilot', 'llm', 'gpt', 'claude', 'gemini', 'ai model']):
            category = "CODE"
            keywords.insert(0, "AI")
            confidence = 0.75
        
        # UI detection
        elif any(word in text for word in ['button', 'login', 'signup', 'sign up', 'sign in', 'dashboard', 'menu', 'form', 'input', 'click', 'interface', 'ui', 'ux', 'design', 'mockup']):
            category = "UI"
            confidence = 0.7
        
        # Documentation detection
        elif any(word in text for word in ['documentation', 'readme', 'guide', 'tutorial', 'docs', 'api reference', 'manual', 'instructions', 'how to']):
            category = "DOCUMENTATION"
            confidence = 0.7
        
        # Data/Finance detection
        elif any(word in text for word in ['chart', 'graph', 'table', 'data', 'report', 'analytics', 'statistics', 'stock', 'portfolio', 'investment', 'nifty', 'sensex', 'mutual fund', 'ipo', 'finance', 'invoice', 'bill', 'payment']):
            category = "DATA"
            confidence = 0.7
        
        # Communication detection
        elif any(word in text for word in ['slack', 'email', 'gmail', 'outlook', 'message', 'chat', 'whatsapp', 'telegram', 'conversation', 'reply', 'meeting', 'zoom', 'teams']):
            category = "COMMUNICATION"
            confidence = 0.7
        
        folder = self._suggest_folder(category, keywords)
        
        return ClassificationResult(
            category=category,
            keywords=keywords[:5],
            suggested_folder=folder,
            confidence=confidence,
            tags=keywords[:5]
        )
