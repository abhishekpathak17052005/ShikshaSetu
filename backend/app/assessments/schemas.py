from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AssessmentType(StrEnum):
    INITIAL_COMPETENCY = "INITIAL_COMPETENCY"


class QuestionType(StrEnum):
    SELF_RATING = "SELF_RATING"
    MCQ = "MCQ"
    SCENARIO = "SCENARIO"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"


class AssessmentScoringConfig(BaseModel):
    self_assessment_weight: float = Field(default=0.20, ge=0, le=1)
    knowledge_test_weight: float = Field(default=0.40, ge=0, le=1)
    scenario_test_weight: float = Field(default=0.30, ge=0, le=1)
    training_evidence_weight: float = Field(default=0.10, ge=0, le=1)
    training_evidence_score: float = Field(default=4.0, ge=1, le=5)

    @model_validator(mode="after")
    def weights_must_sum_to_one(self) -> "AssessmentScoringConfig":
        weights = (
            self.self_assessment_weight,
            self.knowledge_test_weight,
            self.scenario_test_weight,
            self.training_evidence_weight,
        )
        if abs(sum(weights) - 1.0) > 1e-9:
            raise ValueError("assessment weights must sum to 1")
        return self


class QuestionResponse(BaseModel):
    question_id: str
    competency_id: str
    question_type: QuestionType
    question_text: str
    options: list[str] = Field(default_factory=list)
    scenario_context: str | None = None
    difficulty: str
    weight: float = Field(gt=0)


class AssessmentResponse(BaseModel):
    id: str
    assessment_type: AssessmentType
    assessment_key: str
    title: str
    description: str
    competency_ids: list[str]
    questions: list[QuestionResponse]
    status: str
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class StartAssessmentRequest(BaseModel):
    assessment_key: str = "initial-competency-v1"


class AssessmentAnswer(BaseModel):
    question_id: str
    answer: str = Field(min_length=1)

    @field_validator("answer")
    @classmethod
    def strip_answer(cls, value: str) -> str:
        return value.strip()


class TrainingEvidenceSubmission(BaseModel):
    training_name: str = Field(min_length=1, max_length=200)
    provider: str = Field(min_length=1, max_length=200)
    completion_date: datetime | None = None
    duration: str | None = Field(default=None, max_length=100)
    competencies: list[str] = Field(min_length=1)
    certificate_reference: str | None = Field(default=None, max_length=300)


class SubmitAssessmentRequest(BaseModel):
    self_ratings: dict[str, float] = Field(default_factory=dict)
    answers: list[AssessmentAnswer] = Field(default_factory=list)
    training_evidence: list[TrainingEvidenceSubmission] = Field(default_factory=list)

    @field_validator("self_ratings")
    @classmethod
    def validate_self_ratings(cls, value: dict[str, float]) -> dict[str, float]:
        if any(rating < 1 or rating > 5 for rating in value.values()):
            raise ValueError("self ratings must be between 1 and 5")
        return value


class CompetencyResult(BaseModel):
    competency_id: str
    score: float = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)


class AssessmentAttemptResponse(BaseModel):
    id: str
    assessment_id: str
    assessment_type: AssessmentType
    assessment_version: int
    status: AttemptStatus
    questions: list[QuestionResponse]
    started_at: datetime
    submitted_at: datetime | None = None
    competency_results: list[CompetencyResult] = Field(default_factory=list)


class AssessmentSubmissionResponse(BaseModel):
    attempt_id: str
    status: AttemptStatus
    competency_results: list[CompetencyResult]


class ComponentScores(BaseModel):
    self_assessment: float | None = Field(default=None, ge=1, le=5)
    knowledge_test: float | None = Field(default=None, ge=1, le=5)
    scenario_test: float | None = Field(default=None, ge=1, le=5)
    training_evidence: float | None = Field(default=None, ge=1, le=5)

    model_config = ConfigDict(extra="forbid")
