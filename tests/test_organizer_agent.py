"""Tests for Organizer agent."""
import pytest
from pathlib import Path
from datetime import datetime
from PIL import Image
from src.agents.organizer_agent import OrganizerAgent
from src.schemas.models import ClassificationResult


@pytest.fixture
def test_image(tmp_path):
    """Create a test image."""
    img = Image.new('RGB', (100, 100), color='blue')
    image_path = tmp_path / "source" / "test.png"
    image_path.parent.mkdir(exist_ok=True)
    img.save(image_path)
    return image_path


@pytest.fixture
def organizer(tmp_path):
    """Create organizer agent."""
    base_folder = tmp_path / "organized"
    db_path = tmp_path / "test.db"
    
    # Initialize database
    from src.utils.database import DatabaseManager
    db = DatabaseManager(db_path)
    db.connect()
    db.initialize_schema()
    db.close()
    
    return OrganizerAgent(base_folder, db_path, dry_run=False)


@pytest.fixture
def classification():
    """Create test classification result."""
    return ClassificationResult(
        category="ERROR",
        keywords=["database", "timeout", "connection"],
        suggested_folder="2025-12/ERROR/Database",
        confidence=0.9,
        tags=["database", "timeout"]
    )


class TestOrganizerAgent:
    """Test OrganizerAgent class."""
    
    def test_init(self, tmp_path):
        """Test initialization."""
        base_folder = tmp_path / "organized"
        db_path = tmp_path / "test.db"
        
        agent = OrganizerAgent(base_folder, db_path)
        assert agent.base_folder == base_folder
        assert agent.db_path == db_path
    
    def test_get_target_folder_error(self, organizer):
        """Test target folder for error category."""
        folder = organizer.get_target_folder(
            category="ERROR",
            keywords=["database", "timeout"],
            date=datetime(2025, 12, 7)
        )
        
        assert "2025-12" in str(folder)
        assert "Error" in str(folder)
        assert "Database" in str(folder) or "Network" in str(folder)
    
    def test_get_target_folder_code(self, organizer):
        """Test target folder for code category."""
        folder = organizer.get_target_folder(
            category="CODE",
            keywords=["python", "async"],
            date=datetime(2025, 12, 7)
        )
        
        assert "2025-12" in str(folder)
        assert "Code" in str(folder)
        assert "Python" in str(folder)
    
    def test_get_target_folder_ui(self, organizer):
        """Test target folder for UI category."""
        folder = organizer.get_target_folder(
            category="UI",
            keywords=["dashboard", "analytics"],
            date=datetime(2025, 12, 7)
        )
        
        assert "2025-12" in str(folder)
        assert "Ui" in str(folder)
        assert "Dashboard" in str(folder)
    
    def test_organize_success(self, organizer, test_image, classification):
        """Test successful organization."""
        result = organizer.organize(
            source_path=test_image,
            classification=classification,
            created_date=datetime(2025, 12, 7)
        )
        
        assert result.success
        assert result.original_filename == "test.png"
        assert len(result.new_filename) > 0
        assert result.destination_path.exists()
    
    def test_organize_file_not_found(self, organizer, tmp_path, classification):
        """Test organization with non-existent file."""
        fake_path = tmp_path / "nonexistent.png"
        
        result = organizer.organize(
            source_path=fake_path,
            classification=classification
        )
        
        assert not result.success
        assert "not found" in result.error_message.lower()
    
    def test_organize_dry_run(self, tmp_path, test_image, classification):
        """Test dry run mode."""
        base_folder = tmp_path / "organized"
        db_path = tmp_path / "test.db"
        
        # Initialize database
        from src.utils.database import DatabaseManager
        db = DatabaseManager(db_path)
        db.connect()
        db.initialize_schema()
        db.close()
        
        organizer = OrganizerAgent(base_folder, db_path, dry_run=True)
        
        result = organizer.organize(
            source_path=test_image,
            classification=classification
        )
        
        assert result.success
        assert test_image.exists()  # Original still exists
        assert not result.destination_path.exists()  # Not actually moved
    
    def test_subcategory_error_database(self, organizer):
        """Test subcategory detection for database errors."""
        subcat = organizer._get_subcategory("ERROR", ["database", "connection"])
        assert subcat == "Database"
    
    def test_subcategory_error_network(self, organizer):
        """Test subcategory detection for network errors."""
        subcat = organizer._get_subcategory("ERROR", ["timeout", "network"])
        assert subcat == "Network"
    
    def test_subcategory_code_python(self, organizer):
        """Test subcategory detection for Python code."""
        subcat = organizer._get_subcategory("CODE", ["python", "async"])
        assert subcat == "Python"
    
    def test_subcategory_ui_dashboard(self, organizer):
        """Test subcategory detection for UI dashboard."""
        subcat = organizer._get_subcategory("UI", ["dashboard", "analytics"])
        assert subcat == "Dashboard"
    
    def test_subcategory_none(self, organizer):
        """Test subcategory when no match found."""
        subcat = organizer._get_subcategory("OTHER", ["random", "stuff"])
        assert subcat is None


