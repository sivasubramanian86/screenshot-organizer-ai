"""Tests for Indexer agent."""
import pytest
from pathlib import Path
from datetime import datetime
from PIL import Image
from src.agents.indexer_agent import IndexerAgent
from src.schemas.models import (
    ScreenshotMetadata,
    ProcessingResult,
    ClassificationResult,
    VisionAnalysis
)


@pytest.fixture
def test_image(tmp_path):
    """Create a test image."""
    img = Image.new('RGB', (200, 200), color='green')
    image_path = tmp_path / "test.png"
    img.save(image_path)
    return image_path


@pytest.fixture
def indexer(tmp_path):
    """Create indexer agent."""
    db_path = tmp_path / "test.db"
    return IndexerAgent(db_path)


@pytest.fixture
def processing_result(test_image):
    """Create test processing result."""
    metadata = ScreenshotMetadata(
        file_path=test_image,
        original_filename="test.png",
        file_size_bytes=1024,
        width=200,
        height=200,
        format="PNG",
        created_timestamp=datetime.now(),
        modified_timestamp=datetime.now(),
        file_hash="abc123"
    )
    
    vision = VisionAnalysis(
        description="Test screenshot",
        content_type="ui",
        objects_detected=["button"],
        keywords=["test"],
        has_text=True,
        confidence=0.9
    )
    
    return ProcessingResult(
        metadata=metadata,
        ocr_text="Test OCR text",
        vision_analysis=vision
    )


@pytest.fixture
def classification():
    """Create test classification."""
    return ClassificationResult(
        category="UI",
        keywords=["test", "screenshot", "ui"],
        suggested_folder="2025-12/UI",
        confidence=0.9,
        tags=["test"]
    )


class TestIndexerAgent:
    """Test IndexerAgent class."""
    
    def test_init(self, tmp_path):
        """Test initialization."""
        db_path = tmp_path / "test.db"
        indexer = IndexerAgent(db_path)
        assert indexer.db_path == db_path
        assert db_path.exists()
    
    def test_index_screenshot(
        self,
        indexer,
        test_image,
        processing_result,
        classification,
        tmp_path
    ):
        """Test indexing a screenshot."""
        new_path = tmp_path / "organized" / "test_new.png"
        new_path.parent.mkdir(exist_ok=True)
        
        screenshot_id = indexer.index_screenshot(
            file_path=test_image,
            processing_result=processing_result,
            classification=classification,
            new_filename="test_new.png",
            new_path=new_path
        )
        
        assert screenshot_id > 0
    
    def test_generate_thumbnail(self, indexer, test_image):
        """Test thumbnail generation."""
        thumbnail = indexer._generate_thumbnail(test_image)
        
        assert isinstance(thumbnail, bytes)
        assert len(thumbnail) > 0
    
    def test_generate_thumbnail_custom_size(self, indexer, test_image):
        """Test thumbnail with custom size."""
        thumbnail = indexer._generate_thumbnail(test_image, size=(100, 100))
        
        assert isinstance(thumbnail, bytes)
        assert len(thumbnail) > 0
    
    def test_rebuild_index(
        self,
        indexer,
        test_image,
        processing_result,
        classification,
        tmp_path
    ):
        """Test rebuilding search index."""
        # Index a screenshot first
        new_path = tmp_path / "test_new.png"
        indexer.index_screenshot(
            test_image,
            processing_result,
            classification,
            "test_new.png",
            new_path
        )
        
        # Rebuild index
        count = indexer.rebuild_index()
        
        assert count > 0
    
    def test_update_screenshot(
        self,
        indexer,
        test_image,
        processing_result,
        classification,
        tmp_path
    ):
        """Test updating screenshot metadata."""
        # Index first
        new_path = tmp_path / "test_new.png"
        screenshot_id = indexer.index_screenshot(
            test_image,
            processing_result,
            classification,
            "test_new.png",
            new_path
        )
        
        # Update
        success = indexer.update_screenshot(
            screenshot_id,
            category="CODE",
            keywords=["updated", "keywords"],
            tags=["new_tag"]
        )
        
        assert success


class TestIndexerIntegration:
    """Integration tests for indexer."""
    
    def test_multiple_screenshots(
        self,
        indexer,
        tmp_path,
        classification
    ):
        """Test indexing multiple screenshots."""
        # Create multiple test images
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='blue')
            image_path = tmp_path / f"test_{i}.png"
            img.save(image_path)
            
            metadata = ScreenshotMetadata(
                file_path=image_path,
                original_filename=f"test_{i}.png",
                file_size_bytes=1024,
                width=100,
                height=100,
                format="PNG",
                created_timestamp=datetime.now(),
                modified_timestamp=datetime.now(),
                file_hash=f"hash{i}"
            )
            
            vision = VisionAnalysis(
                description=f"Test {i}",
                content_type="ui",
                objects_detected=[],
                keywords=[f"test{i}"],
                has_text=False,
                confidence=0.8
            )
            
            processing_result = ProcessingResult(
                metadata=metadata,
                ocr_text=f"Text {i}",
                vision_analysis=vision
            )
            
            new_path = tmp_path / f"new_{i}.png"
            screenshot_id = indexer.index_screenshot(
                image_path,
                processing_result,
                classification,
                f"new_{i}.png",
                new_path
            )
            
            assert screenshot_id > 0
