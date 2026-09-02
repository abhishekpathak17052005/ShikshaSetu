"""
Pure skill gap calculation engine.

Deterministic, testable, independent of FastAPI/MongoDB.
"""

from collections.abc import Mapping


# Gap category thresholds (ShikshaSetu prototype)
GAP_THRESHOLDS = {
    "NO_GAP": (0.0, 0.0),
    "LOW": (0.01, 0.50),
    "MEDIUM": (0.51, 1.00),
    "HIGH": (1.01, 1.50),
    "CRITICAL": (1.51, 5.0),
}


def categorize_gap(gap: float) -> str:
    """
    Categorize a gap into NO_GAP, LOW, MEDIUM, HIGH, or CRITICAL.
    
    Args:
        gap: Gap size (0.0 to 5.0)
    
    Returns:
        Gap category as string
    
    Raises:
        ValueError: If gap is negative or > 5.0
    """
    if gap < 0 or gap > 5.0:
        raise ValueError(f"gap must be between 0 and 5.0, got {gap}")
    
    for category, (min_val, max_val) in GAP_THRESHOLDS.items():
        if min_val <= gap <= max_val:
            return category
    
    raise ValueError(f"Gap {gap} does not match any category")


def calculate_gap(required_level: float, current_level: float | None) -> float:
    """
    Calculate skill gap.
    
    Gap = Required - Current
    
    If current >= required, gap = 0.
    
    Args:
        required_level: Required competency level (1.0-5.0)
        current_level: Current competency level (1.0-5.0) or None if not assessed
    
    Returns:
        Gap (0.0 to 5.0)
    
    Raises:
        ValueError: If required_level is invalid
    """
    if required_level < 1 or required_level > 5:
        raise ValueError(f"required_level must be between 1 and 5, got {required_level}")
    
    if current_level is None:
        # Not assessed: treat as zero for gap calculation (gap equals full required level)
        return required_level
    
    if current_level < 1 or current_level > 5:
        raise ValueError(f"current_level must be between 1 and 5, got {current_level}")
    
    gap = required_level - current_level
    
    # Never return negative gap
    return max(0.0, gap)


def calculate_priority_score(
    gap: float,
    importance: float,
    role_priority: int,
    max_gap: float = 4.0,
    max_priority: int = 4,
) -> float:
    """
    Calculate priority score for gap ranking.
    
    Uses weighted formula:
    priority_score = normalized_gap × 0.60 + normalized_importance × 0.25 + normalized_priority × 0.15
    
    Args:
        gap: Gap size (0.0-5.0)
        importance: Importance weight (0.0-1.0)
        role_priority: Role requirement priority (1-4, where 1 is highest)
        max_gap: Normalization gap reference (default 4.0)
        max_priority: Maximum priority value (default 4)
    
    Returns:
        Priority score (0.0-1.0)
    
    Raises:
        ValueError: If inputs are invalid
    """
    if gap < 0 or gap > 5.0:
        raise ValueError(f"gap must be between 0 and 5.0, got {gap}")
    if importance < 0 or importance > 1:
        raise ValueError(f"importance must be between 0 and 1, got {importance}")
    if role_priority < 1 or role_priority > max_priority:
        raise ValueError(f"role_priority must be between 1 and {max_priority}, got {role_priority}")
    
    # Normalize gap (0 gap → 0, max gap 4.0+ → 1.0 clamped)
    normalized_gap = min(1.0, gap / max_gap) if max_gap > 0 else 0
    
    # Importance already normalized (0.0-1.0)
    normalized_importance = importance
    
    # Normalize priority (1 → 1.0, max → 0.0)
    normalized_priority = 1.0 - ((role_priority - 1) / (max_priority - 1))
    
    # Weighted combination
    priority_score = (
        normalized_gap * 0.60
        + normalized_importance * 0.25
        + normalized_priority * 0.15
    )
    
    return round(priority_score, 2)


