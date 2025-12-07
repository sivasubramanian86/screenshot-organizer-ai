"""Tests for Search engine."""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from src.utils.search_engine import SearchEngine
from src.agents.indexer_agent import IndexerAgent
from src.schemas.models import (
    ScreenshotMetadata,
    ProcessingResult,
    ClassificationResult,
    VisionAnalysis
)
from PIL import Image


@pytest.fixture
def search_engine(tmp_path):
    """Create search engine."""
    db_path = tmp_path / "test.db"
    
    # Initialize database
    indexer = IndexerAgent(db_path)
    
    # Add test data
    for i in range(5):
        img = Image.new('RGB', (100, 100), color='red')
        image_path = tmp_path / f"test_{i}.png"
        img.save(image_path)
        
        metadata = ScreenshotMetadata(
            file_path=image_path,
            original_filename=f"test_{i}.png",
            file_size_bytes=1024,
            width=100,
            height=100,
            format="PNG",
            created_timestamp=datetime.now() - timedelta(days=i),
            modified_timestamp=datetime.now(),
            file_hash=f"hash{i}"
        )
        
        vision = VisionAnalysis(
            description=f"Test screenshot {i}",
            content_type="ui",
            objects_detected=["button"],
            keywords=[f"keyword{i}", "test"],
            has_text=True,
            confidence=0.8 + (i * 0.02)
        )
        
        processing_result = ProcessingResult(
            metadata=metadata,
            ocr_text=f"Error database timeout {i}" if i < 2 else f"UI dashboard {i}",
            vision_analysis=vision
        )
        
        classification = ClassificationResult(
            category="ERROR" if i < 2 else "UI",
            keywords=[f"keyword{i}", "test"],
            suggested_folder=f"2025-12/{'ERROR' if i < 2 else 'UI'}",
            confidence=0.9,
            tags=["test"]
        )
        
        indexer.index_screenshot(
            image_path,
            processing_result,
            classification,
            f"new_{i}.png",
            tmp_path / f"new_{i}.png"
        )
    
    return SearchEngine(db_path)


class TestSearchEngine:
    """Test SearchEngine class."""
    
    def test_init(self, tmp_path):
        """Test initialization."""
        db_path = tmp_path / "test.db"
        engine = SearchEngine(db_path)
        assert engine.db_path == db_path
    
    def test_search_all(self, search_engine):
        """Test searching all screenshots."""
        results = search_engine.search()
        assert len(results) == 5
    
    def test_search_by_query(self, search_engine):
        """Test text search."""
        results = search_engine.search(query="database")
        assert len(results) >= 1
    
    def test_search_by_category(self, search_engine):
        """Test category filter."""
        results = search_engine.search(category="ERROR")
        assert len(results) == 2
        assert all(r['category'] == "ERROR" for r in results)
    
    def test_search_by_date_range(self, search_engine):
        """Test date range filter."""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        results = search_engine.search(
            date_from=yesterday,
            date_to=today
        )
        assert len(results) >= 1
    
    def test_search_with_limit(self, search_engine):
        """Test result limit."""
        results = search_engine.search(limit=2)
        assert len(results) == 2
    
    def test_full_text_search(self, search_engine):
        """Test full-text search."""
        results = search_engine.full_text_search("database")
        assert len(results) >= 1
    
    def test_filter_by_category(self, search_engine):
        """Test category filtering."""
        results = search_engine.filter_by_category("UI")
        assert len(results) == 3
    
    def test_filter_by_date_range(self, search_engine):
        """Test date range filtering."""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        results = search_engine.filter_by_date_range(week_ago, today)
        assert len(results) >= 1
    
    def test_advanced_search_category(self, search_engine):
        """Test advanced search with category."""
        results = search_engine.advanced_search("category:ERROR")
        assert len(results) == 2
    
    def test_advanced_search_tag(self, search_engine):
        """Test advanced search with tag."""
        results = search_engine.advanced_search("tag:test")
        assert len(results) >= 1
    
    def test_get_suggestions(self, search_engine):
        """Test search suggestions."""
        suggestions = search_engine.get_suggestions("key")
        assert len(suggestions) >= 1
        assert all(s.startswith("key") for s in suggestions)
    
    def test_get_stats(self, search_engine):
        """Test statistics."""
        stats = search_engine.get_stats()
        
        assert 'total_screenshots' in stats
        assert stats['total_screenshots'] == 5
        assert 'by_category' in stats
        assert 'ERROR' in stats['by_category']
        assert 'UI' in stats['by_category']
    
    def test_get_recent(self, search_engine):
        """Test getting recent screenshots."""
        results = search_engine.get_recent(limit=3)
        assert len(results) == 3
    
    def test_get_by_id(self, search_engine):
        """Test getting screenshot by ID."""
        result = search_engine.get_by_id(1)
        assert result is not None
        assert result['id'] == 1
    
    def test_get_by_id_not_found(self, search_engine):
        """Test getting non-existent screenshot."""
        result = search_engine.get_by_id(9999)
        assert result is None


class TestSearchIntegration:
    """Integration tests for search."""
    
    def test_search_workflow(self, search_engine):
        """Test complete search workflow."""
        # Search by text
        results = search_engine.full_text_search("database")
        assert len(results) >= 1
        
        # Get first result ID
        screenshot_id = results[0]['id']
        
        # Get by ID
        screenshot = search_engine.get_by_id(screenshot_id)
        assert screenshot is not None
        assert screenshot['id'] == screenshot_id
    
    def test_combined_filters(self, search_engine):
        """Test combining multiple filters."""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        results = search_engine.search(
            query="test",
            category="ERROR",
            date_from=week_ago,
            date_to=today,
            min_confidence=0.5
        )
        
        assert all(r['category'] == "ERROR" for r in results)
        assert all(r['confidence'] >= 0.5 for r in results)
