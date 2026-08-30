"""Models for question bank."""
from enum import StrEnum


class QuestionType(StrEnum):
    """Question types for capability assessments."""
    MCQ = "MCQ"
    SCENARIO = "SCENARIO"


class QuestionDifficulty(StrEnum):
    """Difficulty levels for questions."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionStatus(StrEnum):
    """Status of a question in the bank."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"
