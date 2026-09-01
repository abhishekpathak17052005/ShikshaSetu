"""Pydantic V2 request and response schemas for Trainer Assessment Studio."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class TrainerDashboardResponse(BaseModel):
    """Aggregated metrics for trainer dashboard."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    total_materials_uploaded: int = 0
    materials_count: int = 0
    total_questions_generated: int = 0
    questions_count: int = 0
    questions_approved: int = 0
    approved_questions_count: int = 0
    questions_rejected: int = 0
    rejected_questions_count: int = 0
    questions_pending_review: int = 0
    pending_questions_count: int = 0
    pending_review_count: int = 0
    total_quizzes_created: int = 0
    quizzes_count: int = 0
    published_quizzes: int = 0
    published_quizzes_count: int = 0
    total_assigned_learners: int = 0
    total_learner_attempts: int = 0
    learner_attempts_count: int = 0
    average_learner_score: float = 0.0
    average_score_all_quizzes: Optional[float] = None
    recent_materials: list[dict] = Field(default_factory=list)
    recent_quizzes: list[dict] = Field(default_factory=list)


class TrainerMaterialResponse(BaseModel):
    """Learning material representation for trainer."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(default="", validation_alias="_id")
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    status: str
    chunk_count: int
    questions_count: int
    approved_questions_count: int
    created_at: str


class TrainerQuestionResponse(BaseModel):
    """Detailed question representation in Trainer Review Studio."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(default="", validation_alias="_id")
    material_id: str
    competency_code: str
    question: str
    options: list[str]
    correct_answer: str
    explanation: str
    difficulty: str
    source_chunks: list[str] = Field(default_factory=list)
    grounding_score: Optional[float] = None
    status: str
    review_notes: Optional[str] = None
    created_at: str
    updated_at: str


class TrainerQuestionUpdateRequest(BaseModel):
    """Request to edit an AI-generated question."""
    question: Optional[str] = None
    options: Optional[list[str]] = Field(default=None, min_length=3, max_length=5)
    correct_answer: Optional[str] = Field(default=None, pattern="^[A-E]$")
    explanation: Optional[str] = None
    difficulty: Optional[str] = Field(default=None, pattern="^(EASY|MEDIUM|HARD)$")


class TrainerQuestionReviewRequest(BaseModel):
    """Request to approve or reject a question."""
    action: str = Field(pattern="^(APPROVE|REJECT)$")
    review_notes: Optional[str] = None


class TrainerGenerateQuestionsRequest(BaseModel):
    """Request to trigger RAG question generation for a material."""
    competency_code: str = Field(..., description="Target competency code")
    question_count: int = Field(default=5, ge=1, le=10)
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")


class TrainerQuizCreateRequest(BaseModel):
    """Request to create a quiz draft from approved questions."""
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    material_id: Optional[str] = None
    competency_code: str
    question_ids: list[str] = Field(min_length=1, description="IDs of approved trainer_questions")


class TrainerQuizResponse(BaseModel):
    """Quiz response for trainer management."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(default="", validation_alias="_id")
    trainer_id: str
    title: str
    description: Optional[str] = None
    competency_code: str
    status: str
    question_count: int
    questions: list[TrainerQuestionResponse] = Field(default_factory=list)
    assigned_learners_count: int = 0
    attempts_count: int = 0
    average_score: Optional[float] = None
    created_at: str
    published_at: Optional[str] = None


class TrainerQuizAssignRequest(BaseModel):
    """Request to assign a published quiz to learners."""
    learner_ids: list[str] = Field(min_length=1, description="List of learner user IDs to assign")


class TrainerQuizAssignResponse(BaseModel):
    """Response after assigning quiz."""
    quiz_id: str
    assigned_learners_count: int
    status: str
    message: str


class TrainerFeedbackRequest(BaseModel):
    """Feedback provided by trainer on a learner's quiz attempt."""
    feedback_text: str = Field(min_length=1)
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class TrainerLearnerAttemptResponse(BaseModel):
    """Learner attempt record with evaluation info."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    attempt_id: str = Field(default="", validation_alias="_id")
    quiz_id: str
    quiz_title: str
    learner_id: str
    learner_name: str
    learner_email: str
    score: int
    percentage: float
    correct_count: int
    total_questions: int
    competency_code: str
    submitted_at: str
    has_trainer_feedback: bool
    trainer_feedback: Optional[dict] = None


class TrainerLearnerSummary(BaseModel):
    """Summary of a learner assigned to trainer's quizzes."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    learner_id: str
    full_name: str
    email: str
    department: str
    designation: str
    assigned_quizzes_count: int
    completed_quizzes_count: int
    average_score: float
