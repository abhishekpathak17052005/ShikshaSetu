"""Pydantic schemas for AI module."""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

VALID_BLOOM_LEVELS = {"REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"}


class GeneratedMCQ(BaseModel):
    """Schema for a generated multiple-choice question with traceability."""

    question: str = Field(..., min_length=10, description="The question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly four answer options")
    correct_answer: str = Field(..., description="The correct option letter (A, B, C, or D)")
    explanation: str = Field(..., min_length=10, description="Explanation for the correct answer")
    difficulty: str = Field(default="MEDIUM", description="Difficulty level: EASY, MEDIUM, HARD")
    bloom_level: str = Field(default="UNDERSTAND", description="Bloom's Taxonomy level")
    source_document_id: Optional[str] = Field(default=None, description="Source material ID")
    source_chunks: List[str] = Field(default_factory=list, description="IDs of source chunks this question is grounded in")

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: str) -> str:
        if not v or len(v) != 1 or v.upper() not in "ABCD":
            raise ValueError("correct_answer must be a single letter A-D")
        return v.upper()

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        if v.upper() not in ("EASY", "MEDIUM", "HARD"):
            raise ValueError("difficulty must be EASY, MEDIUM, or HARD")
        return v.upper()

    @field_validator("bloom_level")
    @classmethod
    def validate_bloom_level(cls, v: str) -> str:
        value = (v or "UNDERSTAND").upper()
        if value not in VALID_BLOOM_LEVELS:
            raise ValueError("bloom_level must be one of REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE")
        return value

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        if len(v) != 4:
            raise ValueError("options must contain exactly 4 unique choices")
        if len(set(v)) != len(v):
            raise ValueError("options must be unique")
        if any(not opt or not str(opt).strip() for opt in v):
            raise ValueError("options cannot be empty")
        return [str(opt).strip() for opt in v]

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What is the primary purpose of data normalization?",
                "options": [
                    "To increase data volume",
                    "To reduce data redundancy and improve consistency",
                    "To delete unnecessary data",
                    "To encrypt sensitive information",
                ],
                "correct_answer": "B",
                "explanation": "Data normalization reduces redundancy and ensures data consistency in relational databases.",
                "difficulty": "MEDIUM",
                "bloom_level": "UNDERSTAND",
                "source_chunks": ["chunk_1", "chunk_2"],
            }
        }
    }


class GenerationRequest(BaseModel):
    """Request to generate MCQs from a learning material."""

    competency_code: str = Field(..., description="Competency code (e.g., TECH_SQL)")
    question_count: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    difficulty: Optional[str] = Field(default=None, description="Target difficulty: EASY, MEDIUM, HARD (if not specified, mix)")
    bloom_level: Optional[str] = Field(default="UNDERSTAND", description="Target Bloom taxonomy level")

    @field_validator("bloom_level")
    @classmethod
    def validate_bloom_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        value = v.upper()
        if value not in VALID_BLOOM_LEVELS:
            raise ValueError("bloom_level must be one of REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE")
        return value

    model_config = {
        "json_schema_extra": {
            "example": {
                "competency_code": "TECH_SQL",
                "question_count": 5,
                "difficulty": "MEDIUM",
                "bloom_level": "UNDERSTAND",
            }
        }
    }


class GenerationResponse(BaseModel):
    """Response with generated MCQs."""

    material_id: str = Field(..., description="ID of the learning material")
    competency_code: str = Field(..., description="Competency code used for generation")
    questions: List[GeneratedMCQ] = Field(..., description="Generated questions")
    retrieved_chunk_count: int = Field(..., description="Number of chunks retrieved")
    generation_timestamp: str = Field(..., description="ISO timestamp of generation")

    model_config = {
        "json_schema_extra": {
            "example": {
                "material_id": "507f1f77bcf86cd799439011",
                "competency_code": "TECH_SQL",
                "questions": [
                    {
                        "question": "What is the primary purpose of data normalization?",
                        "options": [
                            "To increase data volume",
                            "To reduce data redundancy and improve consistency",
                            "To delete unnecessary data",
                            "To encrypt sensitive information",
                        ],
                        "correct_answer": "B",
                        "explanation": "Data normalization reduces redundancy and ensures data consistency in relational databases.",
                        "difficulty": "MEDIUM",
                        "bloom_level": "UNDERSTAND",
                        "source_chunks": ["chunk_1", "chunk_2"],
                    }
                ],
                "retrieved_chunk_count": 5,
                "generation_timestamp": "2024-01-15T10:30:00Z",
            }
        }
    }


class LearningMaterialResponse(BaseModel):
    """Response with learning material metadata."""

    id: str = Field(..., description="Material ID")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original filename as uploaded")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    extraction_status: Optional[str] = Field(..., description="Extraction result")
    processing_stage: Optional[str] = Field(default=None, description="Current processing stage")
    error_message: Optional[str] = Field(default=None, description="Last processing error")
    chunk_count: int = Field(..., description="Total chunks created")
    embedding_count: int = Field(..., description="Total chunks embedded")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    model_config = {"json_schema_extra": {"example": {"id": "507f1f77bcf86cd799439011", "filename": "sql_fundamentals_2024.pdf", "original_filename": "SQL Fundamentals.pdf", "content_type": "application/pdf", "file_size": 2048576, "status": "READY", "extraction_status": "SUCCESS", "chunk_count": 42, "embedding_count": 42, "created_at": "2024-01-15T09:00:00Z", "updated_at": "2024-01-15T09:05:00Z"}}}


class UploadResponse(BaseModel):
    """Response after document upload."""

    material_id: str = Field(..., description="ID of the uploaded material")
    filename: str = Field(..., description="Stored filename")
    status: str = Field(..., description="Current status")
    message: str = Field(..., description="Status message")
    processing_stage: Optional[str] = Field(default=None, description="Failed or completed processing stage")
    error_message: Optional[str] = Field(default=None, description="Processing error detail")

    model_config = {"json_schema_extra": {"example": {"material_id": "507f1f77bcf86cd799439011", "filename": "sql_fundamentals_2024.pdf", "status": "PROCESSING", "message": "Document uploaded and queued for processing"}}}
