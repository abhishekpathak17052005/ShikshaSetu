"""Pydantic V2 request and response schemas for Trainer Assessment Studio."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    processing_stage: Optional[str] = None
    error_message: Optional[str] = None
    chunk_count: int
    questions_count: int
    approved_questions_count: int
    created_at: str


class TrainerQuestionResponse(BaseModel):
    """Detailed question representation in Trainer Review Studio."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(default="", validation_alias="_id")
    material_id: Optional[str] = ""
    competency_code: Optional[str] = ""
    question: str
    options: list[str]
    correct_answer: str
    explanation: Optional[str] = ""
    difficulty: Optional[str] = "MEDIUM"
    bloom_level: Optional[str] = "UNDERSTAND"
    source_document_id: Optional[str] = None
    source_chunks: list[str] = Field(default_factory=list)
    grounding_score: Optional[float] = None
    status: str
    review_notes: Optional[str] = None
    created_at: Optional[str] = ""
    updated_at: Optional[str] = ""


class TrainerQuestionUpdateRequest(BaseModel):
    """Request to edit an AI-generated question in review studio."""
    question: Optional[str] = None
    options: Optional[list[str]] = Field(default=None)
    correct_answer: Optional[str] = Field(default=None)
    explanation: Optional[str] = None
    difficulty: Optional[str] = Field(default=None, pattern="^(EASY|MEDIUM|HARD)$")
    bloom_level: Optional[str] = Field(default=None, pattern="^(REMEMBER|UNDERSTAND|APPLY|ANALYZE|EVALUATE|CREATE)$")
    competency_code: Optional[str] = None

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) != 4:
            raise ValueError("options must contain exactly 4 choices")
        cleaned = [str(opt).strip() for opt in v]
        if any(not opt for opt in cleaned):
            raise ValueError("All 4 options must be non-empty")
        if len(set(cleaned)) != 4:
            raise ValueError("All 4 options must be unique")
        return cleaned

    @field_validator("correct_answer")
    @classmethod
    def validate_correct_answer(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        norm = str(v).strip().upper()
        if norm in ("0", "1", "2", "3"):
            return chr(65 + int(norm))
        if norm not in ("A", "B", "C", "D"):
            raise ValueError("correct_answer must be one of A, B, C, or D")
        return norm

    @field_validator("bloom_level")
    @classmethod
    def validate_bloom_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        norm = v.strip().upper()
        if norm not in ("REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"):
            raise ValueError("bloom_level must be one of REMEMBER, UNDERSTAND, APPLY, ANALYZE, EVALUATE, CREATE")
        return norm



class TrainerQuestionReviewRequest(BaseModel):
    """Request to approve or reject a question."""
    action: Optional[str] = Field(default=None, pattern="^(APPROVE|REJECT)$")
    review_notes: Optional[str] = None


class TrainerGenerateQuestionsRequest(BaseModel):
    """Request to trigger RAG question generation for a material."""
    competency_code: str = Field(..., description="Target competency code")
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")
    bloom_level: Optional[str] = Field(default="UNDERSTAND")


class TrainerQuizCreateRequest(BaseModel):
    """Request to create a quiz draft from approved questions."""
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    material_id: Optional[str] = None
    competency_code: str
    question_ids: list[str] = Field(min_length=1, description="IDs of approved trainer_questions")
    target_competency_ids: list[str] = Field(default_factory=list)
    target_role_ids: list[str] = Field(default_factory=list)
    target_designation_ids: list[str] = Field(default_factory=list)
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")


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
    target_competency_ids: list[str] = Field(default_factory=list)
    target_role_ids: list[str] = Field(default_factory=list)
    target_designation_ids: list[str] = Field(default_factory=list)
    difficulty: str = "MEDIUM"
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
    id: Optional[str] = None
    _id: Optional[str] = None
    full_name: str
    email: str
    department: str
    designation: str
    employee_id: Optional[str] = None
    access_role: Optional[str] = "OFFICIAL"
    assigned_quizzes_count: int
    completed_quizzes_count: int
    average_score: float

