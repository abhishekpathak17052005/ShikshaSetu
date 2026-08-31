"""Deterministic capability calibration and difficulty transition formulas."""

from typing import List

# Calibration Boundaries
MIN_THETA: float = 1.0
MAX_THETA: float = 5.0
DEFAULT_INITIAL_THETA: float = 2.5

# Step adjustments based on question difficulty
CORRECT_STEP_MAP = {
    "EASY": 0.30,
    "MEDIUM": 0.40,
    "HARD": 0.50,
}

INCORRECT_STEP_MAP = {
    "HARD": 0.30,
    "MEDIUM": 0.40,
    "EASY": 0.50,
}


def map_theta_to_difficulty(theta: float) -> str:
    """
    Maps continuous capability theta in [1.0, 5.0] to discrete target question difficulty.
    - L1-L2 Foundation (1.0 <= theta < 2.2): EASY
    - L3 Intermediate (2.2 <= theta < 3.8): MEDIUM
    - L4-L5 Advanced (3.8 <= theta <= 5.0): HARD
    """
    if theta < 2.2:
        return "EASY"
    elif theta < 3.8:
        return "MEDIUM"
    else:
        return "HARD"


def map_theta_to_level_label(theta: float) -> str:
    """Returns human-readable proficiency tier aligned with civil services framework."""
    if theta < 1.8:
        return "Level 1 — Awareness / Basic Foundation"
    elif theta < 2.8:
        return "Level 2 — Working Operational Knowledge"
    elif theta < 3.8:
        return "Level 3 — Intermediate Practitioner"
    elif theta < 4.6:
        return "Level 4 — Advanced Specialist"
    else:
        return "Level 5 — Expert / Policy Authority"


def calculate_next_theta(
    current_theta: float,
    difficulty: str,
    is_correct: bool,
) -> float:
    """
    Computes the updated demonstrated capability score theta.
    Guaranteed: 1.0 <= theta <= 5.0.
    """
    diff_key = difficulty.upper() if difficulty else "MEDIUM"
    
    if is_correct:
        step = CORRECT_STEP_MAP.get(diff_key, 0.40)
        new_theta = min(MAX_THETA, current_theta + step)
    else:
        step = INCORRECT_STEP_MAP.get(diff_key, 0.40)
        new_theta = max(MIN_THETA, current_theta - step)

    return round(new_theta, 2)


def get_difficulty_fallback_order(target_difficulty: str) -> List[str]:
    """Returns ordered preference list of difficulty tiers if target difficulty is exhausted."""
    diff = target_difficulty.upper() if target_difficulty else "MEDIUM"
    if diff == "HARD":
        return ["HARD", "MEDIUM", "EASY"]
    elif diff == "EASY":
        return ["EASY", "MEDIUM", "HARD"]
    else:
        return ["MEDIUM", "HARD", "EASY"]
