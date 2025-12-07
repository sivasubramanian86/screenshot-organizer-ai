"""Example usage of OCR and Vision agents."""
from pathlib import Path
from src.agents.ocr_agent import OCRAgent
from src.agents.vision_agent import VisionAgent
from loguru import logger


def example_ocr():
    """Example: Extract text from screenshot."""
    logger.info("=== OCR Example ===")
    
    # Initialize OCR agent
    ocr = OCRAgent()
    
    # Extract text from image
    image_path = Path("test_screenshots/sample.png")
    
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        logger.info("Create a test image first!")
        return
    
    try:
        text = ocr.extract_text(image_path)
        logger.info(f"Extracted text ({len(text)} chars):")
        logger.info(f"{text[:200]}...")
        
        # Second call uses cache
        text2 = ocr.extract_text(image_path)
        logger.info("✅ Second call used cache")
        
    except Exception as e:
        logger.error(f"OCR failed: {e}")


def example_vision():
    """Example: Analyze screenshot with Claude Vision."""
    logger.info("\n=== Vision Example ===")
    
    # Initialize Vision agent
    try:
        vision = VisionAgent()
    except ValueError as e:
        logger.error(f"Vision agent initialization failed: {e}")
        logger.info("Set ANTHROPIC_API_KEY environment variable")
        return
    
    # Analyze image
    image_path = Path("test_screenshots/sample.png")
    
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return
    
    try:
        analysis = vision.analyze_image(image_path)
        
        logger.info(f"Description: {analysis.description}")
        logger.info(f"Content Type: {analysis.content_type}")
        logger.info(f"Keywords: {', '.join(analysis.keywords)}")
        logger.info(f"Objects: {', '.join(analysis.objects_detected)}")
        logger.info(f"Has Text: {analysis.has_text}")
        logger.info(f"Confidence: {analysis.confidence:.2f}")
        
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")


def example_combined():
    """Example: Combine OCR and Vision analysis."""
    logger.info("\n=== Combined OCR + Vision Example ===")
    
    # Initialize agents
    ocr = OCRAgent()
    
    try:
        vision = VisionAgent()
    except ValueError as e:
        logger.error(f"Vision agent not available: {e}")
        return
    
    image_path = Path("test_screenshots/sample.png")
    
    if not image_path.exists():
        logger.warning(f"Image not found: {image_path}")
        return
    
    try:
        # Step 1: Extract text with OCR
        logger.info("Step 1: Extracting text with OCR...")
        ocr_text = ocr.extract_text(image_path)
        logger.info(f"OCR found {len(ocr_text)} characters")
        
        # Step 2: Analyze with Vision (including OCR text)
        logger.info("Step 2: Analyzing with Claude Vision...")
        analysis = vision.analyze_image(image_path, ocr_text=ocr_text)
        
        # Step 3: Display results
        logger.info("\n📊 Analysis Results:")
        logger.info(f"  Description: {analysis.description}")
        logger.info(f"  Type: {analysis.content_type}")
        logger.info(f"  Keywords: {', '.join(analysis.keywords[:5])}")
        logger.info(f"  Confidence: {analysis.confidence:.1%}")
        
        if ocr_text:
            logger.info(f"\n📝 OCR Text Preview:")
            logger.info(f"  {ocr_text[:150]}...")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")


def example_error_handling():
    """Example: Error handling scenarios."""
    logger.info("\n=== Error Handling Examples ===")
    
    # Example 1: Tesseract not installed
    logger.info("1. Testing Tesseract availability...")
    try:
        ocr = OCRAgent()
        logger.info("✅ Tesseract is installed")
    except RuntimeError as e:
        logger.error(f"❌ {e}")
    
    # Example 2: API key missing
    logger.info("\n2. Testing Claude API key...")
    try:
        vision = VisionAgent()
        logger.info("✅ Claude API key is configured")
    except ValueError as e:
        logger.error(f"❌ {e}")
    
    # Example 3: File not found
    logger.info("\n3. Testing file not found...")
    try:
        ocr = OCRAgent()
        ocr.extract_text(Path("/nonexistent/file.png"))
    except FileNotFoundError as e:
        logger.info(f"✅ Correctly caught: {e}")
    
    # Example 4: File too large
    logger.info("\n4. Testing file size limit...")
    logger.info("Files over 50MB will be rejected")


def example_batch_processing():
    """Example: Process multiple screenshots."""
    logger.info("\n=== Batch Processing Example ===")
    
    ocr = OCRAgent()
    
    try:
        vision = VisionAgent()
    except ValueError:
        logger.error("Vision agent not available")
        return
    
    # Find all screenshots
    screenshot_dir = Path("test_screenshots")
    if not screenshot_dir.exists():
        logger.warning("Create test_screenshots/ folder first")
        return
    
    images = list(screenshot_dir.glob("*.png"))
    logger.info(f"Found {len(images)} images")
    
    for i, image_path in enumerate(images, 1):
        logger.info(f"\n[{i}/{len(images)}] Processing: {image_path.name}")
        
        try:
            # OCR
            text = ocr.extract_text(image_path)
            
            # Vision
            analysis = vision.analyze_image(image_path, ocr_text=text)
            
            logger.info(f"  Type: {analysis.content_type}")
            logger.info(f"  Keywords: {', '.join(analysis.keywords[:3])}")
            
        except Exception as e:
            logger.error(f"  Failed: {e}")


if __name__ == "__main__":
    # Configure logger
    logger.add("logs/ocr_vision_example.log", rotation="10 MB")
    
    logger.info("🚀 OCR & Vision Agent Examples\n")
    
    # Run examples (uncomment the ones you want)
    example_ocr()
    # example_vision()
    # example_combined()
    # example_error_handling()
    # example_batch_processing()
