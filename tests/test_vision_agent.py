"""Tests for Vision agent."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from src.agents.vision_agent import VisionAgent
from src.schemas.models import VisionAnalysis


@pytest.fixture
def test_image(tmp_path):
    """Create a test image."""
    img = Image.new('RGB', (400, 300), color='red')
    image_path = tmp_path / "test_screenshot.png"
    img.save(image_path)
    return image_path


@pytest.fixture
def mock_anthropic_response():
    """Mock Claude API response."""
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = """{
        "description": "A red screenshot showing test content",
        "content_type": "ui",
        "objects_detected": ["button", "text", "image"],
        "keywords": ["test", "screenshot", "ui", "red"],
        "has_text": true,
        "confidence": 0.85
    }"""
    return mock_response


class TestVisionAgent:
    """Test VisionAgent class."""
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        agent = VisionAgent(api_key="test-key")
        assert agent.api_key == "test-key"
        assert agent.model == "claude-3-5-sonnet-20241022"
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                VisionAgent()
    
    def test_init_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env-key'}):
            agent = VisionAgent()
            assert agent.api_key == "env-key"
    
    def test_encode_image_png(self, test_image):
        """Test image encoding for PNG."""
        agent = VisionAgent(api_key="test-key")
        encoded, media_type = agent._encode_image(test_image)
        
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        assert media_type == "image/png"
    
    def test_encode_image_jpg(self, tmp_path):
        """Test image encoding for JPEG."""
        img = Image.new('RGB', (100, 100), color='blue')
        image_path = tmp_path / "test.jpg"
        img.save(image_path)
        
        agent = VisionAgent(api_key="test-key")
        encoded, media_type = agent._encode_image(image_path)
        
        assert media_type == "image/jpeg"
    
    @patch('anthropic.Anthropic')
    def test_analyze_image_success(self, mock_anthropic_class, test_image, mock_anthropic_response):
        """Test successful image analysis."""
        # Setup mock
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client
        
        # Test
        agent = VisionAgent(api_key="test-key")
        agent.client = mock_client
        
        result = agent.analyze_image(test_image)
        
        assert isinstance(result, VisionAnalysis)
        assert result.description == "A red screenshot showing test content"
        assert result.content_type == "ui"
        assert "test" in result.keywords
        assert result.confidence == 0.85
    
    @patch('anthropic.Anthropic')
    def test_analyze_image_with_ocr_text(self, mock_anthropic_class, test_image, mock_anthropic_response):
        """Test image analysis with OCR text."""
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key")
        agent.client = mock_client
        
        result = agent.analyze_image(test_image, ocr_text="Sample OCR text")
        
        assert isinstance(result, VisionAnalysis)
        # Verify OCR text was included in API call
        call_args = mock_client.messages.create.call_args
        assert "Sample OCR text" in str(call_args)
    
    def test_file_not_found(self):
        """Test error handling for non-existent file."""
        agent = VisionAgent(api_key="test-key")
        
        with pytest.raises(FileNotFoundError):
            agent.analyze_image(Path("/nonexistent/image.png"))
    
    def test_file_too_large(self, tmp_path):
        """Test error handling for large files."""
        agent = VisionAgent(api_key="test-key")
        
        # Create mock large file
        large_file = tmp_path / "large.png"
        with open(large_file, 'wb') as f:
            f.write(b'0' * (51 * 1024 * 1024))  # 51MB
        
        with pytest.raises(ValueError, match="too large"):
            agent.analyze_image(large_file)
    
    @patch('anthropic.Anthropic')
    def test_rate_limit_retry(self, mock_anthropic_class, test_image):
        """Test retry logic for rate limiting."""
        import anthropic
        
        mock_client = Mock()
        # First call raises rate limit, second succeeds
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"description": "test", "content_type": "other", "objects_detected": [], "keywords": [], "has_text": false, "confidence": 0.5}'
        
        mock_client.messages.create.side_effect = [
            anthropic.RateLimitError("Rate limited"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key", max_retries=2)
        agent.client = mock_client
        
        with patch('time.sleep'):  # Skip actual sleep
            result = agent.analyze_image(test_image)
        
        assert isinstance(result, VisionAnalysis)
        assert mock_client.messages.create.call_count == 2
    
    @patch('anthropic.Anthropic')
    def test_authentication_error(self, mock_anthropic_class, test_image):
        """Test handling of authentication errors."""
        import anthropic
        
        mock_client = Mock()
        mock_client.messages.create.side_effect = anthropic.AuthenticationError("Invalid API key")
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="invalid-key")
        agent.client = mock_client
        
        with pytest.raises(ValueError, match="Invalid Claude API key"):
            agent.analyze_image(test_image)
    
    @patch('anthropic.Anthropic')
    def test_timeout_retry(self, mock_anthropic_class, test_image):
        """Test retry logic for timeouts."""
        import anthropic
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"description": "test", "content_type": "other", "objects_detected": [], "keywords": [], "has_text": false, "confidence": 0.5}'
        
        mock_client.messages.create.side_effect = [
            anthropic.APITimeoutError("Timeout"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key", max_retries=2)
        agent.client = mock_client
        
        with patch('time.sleep'):
            result = agent.analyze_image(test_image)
        
        assert isinstance(result, VisionAnalysis)
    
    @patch('anthropic.Anthropic')
    def test_fallback_parsing(self, mock_anthropic_class, test_image):
        """Test fallback parsing when JSON not found in response."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a plain text response without JSON"
        
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key")
        agent.client = mock_client
        
        result = agent.analyze_image(test_image)
        
        assert isinstance(result, VisionAnalysis)
        assert result.content_type == "other"
        assert result.confidence == 0.5


class TestVisionIntegration:
    """Integration tests for Vision agent."""
    
    @patch('anthropic.Anthropic')
    def test_multiple_images(self, mock_anthropic_class, tmp_path):
        """Test processing multiple images."""
        # Create test images
        images = []
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='blue')
            image_path = tmp_path / f"test_{i}.png"
            img.save(image_path)
            images.append(image_path)
        
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"description": "test", "content_type": "ui", "objects_detected": [], "keywords": [], "has_text": false, "confidence": 0.8}'
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        agent = VisionAgent(api_key="test-key")
        agent.client = mock_client
        
        # Analyze all images
        results = [agent.analyze_image(img) for img in images]
        
        assert len(results) == 3
        assert all(isinstance(r, VisionAnalysis) for r in results)
