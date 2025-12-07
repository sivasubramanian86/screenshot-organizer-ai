"""Example usage of Classifier agent."""
from pathlib import Path
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from src.agents.classifier_agent import ClassifierAgent
from loguru import logger


def example_error_classification():
    """Example: Classify error screenshot."""
    logger.info("=== Error Classification Example ===")
    
    classifier = ClassifierAgent(api_key="test-key")
    
    ocr_text = """
    DatabaseConnectionTimeout: Could not connect to database
    at Connection.connect (database.js:45)
    Error: ETIMEDOUT - Connection timed out after 30000ms
    Retry attempt 3 of 3 failed
    """
    
    vision_desc = "Terminal window showing red error message with stack trace"
    
    try:
        result = classifier.classify(ocr_text, vision_description=vision_desc)
        
        logger.info(f"Category: {result.category}")
        logger.info(f"Keywords: {', '.join(result.keywords)}")
        logger.info(f"Confidence: {result.confidence:.1%}")
        logger.info(f"Suggested Folder: {result.suggested_folder}")
        logger.info(f"Tags: {', '.join(result.tags)}")
    except Exception as e:
        logger.error(f"Classification failed: {e}")


def example_code_classification():
    """Example: Classify code screenshot."""
    logger.info("\n=== Code Classification Example ===")
    
    classifier = ClassifierAgent(api_key="test-key")
    
    ocr_text = """
    async def fetch_user_data(user_id: int) -> dict:
        '''Fetch user data from API with retry logic.'''
        @retry(max_attempts=3)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'/api/users/{user_id}') as response:
                return await response.json()
    """
    
    vision_desc = "Code editor showing Python async function with decorators"
    
    try:
        result = classifier.classify(ocr_text, vision_description=vision_desc)
        
        logger.info(f"Category: {result.category}")
        logger.info(f"Keywords: {', '.join(result.keywords)}")
        logger.info(f"Confidence: {result.confidence:.1%}")
        logger.info(f"Suggested Folder: {result.suggested_folder}")
    except Exception as e:
        logger.error(f"Classification failed: {e}")


def example_ui_classification():
    """Example: Classify UI screenshot."""
    logger.info("\n=== UI Classification Example ===")
    
    classifier = ClassifierAgent(api_key="test-key")
    
    ocr_text = "Dashboard | Analytics | Export | Settings | User Profile"
    vision_desc = "Web dashboard with charts, graphs, and export button"
    
    try:
        result = classifier.classify(ocr_text, vision_description=vision_desc)
        
        logger.info(f"Category: {result.category}")
        logger.info(f"Keywords: {', '.join(result.keywords)}")
        logger.info(f"Confidence: {result.confidence:.1%}")
        logger.info(f"Suggested Folder: {result.suggested_folder}")
    except Exception as e:
        logger.error(f"Classification failed: {e}")


def example_full_pipeline():
    """Example: Complete OCR + Vision + Classification pipeline."""
    logger.info("\n=== Full Pipeline Example ===")
    
    # Initialize all agents
    ocr = OCRAgent()
    
    try:
        vision = VisionAgent()
        classifier = ClassifierAgent()
    except ValueError as e:
        logger.error(f"Agent initialization failed: {e}")
        return
    
    image_path = Path("test_screenshots/sample.png")
    
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return
    
    try:
        # Step 1: Extract text
        logger.info("Step 1: Extracting text with OCR...")
        ocr_text = ocr.extract_text(image_path)
        logger.info(f"  Found {len(ocr_text)} characters")
        
        # Step 2: Analyze image
        logger.info("Step 2: Analyzing with Claude Vision...")
        vision_analysis = vision.analyze_image(image_path, ocr_text=ocr_text)
        logger.info(f"  Type: {vision_analysis.content_type}")
        
        # Step 3: Classify
        logger.info("Step 3: Classifying screenshot...")
        classification = classifier.classify(ocr_text, vision_analysis=vision_analysis)
        
        # Display results
        logger.info("\n📊 Final Results:")
        logger.info(f"  Category: {classification.category}")
        logger.info(f"  Keywords: {', '.join(classification.keywords[:5])}")
        logger.info(f"  Confidence: {classification.confidence:.1%}")
        logger.info(f"  Folder: {classification.suggested_folder}")
        logger.info(f"  Tags: {', '.join(classification.tags)}")
        
        if classification.confidence < 0.6:
            logger.warning("⚠️  Low confidence - may need manual review")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")


def example_confidence_levels():
    """Example: Different confidence levels."""
    logger.info("\n=== Confidence Level Examples ===")
    
    classifier = ClassifierAgent(api_key="test-key")
    
    examples = [
        {
            "name": "High Confidence (0.9+)",
            "ocr": "TypeError: Cannot read property 'id' of null at line 42",
            "vision": "Clear error message with stack trace"
        },
        {
            "name": "Medium Confidence (0.6-0.9)",
            "ocr": "function getData() { return fetch('/api/data'); }",
            "vision": "Code snippet, possibly from documentation"
        },
        {
            "name": "Low Confidence (<0.6)",
            "ocr": "Click here to continue",
            "vision": "Generic button on webpage"
        }
    ]
    
    for example in examples:
        logger.info(f"\n{example['name']}:")
        try:
            result = classifier.classify(example["ocr"], vision_description=example["vision"])
            logger.info(f"  Category: {result.category}")
            logger.info(f"  Confidence: {result.confidence:.1%}")
            
            if result.confidence < 0.6:
                logger.warning("  ⚠️  Needs manual review")
        except Exception as e:
            logger.error(f"  Failed: {e}")


def example_edge_cases():
    """Example: Edge case handling."""
    logger.info("\n=== Edge Case Examples ===")
    
    classifier = ClassifierAgent(api_key="test-key")
    
    # Mixed content
    logger.info("1. Mixed Content (Code + Documentation):")
    mixed_text = """
    # API Documentation
    
    ## Authentication
    Use Bearer token in header:
    
    ```python
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get('/api/users', headers=headers)
    ```
    """
    
    try:
        result = classifier.classify(mixed_text, vision_description="Documentation with code examples")
        logger.info(f"  Category: {result.category}")
        logger.info(f"  Confidence: {result.confidence:.1%}")
    except Exception as e:
        logger.error(f"  Failed: {e}")
    
    # Empty/minimal content
    logger.info("\n2. Minimal Content:")
    try:
        result = classifier.classify("", vision_description="Blank screen")
        logger.info(f"  Category: {result.category}")
        logger.info(f"  Confidence: {result.confidence:.1%}")
    except Exception as e:
        logger.error(f"  Failed: {e}")


if __name__ == "__main__":
    logger.add("logs/classifier_example.log", rotation="10 MB")
    logger.info("🚀 Classifier Agent Examples\n")
    
    # Run examples (uncomment the ones you want)
    # example_error_classification()
    # example_code_classification()
    # example_ui_classification()
    example_full_pipeline()
    # example_confidence_levels()
    # example_edge_cases()
