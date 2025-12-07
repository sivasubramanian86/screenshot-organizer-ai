"""Tests for Classifier agent."""
import pytest
from unittest.mock import Mock, patch
from src.agents.classifier_agent import ClassifierAgent
from src.schemas.models import ClassificationResult, VisionAnalysis


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response for classification."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = """{
        "category": "ERROR",
        "keywords": ["database", "connection", "timeout", "retry", "failed"],
        "confidence": 0.92,
        "reasoning": "Clear error message about database connection timeout"
    }"""
    return mock_response


class TestClassifierAgent:
    """Test ClassifierAgent class."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        agent = ClassifierAgent(api_key="test-key")
        assert agent.api_key == "test-key"
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                ClassifierAgent()
    
    @patch('anthropic.Anthropic')
    def test_classify_error_screenshot(self, mock_anthropic_class, mock_claude_response):
        """Test classification of error screenshot."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        ocr_text = "DatabaseConnectionTimeout: Could not connect to database after 30s"
        vision_desc = "Screenshot showing red error message on terminal"
        
        result = agent.classify(ocr_text, vision_description=vision_desc)
        
        assert isinstance(result, ClassificationResult)
        assert result.category == "ERROR"
        assert "database" in [k.lower() for k in result.keywords]
        assert result.confidence >= 0.9
        assert "Database" in result.suggested_folder or "Network" in result.suggested_folder
    
    @patch('anthropic.Anthropic')
    def test_classify_code_screenshot(self, mock_anthropic_class):
        """Test classification of code screenshot."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """{
            "category": "CODE",
            "keywords": ["python", "async", "await", "function", "decorator"],
            "confidence": 0.88,
            "reasoning": "Python code with async/await syntax"
        }"""
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        ocr_text = "async def fetch_data():\n    await asyncio.sleep(1)"
        result = agent.classify(ocr_text)
        
        assert result.category == "CODE"
        assert "python" in [k.lower() for k in result.keywords]
        assert "Python" in result.suggested_folder
    
    @patch('anthropic.Anthropic')
    def test_classify_ui_screenshot(self, mock_anthropic_class):
        """Test classification of UI screenshot."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """{
            "category": "UI",
            "keywords": ["dashboard", "analytics", "chart", "export", "button"],
            "confidence": 0.85,
            "reasoning": "Dashboard interface with analytics charts"
        }"""
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        vision_desc = "Dashboard with multiple charts and export button"
        result = agent.classify("", vision_description=vision_desc)
        
        assert result.category == "UI"
        assert "dashboard" in [k.lower() for k in result.keywords]
        assert "Dashboard" in result.suggested_folder
    
    @patch('anthropic.Anthropic')
    def test_classify_with_vision_analysis(self, mock_anthropic_class, mock_claude_response):
        """Test classification with VisionAnalysis object."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        vision = VisionAnalysis(
            description="Error message on red background",
            content_type="error",
            objects_detected=["text", "error_icon"],
            keywords=["error", "database"],
            has_text=True,
            confidence=0.9
        )
        
        result = agent.classify("Database error", vision_analysis=vision)
        
        assert isinstance(result, ClassificationResult)
        assert result.category == "ERROR"
    
    def test_parse_response_valid_json(self):
        """Test parsing valid JSON response."""
        agent = ClassifierAgent(api_key="test-key")
        
        content = """{
            "category": "CODE",
            "keywords": ["python", "test"],
            "confidence": 0.8
        }"""
        
        result = agent._parse_response(content)
        
        assert result["category"] == "CODE"
        assert result["keywords"] == ["python", "test"]
        assert result["confidence"] == 0.8
    
    def test_parse_response_invalid_category(self):
        """Test parsing with invalid category defaults to OTHER."""
        agent = ClassifierAgent(api_key="test-key")
        
        content = """{
            "category": "INVALID",
            "keywords": ["test"],
            "confidence": 0.5
        }"""
        
        result = agent._parse_response(content)
        assert result["category"] == "OTHER"
    
    def test_parse_response_confidence_clamping(self):
        """Test confidence is clamped to [0, 1]."""
        agent = ClassifierAgent(api_key="test-key")
        
        content = """{
            "category": "CODE",
            "keywords": ["test"],
            "confidence": 1.5
        }"""
        
        result = agent._parse_response(content)
        assert result["confidence"] == 1.0
    
    def test_suggest_folder_error_database(self):
        """Test folder suggestion for database error."""
        agent = ClassifierAgent(api_key="test-key")
        
        folder = agent._suggest_folder("ERROR", ["database", "connection", "timeout"])
        
        assert "ERROR" in folder
        assert "Database" in folder or "Network" in folder
    
    def test_suggest_folder_code_python(self):
        """Test folder suggestion for Python code."""
        agent = ClassifierAgent(api_key="test-key")
        
        folder = agent._suggest_folder("CODE", ["python", "async", "function"])
        
        assert "CODE" in folder
        assert "Python" in folder
    
    def test_suggest_folder_ui_dashboard(self):
        """Test folder suggestion for UI dashboard."""
        agent = ClassifierAgent(api_key="test-key")
        
        folder = agent._suggest_folder("UI", ["dashboard", "analytics"])
        
        assert "UI" in folder
        assert "Dashboard" in folder
    
    def test_suggest_folder_no_subcategory(self):
        """Test folder suggestion without subcategory."""
        agent = ClassifierAgent(api_key="test-key")
        
        folder = agent._suggest_folder("OTHER", ["random", "stuff"])
        
        assert "OTHER" in folder
        assert folder.count("/") == 1  # Only date/category
    
    def test_fallback_classification_error(self):
        """Test fallback classification for error text."""
        agent = ClassifierAgent(api_key="test-key")
        
        result = agent._fallback_classification(
            "Error: Connection timeout",
            "Red error message"
        )
        
        assert result.category == "ERROR"
        assert result.confidence < 0.6
    
    def test_fallback_classification_code(self):
        """Test fallback classification for code text."""
        agent = ClassifierAgent(api_key="test-key")
        
        result = agent._fallback_classification(
            "def function(): return True",
            "Code editor screenshot"
        )
        
        assert result.category == "CODE"
        assert result.confidence < 0.6
    
    @patch('anthropic.Anthropic')
    def test_classify_api_failure_uses_fallback(self, mock_anthropic_class):
        """Test that API failure triggers fallback classification."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        result = agent.classify("Error: timeout", vision_description="Error message")
        
        assert isinstance(result, ClassificationResult)
        assert result.category in ["ERROR", "OTHER"]
    
    def test_keyword_limit(self):
        """Test that keywords are limited to 10."""
        agent = ClassifierAgent(api_key="test-key")
        
        content = """{
            "category": "CODE",
            "keywords": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "k10", "k11", "k12"],
            "confidence": 0.8
        }"""
        
        result = agent._parse_response(content)
        assert len(result["keywords"]) <= 10


class TestClassifierIntegration:
    """Integration tests for classifier."""
    
    @patch('anthropic.Anthropic')
    def test_full_classification_pipeline(self, mock_anthropic_class):
        """Test complete classification pipeline."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = """{
            "category": "ERROR",
            "keywords": ["database", "timeout", "connection"],
            "confidence": 0.95,
            "reasoning": "Database connection error"
        }"""
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        agent = ClassifierAgent(api_key="test-key")
        agent.client = mock_client
        
        # Full pipeline
        ocr_text = "DatabaseConnectionTimeout: Failed to connect"
        vision = VisionAnalysis(
            description="Error message on terminal",
            content_type="error",
            objects_detected=["text"],
            keywords=["error"],
            has_text=True,
            confidence=0.9
        )
        
        result = agent.classify(ocr_text, vision_analysis=vision)
        
        assert result.category == "ERROR"
        assert len(result.keywords) > 0
        assert result.confidence > 0.9
        assert len(result.suggested_folder) > 0
        assert len(result.tags) > 0
