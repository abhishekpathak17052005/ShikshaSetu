"""Scoring formula for learning recommendations - deterministic 5-component model."""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from pymongo.database import Database

from .candidates import CandidateResource
from .provider import LearningResourceProvider


@dataclass
class ScoreComponent:
    """A single component of the recommendation score."""

    name: str  # "competency_match", "gap_priority", etc.
    weight: float  # 0.0 - 1.0
    score: float  # 0.0 - 1.0
    value: float  # weight * score


@dataclass
class RecommendationScore:
    """Complete scoring breakdown for a recommendation."""

    total_score: float  # 0.0 - 1.0
    components: List[ScoreComponent]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "total": self.total_score,
            "breakdown": [
                {
                    "name": c.name,
                    "weight": c.weight,
                    "score": c.score,
                    "value": c.value,
                }
                for c in self.components
            ],
        }


class ScoringFormula:
    """
    Deterministic 5-component scoring formula for recommendations.

    Components:
    - competency_match (40%): How well the resource covers the competency
    - gap_priority (25%): Priority of the gap based on size and importance
    - role_match (20%): How well the resource aligns with user's role
    - difficulty_match (10%): How well resource difficulty matches user level
    - prerequisite_match (5%): How many prerequisites user meets
    """

    # Default weights (configurable)
    WEIGHTS = {
        "competency_match": 0.40,
        "gap_priority": 0.25,
        "role_match": 0.20,
        "difficulty_match": 0.10,
        "prerequisite_match": 0.05,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """Initialize with optional custom weights."""
        self.weights = weights or self.WEIGHTS.copy()

        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total}: {self.weights}"
            )

    def score_candidate(
        self,
        candidate: CandidateResource,
        provider: LearningResourceProvider,
        user_current_level: Optional[float] = None,
        user_role: Optional[str] = None,
    ) -> RecommendationScore:
        """
        Calculate the overall recommendation score for a candidate resource.

        Args:
            candidate: The candidate resource
            provider: The resource provider
            user_current_level: User's current level for the competency
            user_role: User's role for role matching

        Returns:
            RecommendationScore with breakdown
        """

        # Calculate components
        competency_match = self._score_competency_match(candidate)
        gap_priority = self._score_gap_priority(candidate)
        role_match = self._score_role_match(candidate, provider, user_role)
        difficulty_match = self._score_difficulty_match(candidate, provider, user_current_level)
        prerequisite_match = self._score_prerequisite_match(candidate, provider)

        # Create component objects
        components = [
            ScoreComponent(
                name="competency_match",
                weight=self.weights["competency_match"],
                score=competency_match,
                value=competency_match * self.weights["competency_match"],
            ),
            ScoreComponent(
                name="gap_priority",
                weight=self.weights["gap_priority"],
                score=gap_priority,
                value=gap_priority * self.weights["gap_priority"],
            ),
            ScoreComponent(
                name="role_match",
                weight=self.weights["role_match"],
                score=role_match,
                value=role_match * self.weights["role_match"],
            ),
            ScoreComponent(
                name="difficulty_match",
                weight=self.weights["difficulty_match"],
                score=difficulty_match,
                value=difficulty_match * self.weights["difficulty_match"],
            ),
            ScoreComponent(
                name="prerequisite_match",
                weight=self.weights["prerequisite_match"],
                score=prerequisite_match,
                value=prerequisite_match * self.weights["prerequisite_match"],
            ),
        ]

        # Total score
        total_score = sum(c.value for c in components)

        return RecommendationScore(total_score=total_score, components=components)

    def _score_competency_match(self, candidate: CandidateResource) -> float:
        """
        Score competency match: how well the resource covers the competency.

        Uses the mapping confidence directly.
        Range: 0.0 - 1.0
        """
        return candidate.mapping_confidence

    def _score_gap_priority(self, candidate: CandidateResource) -> float:
        """
        Score gap priority: importance of addressing this gap.

        Uses the pre-calculated priority_score from skill gaps.
        Range: 0.0 - 1.0
        """
        return candidate.gap.get("priority_score", 0.5)

    def _score_role_match(
        self,
        candidate: CandidateResource,
        provider: LearningResourceProvider,
        user_role: Optional[str] = None,
    ) -> float:
        """
        Score role match: how well the resource aligns with the user's role.

        If role data unavailable: return 0.5 (neutral).
        Range: 0.0 - 1.0
        """
        if not user_role:
            return 0.5  # Neutral - no role specified

        role_match = provider.get_resource_role_match(candidate.resource, user_role)

        if role_match is None:
            return 0.5  # Neutral - no role matching data available

        return role_match

    def _score_difficulty_match(
        self,
        candidate: CandidateResource,
        provider: LearningResourceProvider,
        user_current_level: Optional[float] = None,
    ) -> float:
        """
        Score difficulty match: how well resource difficulty fits user level.

        Maps difficulty string to numeric level, compares to user's current level.
        If difficulty data unavailable: return 0.5 (neutral).
        Range: 0.0 - 1.0
        """
        difficulty = provider.get_resource_difficulty(candidate.resource)

        if difficulty is None:
            return 0.5  # Neutral - no difficulty data

        if user_current_level is None:
            return 0.5  # Neutral - no user level specified

        # Map difficulty to numeric level
        difficulty_map = {
            "Beginner": 1.0,
            "Intermediate": 2.5,
            "Advanced": 4.0,
        }

        resource_level = difficulty_map.get(difficulty)
        if resource_level is None:
            return 0.5  # Neutral - unknown difficulty

        # Score based on how well aligned resource level is to user level
        # Perfect match (same level): 1.0
        # Stretch goal (1-1.5 levels above): 0.8
        # Too easy (more than 1 level below): 0.6
        # Too hard (more than 1.5 levels above): 0.4

        level_diff = resource_level - user_current_level

        if abs(level_diff) <= 0.5:
            return 1.0  # Perfect match
        elif 0.5 < level_diff <= 1.5:
            return 0.8  # Good stretch goal
        elif -1.0 <= level_diff <= -0.5:
            return 0.6  # Too easy but close
        elif level_diff < -1.0:
            return 0.4  # Much too easy
        else:  # level_diff > 1.5
            return 0.4  # Too hard

    def _score_prerequisite_match(
        self, candidate: CandidateResource, provider: LearningResourceProvider
    ) -> float:
        """
        Score prerequisite match: how many prerequisites the user meets.

        If prerequisite data unavailable: return 0.5 (neutral).
        Range: 0.0 - 1.0
        """
        prerequisites = provider.get_resource_prerequisites(candidate.resource)

        if not prerequisites:
            return 0.5  # Neutral - no prerequisites or unknown

        # For prototype: no prerequisite verification data
        # Return neutral score (0.5)
        # In future: check user's completed resources/competencies
        return 0.5


