"""Learning Materials Model for MongoDB."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LearningMaterial(BaseModel):
    """
    Learning material document model.
    
    Represents an uploaded document (PDF, DOCX, PPTX) belonging to a user.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="ID of the user who uploaded the material")
    filename: str = Field(..., description="Stored filename (sanitized)")
    original_filename: str = Field(..., description="Original filename as uploaded")
    content_type: str = Field(..., description="MIME type (e.g., application/pdf)")
    file_size: int = Field(..., description="File size in bytes")
    storage_reference: str = Field(..., description="Reference to stored file (e.g., path)")
    
    status: str = Field(
        default="UPLOADED",
        description="Processing status: UPLOADED, PROCESSING, READY, FAILED"
    )
    extraction_status: Optional[str] = Field(
        default=None,
        description="Extraction result: SUCCESS, FAILURE, or None if not yet extracted"
    )
    extraction_error: Optional[str] = Field(
        default=None,
        description="Error message if extraction failed"
    )
    
    chunk_count: int = Field(default=0, description="Number of chunks created")
    embedding_count: int = Field(default=0, description="Number of chunks embedded")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True


class DocumentChunk(BaseModel):
    """
    Document chunk model for persistence.
    
    Represents a chunk of text extracted from a learning material.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    material_id: str = Field(..., description="Reference to LearningMaterial")
    sequence: int = Field(..., description="Sequential chunk number within the material")
    text: str = Field(..., description="Chunk text content")
    
    # Source metadata for traceability
    source_page: Optional[int] = Field(default=None, description="Page number (PDF/DOCX)")
    source_slide: Optional[int] = Field(default=None, description="Slide number (PPTX)")
    source_section: Optional[str] = Field(default=None, description="Section/heading")
    
    # Embedding
    embedding: Optional[list] = Field(default=None, description="Vector embedding (if embedded)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
