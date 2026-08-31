"""Pydantic schemas for the Adaptive Capability Assessment Engine."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AdaptiveStartRequest(BaseModel):
    competency_code: str = Field(..., description="Target competency code to evaluate (e.g. STAT_SAMPLING)")
    max_questions: int = Field(default=5, ge=3, le=10, description="Target questions per assessment session")


class AdaptiveQuestionItem(BaseModel):
    question_id: str
    question_type: str
    question_text: str
    options: List[str] = Field(default_factory=list)
    difficulty: str
    scenario_context: Optional[str] = None


class AdaptiveStartResponse(BaseModel):
    session_id: str
    competency_code: str
    competency_name: str
    estimated_level: float
    difficulty: str
    proficiency_tier: str
    current_question_number: int
    total_questions_planned: int
    question: Optional[AdaptiveQuestionItem] = None
    status: str = "IN_PROGRESS"


class AdaptiveAnswerRequest(BaseModel):
    question_id: str
    selected_answer: str = Field(..., description="Selected option key or text (e.g. 'A', 'B', 'C', 'D')")


class AdaptiveAnswerResponse(BaseModel):
    session_id: str
    is_correct: bool
    explanation: Optional[str] = None
    previous_estimated_level: float
    updated_estimated_level: float
    next_difficulty: str
    proficiency_tier: str
    questions_completed: int
    total_questions_planned: int
    is_complete: bool
    next_question: Optional[AdaptiveQuestionItem] = None


class AdaptiveFinalizeResponse(BaseModel):
    session_id: str
    competency_code: str
    competency_name: str
    final_demonstrated_level: float
    proficiency_tier: str
    total_questions: int
    correct_count: int
    accuracy_pct: float
    previous_competency_level: float
    updated_competency_level: float
    previous_skill_gap: float
    updated_skill_gap: float
    evidence_record_id: str
    evidence_type: str = "CAPABILITY_ASSESSMENT"
    evidence_confidence: float = 0.85
    completed_at: str
    status: str = "COMPLETED"
