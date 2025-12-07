"""Example usage of Naming and Organizer agents."""
from pathlib import Path
from datetime import datetime
from src.agents.naming_agent import NamingAgent
from src.agents.organizer_agent import OrganizerAgent
from src.schemas.models import ClassificationResult
from loguru import logger


def example_naming():
    """Example: Generate intelligent filenames."""
    logger.info("=== Naming Agent Example ===")
    
    namer = NamingAgent()
    
    # Example 1: Error screenshot
    filename = namer.generate_filename(
        category="ERROR",
        keywords=["database", "timeout", "connection", "failed"],
        file_path=Path("test.png"),
        created_date=datetime(2025, 12, 7)
    )
    logger.info(f"Error filename: {filename}")
    # Output: 2025-12-07_Error-DB_Database_Timeout_Connection_a3f2.png
    
    # Example 2: Code screenshot
    filename = namer.generate_filename(
        category="CODE",
        keywords=["python", "async", "await", "decorator"],
        file_path=Path("test.png"),
        created_date=datetime(2025, 12, 7)
    )
    logger.info(f"Code filename: {filename}")
    # Output: 2025-12-07_Code-Python_Python_Async_Await_a3f2.png
    
    # Example 3: UI screenshot
    filename = namer.generate_filename(
        category="UI",
        keywords=["dashboard", "analytics", "export"],
        file_path=Path("test.png"),
        created_date=datetime(2025, 12, 7)
    )
    logger.info(f"UI filename: {filename}")
    # Output: 2025-12-07_UI-Dashboard_Dashboard_Analytics_Export_a3f2.png


def example_organization():
    """Example: Organize screenshots into folders."""
    logger.info("\n=== Organization Example ===")
    
    # Setup
    base_folder = Path("./organized_screenshots")
    db_path = Path("data/screenshots.db")
    
    organizer = OrganizerAgent(
        base_folder=base_folder,
        db_path=db_path,
        dry_run=True  # Test mode
    )
    
    # Create classification
    classification = ClassificationResult(
        category="ERROR",
        keywords=["database", "timeout", "connection"],
        suggested_folder="2025-12/ERROR/Database",
        confidence=0.92,
        tags=["database", "timeout"]
    )
    
    # Organize file
    source = Path("test_screenshots/sample.png")
    
    if not source.exists():
        logger.warning(f"File not found: {source}")
        return
    
    result = organizer.organize(
        source_path=source,
        classification=classification,
        created_date=datetime(2025, 12, 7)
    )
    
    if result.success:
        logger.info(f"✅ Organization successful")
        logger.info(f"  Original: {result.original_filename}")
        logger.info(f"  New name: {result.new_filename}")
        logger.info(f"  Destination: {result.destination_path}")
    else:
        logger.error(f"❌ Organization failed: {result.error_message}")


def example_folder_structure():
    """Example: Show folder structure generation."""
    logger.info("\n=== Folder Structure Example ===")
    
    base_folder = Path("./organized_screenshots")
    db_path = Path("data/screenshots.db")
    
    organizer = OrganizerAgent(base_folder, db_path, dry_run=True)
    
    # Different categories
    examples = [
        ("ERROR", ["database", "timeout"], "Database errors"),
        ("ERROR", ["404", "not_found"], "HTTP errors"),
        ("CODE", ["python", "async"], "Python code"),
        ("CODE", ["javascript", "react"], "JavaScript code"),
        ("UI", ["dashboard", "analytics"], "Dashboard UI"),
        ("DATA", ["chart", "report"], "Data charts"),
    ]
    
    for category, keywords, description in examples:
        folder = organizer.get_target_folder(
            category=category,
            keywords=keywords,
            date=datetime(2025, 12, 7)
        )
        logger.info(f"{description:20} → {folder}")


def example_duplicate_handling():
    """Example: Handle duplicate filenames."""
    logger.info("\n=== Duplicate Handling Example ===")
    
    namer = NamingAgent()
    target_dir = Path("./test_duplicates")
    target_dir.mkdir(exist_ok=True)
    
    # Create existing file
    existing = target_dir / "2025-12-07_Error-DB_Database_Timeout_a3f2.png"
    existing.touch()
    
    # Try to use same filename
    filename = "2025-12-07_Error-DB_Database_Timeout_a3f2.png"
    new_filename = namer.handle_duplicate(filename, target_dir)
    
    logger.info(f"Original: {filename}")
    logger.info(f"Resolved: {new_filename}")
    # Output: 2025-12-07_Error-DB_Database_Timeout_a3f2(1).png
    
    # Cleanup
    existing.unlink()
    target_dir.rmdir()


def example_rollback():
    """Example: Rollback file moves."""
    logger.info("\n=== Rollback Example ===")
    
    base_folder = Path("./organized_screenshots")
    db_path = Path("data/screenshots.db")
    
    organizer = OrganizerAgent(base_folder, db_path)
    
    # Rollback moves from last 24 hours
    count = organizer.rollback(hours=24)
    
    if count > 0:
        logger.info(f"✅ Rolled back {count} file(s)")
    else:
        logger.info("No recent moves to rollback")


def example_full_pipeline():
    """Example: Complete organization pipeline."""
    logger.info("\n=== Full Pipeline Example ===")
    
    from src.agents.ocr_agent import OCRAgent
    from src.agents.vision_agent import VisionAgent
    from src.agents.classifier_agent import ClassifierAgent
    
    # Initialize all agents
    ocr = OCRAgent()
    
    try:
        vision = VisionAgent()
        classifier = ClassifierAgent()
    except ValueError as e:
        logger.error(f"Agent initialization failed: {e}")
        return
    
    organizer = OrganizerAgent(
        base_folder=Path("./organized_screenshots"),
        db_path=Path("data/screenshots.db"),
        dry_run=True
    )
    
    # Process screenshot
    image_path = Path("test_screenshots/sample.png")
    
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return
    
    try:
        # Step 1: OCR
        logger.info("Step 1: Extracting text...")
        ocr_text = ocr.extract_text(image_path)
        
        # Step 2: Vision
        logger.info("Step 2: Analyzing image...")
        vision_analysis = vision.analyze_image(image_path, ocr_text=ocr_text)
        
        # Step 3: Classify
        logger.info("Step 3: Classifying...")
        classification = classifier.classify(ocr_text, vision_analysis=vision_analysis)
        
        # Step 4: Organize
        logger.info("Step 4: Organizing...")
        result = organizer.organize(image_path, classification)
        
        # Display results
        logger.info("\n📊 Pipeline Results:")
        logger.info(f"  Category: {classification.category}")
        logger.info(f"  Keywords: {', '.join(classification.keywords[:3])}")
        logger.info(f"  Confidence: {classification.confidence:.1%}")
        logger.info(f"  New filename: {result.new_filename}")
        logger.info(f"  Destination: {result.destination_path}")
        
        if result.success:
            logger.info("✅ Organization successful")
        else:
            logger.error(f"❌ Organization failed: {result.error_message}")
    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")


if __name__ == "__main__":
    logger.add("logs/organizer_example.log", rotation="10 MB")
    logger.info("🚀 Naming & Organizer Agent Examples\n")
    
    # Run examples (uncomment the ones you want)
    example_naming()
    # example_organization()
    # example_folder_structure()
    # example_duplicate_handling()
    # example_rollback()
    # example_full_pipeline()
