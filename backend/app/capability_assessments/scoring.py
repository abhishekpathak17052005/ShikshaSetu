"""Scoring functions for capability assessments."""
from app.assessments.scoring import score_ratio


def calculate_question_score(selected_answer: str, correct_answer: str) -> float:
    """
    Calculate score for a single question (MCQ or SCENARIO).
    
    Args:
        selected_answer: The answer selected by the user
        correct_answer: The correct answer from the question
    
    Returns:
        1.0 if correct, 0.0 if incorrect
    """
    return 1.0 if selected_answer == correct_answer else 0.0


def calculate_assessment_percentage(answers_data: list[dict]) -> float:
    """
    Calculate percentage of questions answered correctly.
    
    Args:
        answers_data: List of answer dicts with 'is_correct' field
    
    Returns:
        Percentage as float (0.0 to 1.0)
    """
    if not answers_data:
        return 0.0
    
    correct_count = sum(1 for answer in answers_data if answer.get("is_correct", False))
    total_count = len(answers_data)
    
    return correct_count / total_count if total_count > 0 else 0.0


def calculate_normalized_score_from_percentage(percentage: float) -> float:
    """
    Convert percentage (0-1) to normalized score (1-5 scale).
    
    Uses existing score_ratio logic:
    0-19%   → 1
    20-39%  → 2
    40-59%  → 3
    60-79%  → 4
    80-100% → 5
    
    Args:
        percentage: Percentage correct (0.0 to 1.0)
    
    Returns:
        Normalized score on 1-5 scale
    """
    return score_ratio(percentage)


def calculate_raw_score(percentage: float) -> float:
    """
    Calculate raw score from percentage.
    Raw score is the percentage as decimal (0.0 to 1.0).
    
    Args:
        percentage: Percentage correct
    
    Returns:
        Raw score (same as percentage)
    """
    return max(0.0, min(1.0, percentage))
