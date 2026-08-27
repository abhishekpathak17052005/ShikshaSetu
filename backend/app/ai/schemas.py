"""Pydantic schemas for AI module."""
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class GeneratedMCQ(BaseModel):
    """
    Schema for a generated multiple-choice question.
    
    Grounded MCQ with source traceability.
    """

    question: str = Field(..., min_length=10, description="The question text")
    options: List[str] = Field(
        ...,
        min_items=3,
        max_items=5,
        description="Answer options"
    )
    correct_answer: str = Field(
        ...,
        description="The correct option letter (A, B, C, D, E)"
    )
    explanation: str = Field(
        ...,
        min_length=10,
        description="Explanation for the correct answer"
    )
    difficulty: str = Field(
        default="MEDIUM",
        description="Difficulty level: EASY, MEDIUM, HARD"
    )
    source_chunks: List[str] = Field(
        default_factory=list,
        description="IDs of source chunks this question is grounded in"
    )

    @validator("correct_answer")
    def validate_correct_answer(cls, v):
        """Validate that correct_answer is a valid letter."""
        if not v or len(v) != 1 or v.upper() not in "ABCDE":
            raise ValueError("correct_answer must be a single letter A-E")
        return v.upper()

    @validator("difficulty")
    def validate_difficulty(cls, v):
        """Validate difficulty level."""
        if v.upper() not in ("EASY", "MEDIUM", "HARD"):
            raise ValueError("difficulty must be EASY, MEDIUM, or HARD")
        return v.upper()

    @validator("options")
    def validate_options(cls, v):
        """Validate options are unique and not empty."""
        if len(set(v)) != len(v):
            raise ValueError("options must be unique")
        if any(not opt.strip() for opt in v):
            raise ValueError("options cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the primary purpose of data normalization?",
                "options": [
                    "To increase data volume",
                    "To reduce data redundancy and improve consistency",
                    "To delete unnecessary data",
                    "To encrypt sensitive information"
                ],
                "correct_answer": "B",
                "explanation": "Data normalization reduces redundancy and ensures data consistency in relational databases.",
                "difficulty": "MEDIUM",
                "source_chunks": ["chunk_1", "chunk_2"]
            }
        }


class GenerationRequest(BaseModel):
    """Request to generate MCQs from a learning material."""

    competency_code: str = Field(..., description="Competency code (e.g., TECH_SQL)")
    question_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of questions to generate"
    )
    difficulty: Optional[str] = Field(
        default=None,
        description="Target difficulty: EASY, MEDIUM, HARD (if not specified, mix)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "competency_code": "TECH_SQL",
                "question_count": 5,
                "difficulty": "MEDIUM"
            }
        }


class GenerationResponse(BaseModel):
    """Response with generated MCQs."""

    material_id: str = Field(..., description="ID of the learning material")
    competency_code: str = Field(..., description="Competency code used for generation")
    questions: List[GeneratedMCQ] = Field(..., description="Generated questions")
    retrieved_chunk_count: int = Field(..., description="Number of chunks retrieved")
    generation_timestamp: str = Field(..., description="ISO timestamp of generation")

    class Config:
        json_schema_extra = {
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
                            "To encrypt sensitive information"
                        ],
                        "correct_answer": "B",
                        "explanation": "Data normalization reduces redundancy and ensures data consistency in relational databases.",
                        "difficulty": "MEDIUM",
                        "source_chunks": ["chunk_1", "chunk_2"]
                    }
                ],
                "retrieved_chunk_count": 5,
                "generation_timestamp": "2024-01-15T10:30:00Z"
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
    chunk_count: int = Field(..., description="Total chunks created")
    embedding_count: int = Field(..., description="Total chunks embedded")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "filename": "sql_fundamentals_2024.pdf",
                "original_filename": "SQL Fundamentals.pdf",
                "content_type": "application/pdf",
                "file_size": 2048576,
                "status": "READY",
                "extraction_status": "SUCCESS",
                "chunk_count": 42,
                "embedding_count": 42,
                "created_at": "2024-01-15T09:00:00Z",
                "updated_at": "2024-01-15T09:05:00Z"
            }
        }


class UploadResponse(BaseModel):
    """Response after document upload."""

    material_id: str = Field(..., description="ID of the uploaded material")
    filename: str = Field(..., description="Stored filename")
    status: str = Field(..., description="Current status")
    message: str = Field(..., description="Status message")

    class Config:
        json_schema_extra = {
            "example": {
                "material_id": "507f1f77bcf86cd799439011",
                "filename": "sql_fundamentals_2024.pdf",
                "status": "PROCESSING",
                "message": "Document uploaded and queued for processing"
            }
        }
