"""Pydantic data models for Screenshot Organizer."""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ScreenshotMetadata(BaseModel):
    """Image properties and file information."""
    file_path: Path
    original_filename: str
    file_size_bytes: int
    width: int
    height: int
    format: str  # PNG, JPEG, etc.
    created_timestamp: datetime
    modified_timestamp: datetime
    file_hash: str  # SHA256 hash for deduplication
    
    @field_validator('file_path', mode='before')
    @classmethod
    def validate_path(cls, v: Any) -> Path:
        return Path(v) if not isinstance(v, Path) else v


class VisionAnalysis(BaseModel):
    """Claude Vision API analysis result."""
    description: str
    content_type: str  # error|code|ui|design|document|screenshot|other
    objects_detected: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    has_text: bool
    confidence: float = Field(ge=0.0, le=1.0)


class ClassificationResult(BaseModel):
    """Screenshot classification and categorization."""
    category: str  # ERROR, CODE, UI, DOCUMENTATION, DATA, COMMUNICATION, OTHER
    keywords: List[str] = Field(default_factory=list)
    suggested_folder: str
    confidence: float = Field(ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    """Complete processing result for a screenshot."""
    metadata: ScreenshotMetadata
    ocr_text: Optional[str] = None
    vision_analysis: Optional[VisionAnalysis] = None
    classification: Optional[ClassificationResult] = None
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    processing_duration_ms: Optional[int] = None
    errors: List[str] = Field(default_factory=list)


class OrganizationResult(BaseModel):
    """File organization operation result."""
    original_filename: str
    new_filename: str
    source_path: Path
    destination_path: Path
    operation: str  # move|copy|rename
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_validator('source_path', 'destination_path', mode='before')
    @classmethod
    def validate_paths(cls, v: Any) -> Path:
        return Path(v) if not isinstance(v, Path) else v


class SearchQuery(BaseModel):
    """Search query parameters."""
    query_text: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    keywords: List[str] = Field(default_factory=list)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=50, ge=1, le=1000)
