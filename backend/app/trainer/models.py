"""MongoDB document models and enums for Trainer Assessment Studio."""
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Optional
from bson import ObjectId


class QuestionReviewStatus(StrEnum):
    """Lifecycle status for AI-generated questions under trainer review."""
    GENERATED = "GENERATED"
    EDITED = "EDITED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class TrainerQuizStatus(StrEnum):
    """Lifecycle status for quizzes managed in the Trainer Studio."""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ASSIGNED = "ASSIGNED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class TrainerQuestion(dict):
    """MongoDB model for generated/reviewed question."""

    @staticmethod
    def create(
        trainer_id: str,
        material_id: str,
        competency_code: str,
        question: str,
        options: list[str],
        correct_answer: str,
        explanation: str,
        difficulty: str = "MEDIUM",
        bloom_level: str = "UNDERSTAND",
        source_document_id: str | None = None,
        source_chunks: list[str] | None = None,
        grounding_score: float | None = None,
        status: QuestionReviewStatus = QuestionReviewStatus.GENERATED,
    ) -> dict:
        now = datetime.now(UTC)
        return {
            "_id": ObjectId(),
            "trainer_id": str(trainer_id),
            "material_id": str(material_id),
            "competency_code": competency_code,
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "difficulty": difficulty,
            "bloom_level": bloom_level,
            "source_document_id": source_document_id,
            "source_chunks": source_chunks or [],
            "grounding_score": grounding_score,
            "status": status.value if isinstance(status, QuestionReviewStatus) else status,
            "review_notes": None,
            "created_at": now,
            "updated_at": now,
        }


class TrainerQuiz(dict):
    """MongoDB model for Trainer Quiz draft, publication, and assignment."""

    @staticmethod
    def create(
        trainer_id: str,
        material_id: str | None,
        competency_code: str,
        title: str,
        description: str | None,
        questions: list[dict],
        question_ids: list[str],
        target_competency_ids: list[str] | None = None,
        target_role_ids: list[str] | None = None,
        target_designation_ids: list[str] | None = None,
        difficulty: str = "MEDIUM",
        assignment_type: str = "COMPETENCY_TARGETED",
    ) -> dict:
        now = datetime.now(UTC)
        return {
            "_id": ObjectId(),
            "trainer_id": str(trainer_id),
            "user_id": ObjectId(trainer_id) if ObjectId.is_valid(trainer_id) else trainer_id,
            "material_id": ObjectId(material_id) if material_id and ObjectId.is_valid(material_id) else material_id,
            "competency_code": competency_code,
            "title": title,
            "description": description or "",
            "status": TrainerQuizStatus.DRAFT.value,
            "questions": questions,
            "question_ids": question_ids,
            "question_count": len(questions),
            "target_competency_ids": target_competency_ids or ([competency_code] if competency_code else []),
            "target_role_ids": target_role_ids or [],
            "target_designation_ids": target_designation_ids or [],
            "difficulty": difficulty,
            "assignment_type": assignment_type,
            "assigned_to": [],  # List of learner user_id strings
            "assigned_user_ids": [],
            "published": False,
            "created_at": now,
            "updated_at": now,
            "published_at": None,
        }
