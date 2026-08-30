"""Pydantic schemas for Capability Assessments."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CapabilityAssessmentCreateRequest(BaseModel):
    """Request to create a capability assessment."""
    
    competency_code: str = Field(
        ...,
        description="Competency code to assess (e.g., TECH_SQL)"
    )


class CapabilityAssessmentQuestionResponse(BaseModel):
    """Question in a capability assessment (without answer key)."""
    
    question_id: str
    question_type: str  # MCQ or SCENARIO
    question_text: str
    options: list[str]
    difficulty: str  # EASY, MEDIUM, HARD
    weight: float = Field(gt=0, default=1.0)
    scenario_context: str | None = None


class CapabilityAssessmentResponse(BaseModel):
    """Response when retrieving a capability assessment."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str
    competency_code: str
    assessment_type: str
    title: str
    questions: list[CapabilityAssessmentQuestionResponse]
    status: str
    started_at: datetime
    submitted_at: datetime | None = None
    score: float | None = None
    percentage: float | None = None
    normalized_score: float | None = None
    duration_seconds: int | None = None


class CapabilityAssessmentAnswerSubmission(BaseModel):
    """Single answer submission."""
    
    question_id: str = Field(..., description="ID of the question")
    selected_answer: str = Field(..., description="Selected option")


class CapabilityAssessmentSubmitRequest(BaseModel):
    """Request to submit assessment answers."""
    
    answers: list[CapabilityAssessmentAnswerSubmission] = Field(
        ...,
        description="List of answers for each question"
    )


class CompetencyResult(BaseModel):
    """Result for a competency after assessment."""
    
    competency_code: str
    score: float = Field(ge=1, le=5, description="Score on 1-5 scale")
    confidence: float = Field(ge=0, le=1, description="Confidence in score")


class CapabilityAssessmentSubmitResponse(BaseModel):
    """Response after submitting an assessment."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    assessment_id: str
    competency_code: str
    status: str
    score: float
    percentage: float
    normalized_score: float
    competency_results: list[CompetencyResult]
    submitted_at: datetime


class CapabilityAssessmentResultsResponse(BaseModel):
    """Full results for a submitted assessment."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    assessment_id: str
    competency_code: str
    status: str
    score: float
    percentage: float
    normalized_score: float
    duration_seconds: int | None = None
    correct_answers: int
    total_questions: int
    competency_results: list[CompetencyResult]
    submitted_at: datetime
    started_at: datetime


class CapabilityAssessmentListResponse(BaseModel):
    """Capability assessment in a list view."""
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str
    competency_code: str
    title: str
    status: str
    score: float | None = None
    percentage: float | None = None
    started_at: datetime
    submitted_at: datetime | None = None