class ScoringService:
    """Service to score and rank recommendations."""

    def __init__(self, formula: Optional[ScoringFormula] = None):
        """Initialize with optional custom scoring formula."""
        self.formula = formula if formula is not None else ScoringFormula()

    def score_candidates(
        self,
        candidates: List[CandidateResource],
        user_current_level: Optional[float] = None,
        user_role: Optional[str] = None,
    ) -> List[Tuple[CandidateResource, RecommendationScore]]:
        """
        Score a list of candidates.

        Returns list of (candidate, score) tuples.
        """
        scored = []

        for candidate in candidates:
            score = self.formula.score_candidate(
                candidate=candidate,
                provider=candidate.provider,
                user_current_level=user_current_level,
                user_role=user_role,
            )
            scored.append((candidate, score))

        return scored

    def rank_candidates(
        self,
        candidates: List[CandidateResource],
        user_current_level: Optional[float] = None,
        user_role: Optional[str] = None,
        descending: bool = True,
    ) -> List[Tuple[CandidateResource, RecommendationScore]]:
        """
        Score and rank candidates.

        Args:
            candidates: List of candidates
            user_current_level: User's current level
            user_role: User's role
            descending: If True, highest scores first (default)

        Returns:
            List of (candidate, score) tuples sorted by score
        """
        scored = self.score_candidates(candidates, user_current_level, user_role)

        # Sort by total_score
        scored.sort(
            key=lambda x: x[1].total_score, reverse=descending
        )

        return scored
