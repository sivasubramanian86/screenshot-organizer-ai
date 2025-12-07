"""Example usage of Indexer and Search engine."""
from pathlib import Path
from datetime import datetime, timedelta
from src.utils.search_engine import SearchEngine
from loguru import logger


def example_basic_search():
    """Example: Basic search operations."""
    logger.info("=== Basic Search Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Search all
    results = search.search()
    logger.info(f"Total screenshots: {len(results)}")
    
    # Search by text
    results = search.search(query="database")
    logger.info(f"Found {len(results)} screenshots with 'database'")
    
    # Search by category
    results = search.search(category="ERROR")
    logger.info(f"Found {len(results)} error screenshots")


def example_full_text_search():
    """Example: Full-text search."""
    logger.info("\n=== Full-Text Search Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Search OCR text and keywords
    results = search.full_text_search("database timeout")
    
    logger.info(f"Found {len(results)} results")
    for result in results[:3]:
        logger.info(f"  {result['current_filename']}")
        logger.info(f"    Category: {result['category']}")
        logger.info(f"    Confidence: {result['confidence']:.2f}")
        logger.info(f"    Keywords: {', '.join(result['keywords'][:3])}")


def example_advanced_search():
    """Example: Advanced search with filters."""
    logger.info("\n=== Advanced Search Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Example 1: Category filter
    results = search.advanced_search("category:ERROR")
    logger.info(f"Errors: {len(results)}")
    
    # Example 2: Date range
    results = search.advanced_search("date:2025-12-01..2025-12-07")
    logger.info(f"This week: {len(results)}")
    
    # Example 3: Tag search
    results = search.advanced_search("tag:important")
    logger.info(f"Important: {len(results)}")
    
    # Example 4: Combined
    results = search.advanced_search("database category:ERROR")
    logger.info(f"Database errors: {len(results)}")


def example_date_range():
    """Example: Search by date range."""
    logger.info("\n=== Date Range Search Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Last 7 days
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    results = search.filter_by_date_range(week_ago, today)
    logger.info(f"Last 7 days: {len(results)} screenshots")
    
    # Last 30 days
    month_ago = today - timedelta(days=30)
    results = search.filter_by_date_range(month_ago, today)
    logger.info(f"Last 30 days: {len(results)} screenshots")


def example_suggestions():
    """Example: Search suggestions."""
    logger.info("\n=== Search Suggestions Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Get suggestions
    queries = ["data", "err", "py"]
    
    for query in queries:
        suggestions = search.get_suggestions(query)
        logger.info(f"'{query}' → {', '.join(suggestions[:5])}")


def example_statistics():
    """Example: Database statistics."""
    logger.info("\n=== Statistics Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    stats = search.get_stats()
    
    logger.info(f"Total screenshots: {stats['total_screenshots']}")
    logger.info(f"Average confidence: {stats['average_confidence']:.2f}")
    
    logger.info("\nBy category:")
    for category, count in stats['by_category'].items():
        logger.info(f"  {category}: {count}")
    
    logger.info("\nRecent activity:")
    for date, count in list(stats['by_date'].items())[:7]:
        logger.info(f"  {date}: {count}")


def example_recent_screenshots():
    """Example: Get recent screenshots."""
    logger.info("\n=== Recent Screenshots Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    results = search.get_recent(limit=10)
    
    logger.info(f"Last 10 screenshots:")
    for result in results:
        logger.info(f"  {result['current_filename']}")
        logger.info(f"    Category: {result['category']}")
        logger.info(f"    Date: {result['processed_date']}")


def example_get_by_id():
    """Example: Get screenshot by ID."""
    logger.info("\n=== Get by ID Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Get first screenshot
    results = search.get_recent(limit=1)
    if results:
        screenshot_id = results[0]['id']
        
        # Get full details
        screenshot = search.get_by_id(screenshot_id)
        
        if screenshot:
            logger.info(f"Screenshot #{screenshot_id}:")
            logger.info(f"  Filename: {screenshot['current_filename']}")
            logger.info(f"  Category: {screenshot['category']}")
            logger.info(f"  Keywords: {', '.join(screenshot['keywords'])}")
            logger.info(f"  Confidence: {screenshot['confidence']:.2f}")
            logger.info(f"  OCR text: {screenshot['ocr_text'][:100]}...")


def example_combined_filters():
    """Example: Combine multiple filters."""
    logger.info("\n=== Combined Filters Example ===")
    
    search = SearchEngine(Path("data/screenshots.db"))
    
    # Search with multiple filters
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    results = search.search(
        query="database",
        category="ERROR",
        date_from=week_ago,
        date_to=today,
        min_confidence=0.8,
        limit=20
    )
    
    logger.info(f"Found {len(results)} results matching:")
    logger.info("  - Contains 'database'")
    logger.info("  - Category: ERROR")
    logger.info("  - Last 7 days")
    logger.info("  - Confidence >= 0.8")
    
    for result in results[:5]:
        logger.info(f"\n  {result['current_filename']}")
        logger.info(f"    Confidence: {result['confidence']:.2f}")
        logger.info(f"    Date: {result['created_date']}")


if __name__ == "__main__":
    logger.add("logs/search_example.log", rotation="10 MB")
    logger.info("🔍 Search Engine Examples\n")
    
    # Run examples (uncomment the ones you want)
    example_basic_search()
    # example_full_text_search()
    # example_advanced_search()
    # example_date_range()
    # example_suggestions()
    # example_statistics()
    # example_recent_screenshots()
    # example_get_by_id()
    # example_combined_filters()
