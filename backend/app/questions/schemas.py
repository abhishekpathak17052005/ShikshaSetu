"""Pydantic schemas for questions."""
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.questions.models import QuestionDifficulty, QuestionStatus, QuestionType


class QuestionResponse(BaseModel):
    """Response schema for a question (without correct answer)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(alias="_id")
    question_id: str
    competency_code: str
    question_type: QuestionType
    question_text: str
    options: list[str]
    difficulty: QuestionDifficulty
    weight: float = Field(gt=0, default=1.0)
    scenario_context: str | None = None
    created_at: datetime
    
    # Note: correct_answer is NOT included in response


class QuestionInternalResponse(BaseModel):
    """Internal response with correct answer (for server-side scoring only)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(alias="_id")
    question_id: str
    competency_code: str
    question_type: QuestionType
    question_text: str
    options: list[str]
    correct_answer: str
    difficulty: QuestionDifficulty
    weight: float = Field(gt=0, default=1.0)
    explanation: str | None = None
    scenario_context: str | None = None
    source: str | None = None
    status: QuestionStatus
    created_at: datetime


class QuestionAnswerRequest(BaseModel):
    """Request to answer a question."""
    
    question_id: str = Field(..., description="ID of the question")
    selected_answer: str = Field(..., description="Selected option (A, B, C, D, etc.)")


class QuestionSummary(BaseModel):
    """Summary of question for assessment (no answers)."""
    
    question_id: str
    question_type: QuestionType
    question_text: str
    options: list[str]
    difficulty: QuestionDifficulty
    weight: float = Field(gt=0, default=1.0)
    scenario_context: str | None = None
