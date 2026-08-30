"""MongoDB models for Quiz and QuizAttempt."""
from datetime import datetime
from enum import StrEnum
from typing import Any, Optional

from bson import ObjectId


class QuizStatus(StrEnum):
    """Quiz lifecycle status."""
    DRAFT = "DRAFT"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"


class QuizQuestion(dict):
    """
    Represents a single question in a quiz.
    Preserves Phase 6 MCQ structure with source traceability.
    """
    def __init__(
        self,
        question_id: str,
        question: str,
        options: list[str],
        correct_answer: str,
        explanation: str,
        difficulty: str,
        source_chunks: list[str],
    ):
        super().__init__(
            question_id=question_id,
            question=question,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            difficulty=difficulty,
            source_chunks=source_chunks,
        )


class QuizAnswer(dict):
    """Represents an answer to a quiz question."""
    def __init__(
        self,
        question_id: str,
        selected_answer: str,
        is_correct: bool,
    ):
        super().__init__(
            question_id=question_id,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )


class Quiz(dict):
    """
    MongoDB Quiz document.
    
    Stores:
    - Quiz metadata
    - Questions with full source traceability
    - Scoring and evidence linkage
    """
    
    @staticmethod
    def create(
        user_id: ObjectId,
        material_id: ObjectId,
        competency_code: str,
        title: str,
        questions: list[dict],
        question_count: int,
    ) -> dict:
        """Create a new quiz document."""
        now = datetime.utcnow()
        return {
            "_id": ObjectId(),
            "user_id": user_id,
            "material_id": material_id,
            "competency_code": competency_code,
            "title": title,
            "questions": questions,
            "question_count": question_count,
            "status": QuizStatus.READY,
            "created_at": now,
            "submitted_at": None,
            "score": None,
            "percentage": None,
        }


class QuizAttempt(dict):
    """
    MongoDB QuizAttempt document.
    
    Stores:
    - User's answers
    - Calculated score
    - Timestamps
    - Link to quiz and evidence
    """
    
    @staticmethod
    def create(
        quiz_id: ObjectId,
        user_id: ObjectId,
        answers: list[dict],
        score: int,
        percentage: float,
        correct_count: int,
        total_questions: int,
    ) -> dict:
        """Create a new quiz attempt document."""
        now = datetime.utcnow()
        return {
            "_id": ObjectId(),
            "quiz_id": quiz_id,
            "user_id": user_id,
            "answers": answers,
            "score": score,
            "percentage": percentage,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "started_at": now,
            "submitted_at": now,
        }