def get_assessment_status(current_level: float | None) -> str:
    """
    Determine assessment status.
    
    Args:
        current_level: Current competency level or None
    
    Returns:
        ASSESSED or NOT_ASSESSED
    """
    return "ASSESSED" if current_level is not None else "NOT_ASSESSED"


def build_gap_item(
    competency_id: str,
    competency_code: str,
    competency_name: str,
    domain: str,
    required_level: float,
    current_level: float | None,
    role_priority: int,
    importance: float,
    confidence: float = 0.0,
    last_assessed_at = None,
) -> dict:
    """
    Build a complete gap item with all calculations.
    
    Args:
        competency_id: MongoDB competency ID
        competency_code: Competency code (e.g., STAT_SAMPLING)
        competency_name: Competency name (e.g., Sampling)
        domain: Domain (STATISTICAL, TECHNICAL, etc.)
        required_level: Required level for role (1.0-5.0)
        current_level: Current demonstrated level or None
        role_priority: Role requirement priority (1-4)
        importance: Role requirement importance (0.0-1.0)
        confidence: Assessment confidence (0.0-1.0, default 0)
        last_assessed_at: Timestamp of last assessment
    
    Returns:
        Complete gap item dict
    """
    gap = calculate_gap(required_level, current_level)
    gap_category = categorize_gap(gap)
    assessment_status = get_assessment_status(current_level)
    priority_score = calculate_priority_score(gap, importance, role_priority)
    
    return {
        "competency_id": competency_id,
        "competency_code": competency_code,
        "competency_name": competency_name,
        "domain": domain,
        "required_level": required_level,
        "current_level": current_level,
        "gap": round(gap, 2),
        "gap_category": gap_category,
        "assessment_status": assessment_status,
        "confidence": confidence,
        "priority": role_priority,
        "importance": importance,
        "priority_score": priority_score,
        "last_assessed_at": last_assessed_at,
    }


def sort_gaps(gaps: list[dict]) -> list[dict]:
    """
    Sort gaps by priority (highest first), with tie-breaking.
    
    Primary: priority_score DESC (highest first)
    Secondary: gap DESC (largest first)
    Tertiary: importance DESC (most important first)
    Tertiary: priority ASC (lowest priority value first = highest priority)
    Quaternary: competency_code ASC (stable ordering)
    
    Args:
        gaps: List of gap items
    
    Returns:
        Sorted list (highest priority first)
    """
    return sorted(
        gaps,
        key=lambda g: (
            -g["priority_score"],  # Higher score first
            -g["gap"],             # Larger gap first
            -g["importance"],      # Higher importance first
            g["priority"],         # Lower priority value first (1=highest)
            g["competency_code"],  # Stable alphabetical ordering
        ),
    )


def calculate_summary(gaps: list[dict]) -> dict:
    """
    Calculate summary statistics for gaps.
    
    Args:
        gaps: List of gap items
    
    Returns:
        Summary dict with counts
    """
    no_gap_count = sum(1 for g in gaps if g["gap_category"] == "NO_GAP")
    not_assessed_count = sum(1 for g in gaps if g["assessment_status"] == "NOT_ASSESSED")
    critical_gaps = sum(1 for g in gaps if g["gap_category"] == "CRITICAL")
    high_gaps = sum(1 for g in gaps if g["gap_category"] == "HIGH")
    medium_gaps = sum(1 for g in gaps if g["gap_category"] == "MEDIUM")
    low_gaps = sum(1 for g in gaps if g["gap_category"] == "LOW")
    total_gaps = critical_gaps + high_gaps + medium_gaps + low_gaps
    
    return {
        "required_competencies": len(gaps),
        "total_gaps": total_gaps,
        "no_gap_count": no_gap_count,
        "not_assessed_count": not_assessed_count,
        "critical_gaps": critical_gaps,
        "high_gaps": high_gaps,
        "medium_gaps": medium_gaps,
        "low_gaps": low_gaps,
    }
