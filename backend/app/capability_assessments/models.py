"""MongoDB models for Capability Assessments."""
from datetime import datetime
from enum import StrEnum

from bson import ObjectId


class CapabilityAssessmentStatus(StrEnum):
    """Status of a capability assessment."""
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"


class CapabilityAssessment(dict):
    """
    MongoDB document for a capability assessment instance.
    
    Represents a specific assessment taken by a user for a competency.
    Stores questions (without answer keys) and eventually user answers.
    """
    
    @staticmethod
    def create(
        user_id: ObjectId,
        competency_code: str,
        configuration_id: ObjectId,
        title: str,
        questions: list[dict],
    ) -> dict:
        """Create a new capability assessment document."""
        now = datetime.utcnow()
        return {
            "_id": ObjectId(),
            "user_id": user_id,
            "competency_code": competency_code,
            "configuration_id": configuration_id,
            "assessment_type": "CAPABILITY_ASSESSMENT",
            "title": title,
            "questions": questions,  # Without correct_answer (only question_id, text, options, etc.)
            "answers": [],  # Will be filled on submission
            "status": CapabilityAssessmentStatus.IN_PROGRESS,
            "score": None,  # Raw score (0-1)
            "percentage": None,  # Percentage correct
            "normalized_score": None,  # 1-5 scale
            "started_at": now,
            "submitted_at": None,
            "duration_seconds": None,
            "competency_results": [],  # Will be filled on submission
            "created_at": now,
            "updated_at": now,
        }


class CapabilityAssessmentAnswer(dict):
    """
    Represents a user's answer to a question in an assessment.
    """
    
    def __init__(
        self,
        question_id: str,
        selected_answer: str,
        is_correct: bool = False,
    ):
        """Create an answer record."""
        super().__init__(
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )
