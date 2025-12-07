"""Naming agent for generating intelligent filenames."""
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional


WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}


class NamingAgent:
    """Generate intelligent filenames for screenshots."""
    
    def __init__(self, max_length: int = 200):
        self.max_length = max_length
    
    def generate_filename(
        self,
        category: str,
        keywords: list[str],
        file_path: Path,
        created_date: Optional[datetime] = None
    ) -> str:
        """Generate filename: DATE_CATEGORY-CODE_KEYWORDS_HASH.ext"""
        file_path = Path(file_path)
        
        # Get date
        if created_date is None:
            created_date = datetime.fromtimestamp(file_path.stat().st_ctime)
        date_str = created_date.strftime("%Y-%m-%d")
        
        # Get category code
        category_code = self._get_category_code(category, keywords)
        
        # Get keywords (2-4 main ones)
        keyword_str = self._format_keywords(keywords[:4])
        
        # Get file hash
        file_hash = self._get_file_hash(file_path)
        
        # Get extension
        ext = file_path.suffix
        
        # Build filename
        parts = [date_str, category_code, keyword_str, file_hash]
        filename = "_".join(p for p in parts if p) + ext
        
        # Sanitize
        filename = self._sanitize_filename(filename)
        
        # Truncate if needed
        filename = self._truncate_filename(filename, ext)
        
        return filename
    
    def _get_category_code(self, category: str, keywords: list[str]) -> str:
        """Generate category code with subcategory."""
        category = category.upper()
        
        # Map categories to short codes
        category_map = {
            "ERROR": "Error",
            "CODE": "Code",
            "UI": "UI",
            "DOCUMENTATION": "Docs",
            "DATA": "Data",
            "COMMUNICATION": "Comm",
            "OTHER": "Other"
        }
        
        base = category_map.get(category, "Other")
        
        # Add subcategory from keywords
        subcat = self._get_subcategory(category, keywords)
        if subcat:
            return f"{base}-{subcat}"
        
        return base
    
    def _get_subcategory(self, category: str, keywords: list[str]) -> Optional[str]:
        """Extract subcategory from keywords."""
        if not keywords:
            return None
        
        keywords_lower = [k.lower() for k in keywords]
        
        if category == "ERROR":
            # Look for error codes
            for kw in keywords_lower:
                if kw.isdigit() and len(kw) == 3:  # HTTP codes
                    return kw
                if "404" in kw or "500" in kw or "503" in kw:
                    return kw.replace("error", "").replace("_", "").strip()
            # Look for error types
            if "database" in keywords_lower or "db" in keywords_lower:
                return "DB"
            if "network" in keywords_lower or "timeout" in keywords_lower:
                return "Net"
            if "memory" in keywords_lower or "oom" in keywords_lower:
                return "OOM"
        
        elif category == "CODE":
            # Look for languages
            lang_map = {
                "python": "Python",
                "javascript": "JS",
                "typescript": "TS",
                "java": "Java",
                "rust": "Rust",
                "go": "Go",
                "config": "Config",
                "yaml": "Config",
                "json": "Config"
            }
            for kw in keywords_lower:
                if kw in lang_map:
                    return lang_map[kw]
        
        elif category == "UI":
            # Look for UI components
            ui_map = {
                "dashboard": "Dashboard",
                "login": "Login",
                "signup": "Signup",
                "settings": "Settings",
                "form": "Form"
            }
            for kw in keywords_lower:
                if kw in ui_map:
                    return ui_map[kw]
        
        elif category == "DATA":
            if "chart" in keywords_lower or "graph" in keywords_lower:
                return "Chart"
            if "report" in keywords_lower:
                return "Report"
            if "table" in keywords_lower:
                return "Table"
        
        return None
    
    def _format_keywords(self, keywords: list[str]) -> str:
        """Format keywords for filename."""
        if not keywords:
            return ""
        
        # Take 2-4 keywords, sanitize, and join
        formatted = []
        for kw in keywords[:4]:
            # Remove special chars, capitalize first letter
            clean = re.sub(r'[^a-zA-Z0-9]', '', kw)
            if clean:
                formatted.append(clean.capitalize())
        
        return "_".join(formatted) if formatted else ""
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate 4-character hash from file content."""
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()[:4]
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters and handle reserved names."""
        # Remove invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, '', filename)
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        # Check for Windows reserved names
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in WINDOWS_RESERVED:
            filename = f"File_{filename}"
        
        return filename
    
    def _truncate_filename(self, filename: str, ext: str) -> str:
        """Truncate filename to max length while preserving extension."""
        if len(filename) <= self.max_length:
            return filename
        
        # Calculate available space for name (minus extension)
        available = self.max_length - len(ext)
        
        # Truncate name part
        name = filename[:-len(ext)]
        truncated_name = name[:available]
        
        # Try to truncate at underscore boundary
        last_underscore = truncated_name.rfind('_')
        if last_underscore > available * 0.7:  # Keep at least 70% of name
            truncated_name = truncated_name[:last_underscore]
        
        return truncated_name + ext
    
    def handle_duplicate(self, filename: str, target_dir: Path) -> str:
        """Handle duplicate filenames by appending (1), (2), etc."""
        if not (target_dir / filename).exists():
            return filename
        
        # Split name and extension
        path = Path(filename)
        name = path.stem
        ext = path.suffix
        
        # Find next available number
        counter = 1
        while True:
            new_name = f"{name}({counter}){ext}"
            if not (target_dir / new_name).exists():
                return new_name
            counter += 1
            if counter > 1000:  # Safety limit
                raise ValueError("Too many duplicate files")