class TestOrganizerRollback:
    """Test rollback functionality."""
    
    def test_rollback_recent_moves(self, organizer, test_image, classification):
        """Test rolling back recent file moves."""
        # Organize file
        result = organizer.organize(
            source_path=test_image,
            classification=classification
        )
        
        assert result.success
        assert result.destination_path.exists()
        assert not test_image.exists()
        
        # Rollback
        count = organizer.rollback(hours=24)
        
        assert count > 0
        assert test_image.exists()  # File restored
        assert not result.destination_path.exists()  # Moved back
    
    def test_rollback_no_recent_moves(self, organizer):
        """Test rollback with no recent moves."""
        count = organizer.rollback(hours=24)
        assert count == 0


class TestOrganizerIntegration:
    """Integration tests for organizer."""
    
    def test_full_organization_pipeline(self, organizer, tmp_path):
        """Test complete organization pipeline."""
        # Create multiple test images
        images = []
        for i in range(3):
            img = Image.new('RGB', (100, 100), color='red')
            image_path = tmp_path / "source" / f"test_{i}.png"
            image_path.parent.mkdir(exist_ok=True)
            img.save(image_path)
            images.append(image_path)
        
        # Different classifications
        classifications = [
            ClassificationResult(
                category="ERROR",
                keywords=["database", "timeout"],
                suggested_folder="2025-12/ERROR/Database",
                confidence=0.9,
                tags=["database"]
            ),
            ClassificationResult(
                category="CODE",
                keywords=["python", "async"],
                suggested_folder="2025-12/CODE/Python",
                confidence=0.85,
                tags=["python"]
            ),
            ClassificationResult(
                category="UI",
                keywords=["dashboard"],
                suggested_folder="2025-12/UI/Dashboard",
                confidence=0.8,
                tags=["dashboard"]
            )
        ]
        
        # Organize all
        results = []
        for image, classification in zip(images, classifications):
            result = organizer.organize(image, classification)
            results.append(result)
        
        # Verify all succeeded
        assert all(r.success for r in results)
        
        # Verify folder structure created
        base = organizer.base_folder
        assert (base / "2025-12" / "Error").exists()
        assert (base / "2025-12" / "Code").exists()
        assert (base / "2025-12" / "Ui").exists()
    
    def test_duplicate_handling(self, organizer, tmp_path, classification):
        """Test handling of duplicate filenames."""
        # Create two identical images
        img = Image.new('RGB', (100, 100), color='green')
        
        image1 = tmp_path / "source" / "test1.png"
        image1.parent.mkdir(exist_ok=True)
        img.save(image1)
        
        image2 = tmp_path / "source" / "test2.png"
        img.save(image2)
        
        # Organize both (might generate same filename)
        result1 = organizer.organize(image1, classification)
        result2 = organizer.organize(image2, classification)
        
        assert result1.success
        assert result2.success
        
        # Filenames should be different (duplicate handling)
        if result1.new_filename == result2.new_filename:
            # If same base name, one should have (1) appended
            assert "(1)" in result2.new_filename or result1.new_filename != result2.new_filename
