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

    Represents a chunk of text extracted from a learning material, with full
    metadata for filtered retrieval and embedding lifecycle management.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    material_id: str = Field(..., description="Reference to LearningMaterial")
    sequence: int = Field(..., description="Sequential chunk number within the material")
    text: str = Field(..., description="Chunk text content")

    # Source provenance — preserved from extractor
    source_page: Optional[int] = Field(default=None, description="Page number (PDF/DOCX)")
    source_slide: Optional[int] = Field(default=None, description="Slide number (PPTX)")
    source_section: Optional[str] = Field(default=None, description="Section/heading")

    # Extended metadata for filtered retrieval (P0 upgrade)
    competency_code: Optional[str] = Field(
        default=None,
        description="Competency this chunk is associated with (set at generation time or upload)"
    )
    domain: Optional[str] = Field(
        default=None,
        description="Competency domain: STATISTICAL / TECHNICAL / GOVERNANCE / BEHAVIORAL"
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Type of source document: CURRICULUM / IGOT_COURSE / NSSTA_PROGRAMME / POLICY"
    )
    language: Optional[str] = Field(
        default="en",
        description="ISO 639-1 language code of the chunk text"
    )

    # Embedding lifecycle (P0 upgrade — replaces silent SHA-256 fallback)
    embedding: Optional[list] = Field(
        default=None,
        description="Vector embedding stored as float list (excluded from DB writes via repo layer)"
    )
    embedding_status: str = Field(
        default="PENDING",
        description="PENDING | EMBEDDED | FAILED — tracks real embedding state"
    )
    embedding_model: Optional[str] = Field(
        default=None,
        description="Model name used to generate the embedding"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
