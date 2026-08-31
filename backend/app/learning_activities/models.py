"""Data models for learning activities."""

from enum import Enum


class LearningActivityStatus(str, Enum):
    """Status of a learning activity."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
