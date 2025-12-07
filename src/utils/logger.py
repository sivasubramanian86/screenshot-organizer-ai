"""Logging setup with file rotation."""
import sys
from pathlib import Path
from loguru import logger


def setup_logging(
    log_file: Path,
    level: str = "INFO",
    max_size_mb: int = 10,
    backup_count: int = 5,
    console: bool = True
) -> None:
    """Setup logging with file rotation and console output."""
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    if console:
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level=level,
            colorize=True
        )
    
    # Add file handler with rotation
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=level,
        rotation=f"{max_size_mb} MB",
        retention=backup_count,
        compression="zip"
    )
    
    logger.info(f"Logging initialized: {log_file}")
