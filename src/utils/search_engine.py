"""Search engine for finding screenshots."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger


class SearchEngine:
    """Search and filter screenshots from database."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search screenshots with filters."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            sql = "SELECT * FROM screenshots WHERE 1=1"
            params = []
            
            # Text search
            if query:
                sql += """ AND id IN (
                    SELECT DISTINCT screenshot_id 
                    FROM search_terms 
                    WHERE term LIKE ?
                )"""
                params.append(f"%{query.lower()}%")
            
            # Category filter
            if category:
                sql += " AND category = ?"
                params.append(category.upper())
            
            # Date range
            if date_from:
                sql += " AND created_date >= ?"
                params.append(date_from.isoformat())
            
            if date_to:
                sql += " AND created_date <= ?"
                params.append(date_to.isoformat())
            
            # Tags filter
            if tags:
                for tag in tags:
                    sql += " AND tags LIKE ?"
                    params.append(f"%{tag}%")
            
            # Confidence filter
            if min_confidence > 0:
                sql += " AND confidence >= ?"
                params.append(min_confidence)
            
            # Order and limit
            sql += " ORDER BY processed_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for result in results:
                result['keywords'] = json.loads(result['keywords']) if result['keywords'] else []
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
            
            conn.close()
            return results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def full_text_search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Full-text search across OCR text and keywords."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Search in OCR text and keywords
            cursor.execute("""
                SELECT DISTINCT s.*, 
                       SUM(st.weight) as relevance_score
                FROM screenshots s
                LEFT JOIN search_terms st ON s.id = st.screenshot_id
                WHERE st.term LIKE ? OR s.ocr_text LIKE ?
                GROUP BY s.id
                ORDER BY relevance_score DESC, s.processed_date DESC
                LIMIT ?
            """, (f"%{query.lower()}%", f"%{query}%", limit))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Parse JSON fields
            for result in results:
                result['keywords'] = json.loads(result['keywords']) if result['keywords'] else []
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
            
            conn.close()
            return results
        
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
            return []
    
    def filter_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all screenshots in a category."""
        return self.search(category=category, limit=limit)
    
    def filter_by_date_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get screenshots within date range."""
        return self.search(date_from=start, date_to=end, limit=limit)
    
    def advanced_search(self, query_string: str) -> List[Dict[str, Any]]:
        """Parse and execute advanced search query.
        
        Examples:
        - "error AND database"
        - "category:ERROR date:2025-12-01..2025-12-07"
        - "tag:important"
        """
        # Parse query string
        filters = {
            'query': None,
            'category': None,
            'date_from': None,
            'date_to': None,
            'tags': []
        }
        
        parts = query_string.split()
        query_terms = []
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                
                if key == 'category':
                    filters['category'] = value
                
                elif key == 'date':
                    if '..' in value:
                        start, end = value.split('..')
                        filters['date_from'] = datetime.fromisoformat(start)
                        filters['date_to'] = datetime.fromisoformat(end)
                    else:
                        filters['date_from'] = datetime.fromisoformat(value)
                
                elif key == 'tag':
                    filters['tags'].append(value)
            
            else:
                query_terms.append(part)
        
        if query_terms:
            filters['query'] = ' '.join(query_terms)
        
        return self.search(**filters)
    
    def get_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT term
                FROM search_terms
                WHERE term LIKE ?
                ORDER BY weight DESC
                LIMIT ?
            """, (f"{partial_query.lower()}%", limit))
            
            suggestions = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Suggestions failed: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Total screenshots
            cursor.execute("SELECT COUNT(*) FROM screenshots")
            total = cursor.fetchone()[0]
            
            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM screenshots
                GROUP BY category
                ORDER BY count DESC
            """)
            by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            # By date (last 30 days)
            cursor.execute("""
                SELECT DATE(created_date) as date, COUNT(*) as count
                FROM screenshots
                WHERE created_date >= date('now', '-30 days')
                GROUP BY DATE(created_date)
                ORDER BY date DESC
            """)
            by_date = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average confidence
            cursor.execute("SELECT AVG(confidence) FROM screenshots")
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return {
                'total_screenshots': total,
                'by_category': by_category,
                'by_date': by_date,
                'average_confidence': round(avg_confidence, 2)
            }
        
        except Exception as e:
            logger.error(f"Stats failed: {e}")
            return {}
    
    def get_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent screenshots."""
        return self.search(limit=limit)
    
    def get_by_id(self, screenshot_id: int) -> Optional[Dict[str, Any]]:
        """Get screenshot by ID."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM screenshots WHERE id = ?", (screenshot_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                result['keywords'] = json.loads(result['keywords']) if result['keywords'] else []
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                conn.close()
                return result
            
            conn.close()
            return None
        
        except Exception as e:
            logger.error(f"Get by ID failed: {e}")
            return None
