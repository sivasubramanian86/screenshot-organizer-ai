"""Example usage of MonitorAgent for screenshot monitoring."""
from pathlib import Path
from src.agents.monitor_agent import MonitorAgent
from src.utils.platform_utils import get_screenshot_folder, get_os_type
from loguru import logger


def process_screenshot(file_path: Path) -> None:
    """Callback function to process detected screenshots."""
    logger.info(f"📸 New screenshot detected: {file_path.name}")
    logger.info(f"   Size: {file_path.stat().st_size} bytes")
    logger.info(f"   Path: {file_path}")


def main():
    """Main example demonstrating monitor usage."""
    
    # Auto-detect screenshot folder
    os_type = get_os_type()
    screenshot_folder = get_screenshot_folder(os_type)
    logger.info(f"OS: {os_type}")
    logger.info(f"Screenshot folder: {screenshot_folder}")
    
    # Monitor custom folder
    custom_folder = Path("./test_screenshots")
    custom_folder.mkdir(exist_ok=True)
    
    monitor = MonitorAgent(
        folder_path=custom_folder,
        completion_wait=1.0
    )
    
    logger.info(f"Monitoring: {custom_folder}")
    logger.info("Drop screenshots into the folder to test...")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        monitor.run(callback=process_screenshot)
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")


def example_error_handling():
    """Example demonstrating error handling."""
    
    # Non-existent folder
    try:
        monitor = MonitorAgent(Path("/nonexistent/folder"))
        monitor.start()
    except FileNotFoundError as e:
        logger.error(f"Expected error: {e}")
    
    # Validate before starting
    folder = Path("./test_screenshots")
    folder.mkdir(exist_ok=True)
    
    monitor = MonitorAgent(folder)
    try:
        monitor.validate_folder()
        logger.info("✅ Folder validation passed")
        monitor.start()
        logger.info("✅ Monitor started successfully")
        monitor.stop()
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")


if __name__ == "__main__":
    logger.add("logs/monitor_example.log", rotation="10 MB")
    logger.info("🚀 Starting Monitor Agent Examples\n")
    main()
