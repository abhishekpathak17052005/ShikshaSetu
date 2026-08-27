"""
Unit tests for skill gap calculation engine (pure logic, no database/HTTP).

Tests the deterministic gap calculation, categorization, and ranking.
"""

import pytest

from app.skill_gaps import engine


class TestGapCalculation:
    """Test basic gap calculation: gap = required - current."""

    def test_gap_when_current_below_required(self) -> None:
        """Normal case: employee below role requirement."""
        gap = engine.calculate_gap(required_level=4.0, current_level=2.63)
        assert gap == 1.37

    def test_gap_when_current_equals_required(self) -> None:
        """No gap when current equals required."""
        gap = engine.calculate_gap(required_level=3.0, current_level=3.0)
        assert gap == 0.0

    def test_gap_when_current_above_required(self) -> None:
        """No gap when current exceeds required (clamped to zero)."""
        gap = engine.calculate_gap(required_level=3.0, current_level=3.5)
        assert gap == 0.0

    def test_gap_when_not_assessed(self) -> None:
        """Unassessed competency treated as zero (full gap)."""
        gap = engine.calculate_gap(required_level=2.0, current_level=None)
        assert gap == 2.0

    def test_gap_at_extremes(self) -> None:
        """Test minimum and maximum gaps."""
        # Minimum: current at 5, required at 1
        gap = engine.calculate_gap(required_level=1.0, current_level=5.0)
        assert gap == 0.0  # Clamped
        
        # Maximum: current at 0 (not assessed), required at 5
        gap = engine.calculate_gap(required_level=5.0, current_level=None)
        assert gap == 5.0
        
        # Maximum realistic: current at 1, required at 5
        gap = engine.calculate_gap(required_level=5.0, current_level=1.0)
        assert gap == 4.0

    def test_invalid_required_level_raises_error(self) -> None:
        """Required level must be between 1 and 5."""
        with pytest.raises(ValueError, match="required_level must be between 1 and 5"):
            engine.calculate_gap(required_level=0.5, current_level=2.0)
        
        with pytest.raises(ValueError, match="required_level must be between 1 and 5"):
            engine.calculate_gap(required_level=5.5, current_level=2.0)

    def test_invalid_current_level_raises_error(self) -> None:
        """Current level must be between 1 and 5 (or None)."""
        with pytest.raises(ValueError, match="current_level must be between 1 and 5"):
            engine.calculate_gap(required_level=3.0, current_level=0.5)
        
        with pytest.raises(ValueError, match="current_level must be between 1 and 5"):
            engine.calculate_gap(required_level=3.0, current_level=5.5)


class TestGapCategorization:
    """Test gap categorization into NO_GAP, LOW, MEDIUM, HIGH, CRITICAL."""

    def test_no_gap_boundary(self) -> None:
        """Gap 0.00 is NO_GAP."""
        assert engine.categorize_gap(0.00) == "NO_GAP"

    def test_low_gap_boundaries(self) -> None:
        """LOW: 0.01 to 0.50."""
        assert engine.categorize_gap(0.01) == "LOW"
        assert engine.categorize_gap(0.25) == "LOW"
        assert engine.categorize_gap(0.50) == "LOW"

    def test_medium_gap_boundaries(self) -> None:
        """MEDIUM: 0.51 to 1.00."""
        assert engine.categorize_gap(0.51) == "MEDIUM"
        assert engine.categorize_gap(0.75) == "MEDIUM"
        assert engine.categorize_gap(1.00) == "MEDIUM"

    def test_high_gap_boundaries(self) -> None:
        """HIGH: 1.01 to 1.50."""
        assert engine.categorize_gap(1.01) == "HIGH"
        assert engine.categorize_gap(1.25) == "HIGH"
        assert engine.categorize_gap(1.50) == "HIGH"

    def test_critical_gap_boundaries(self) -> None:
        """CRITICAL: 1.51 to 4.00."""
        assert engine.categorize_gap(1.51) == "CRITICAL"
        assert engine.categorize_gap(2.50) == "CRITICAL"
        assert engine.categorize_gap(4.00) == "CRITICAL"

    def test_gap_boundary_transitions(self) -> None:
        """Test exact transitions between categories."""
        # 0.00 → NO_GAP, 0.01 → LOW
        assert engine.categorize_gap(0.00) == "NO_GAP"
        assert engine.categorize_gap(0.01) == "LOW"
        
        # 0.50 → LOW, 0.51 → MEDIUM
        assert engine.categorize_gap(0.50) == "LOW"
        assert engine.categorize_gap(0.51) == "MEDIUM"
        
        # 1.00 → MEDIUM, 1.01 → HIGH
        assert engine.categorize_gap(1.00) == "MEDIUM"
        assert engine.categorize_gap(1.01) == "HIGH"
        
        # 1.50 → HIGH, 1.51 → CRITICAL
        assert engine.categorize_gap(1.50) == "HIGH"
        assert engine.categorize_gap(1.51) == "CRITICAL"

    def test_invalid_gap_raises_error(self) -> None:
        """Gap must be between 0 and 4."""
        with pytest.raises(ValueError, match="gap must be between 0 and 4.0"):
            engine.categorize_gap(-0.1)
        
        with pytest.raises(ValueError, match="gap must be between 0 and 4.0"):
            engine.categorize_gap(4.1)


class TestAssessmentStatus:
    """Test assessment status determination."""

    def test_assessed_when_current_level_provided(self) -> None:
        """ASSESSED when current_level is not None."""
        assert engine.get_assessment_status(2.5) == "ASSESSED"
        assert engine.get_assessment_status(1.0) == "ASSESSED"
        assert engine.get_assessment_status(5.0) == "ASSESSED"

    def test_not_assessed_when_current_level_none(self) -> None:
        """NOT_ASSESSED when current_level is None."""
        assert engine.get_assessment_status(None) == "NOT_ASSESSED"


class TestPriorityScore:
    """Test deterministic priority score calculation."""

    def test_priority_score_formula(self) -> None:
        """Priority score = normalized_gap × 0.60 + normalized_importance × 0.25 + normalized_priority × 0.15."""
        # High gap, high importance, high priority (1)
        score = engine.calculate_priority_score(
            gap=4.0,
            importance=1.0,
            role_priority=1,
        )
        # normalized_gap = 4/4 = 1.0
        # normalized_importance = 1.0
        # normalized_priority = 1.0 - (0 / 3) = 1.0
        # score = 1.0 * 0.60 + 1.0 * 0.25 + 1.0 * 0.15 = 1.0
        assert score == 1.0

    def test_priority_score_low_everything(self) -> None:
        """Low gap, low importance, low priority (4)."""
        score = engine.calculate_priority_score(
            gap=0.0,
            importance=0.0,
            role_priority=4,
        )
        # normalized_gap = 0 / 4 = 0.0
        # normalized_importance = 0.0
        # normalized_priority = 1.0 - (3 / 3) = 0.0
        # score = 0.0 * 0.60 + 0.0 * 0.25 + 0.0 * 0.15 = 0.0
        assert score == 0.0

    def test_priority_score_realistic_case(self) -> None:
        """Realistic case: SQL gap 0.9, importance 0.75, priority 2."""
        score = engine.calculate_priority_score(
            gap=0.9,
            importance=0.75,
            role_priority=2,
        )
        # normalized_gap = 0.9 / 4 = 0.225
        # normalized_importance = 0.75
        # normalized_priority = 1.0 - (1 / 3) = 0.667
        # score = 0.225 * 0.60 + 0.75 * 0.25 + 0.667 * 0.15
        # score = 0.135 + 0.1875 + 0.1 = 0.4225 ≈ 0.42
        assert round(score, 2) == 0.42

    def test_priority_score_invalid_inputs(self) -> None:
        """Invalid inputs raise errors."""
        with pytest.raises(ValueError, match="gap must be between 0 and"):
            engine.calculate_priority_score(gap=-1.0, importance=0.5, role_priority=2)
        
        with pytest.raises(ValueError, match="importance must be between 0 and 1"):
            engine.calculate_priority_score(gap=1.0, importance=1.5, role_priority=2)
        
        with pytest.raises(ValueError, match="role_priority must be between 1 and"):
            engine.calculate_priority_score(gap=1.0, importance=0.5, role_priority=0)


class TestBuildGapItem:
    """Test building a complete gap item with all calculations."""

    def test_gap_item_with_assessed_competency(self) -> None:
        """Complete gap item for an assessed competency."""
        item = engine.build_gap_item(
            competency_id="abc123",
            competency_code="STAT_SAMPLING",
            competency_name="Sampling",
            domain="STATISTICAL",
            required_level=4.0,
            current_level=2.63,
            role_priority=1,
            importance=1.0,
            confidence=0.80,
            last_assessed_at=None,
        )
        
        assert item["competency_id"] == "abc123"
        assert item["competency_code"] == "STAT_SAMPLING"
        assert item["competency_name"] == "Sampling"
        assert item["domain"] == "STATISTICAL"
        assert item["required_level"] == 4.0
        assert item["current_level"] == 2.63
        assert item["gap"] == 1.37
        assert item["gap_category"] == "HIGH"
        assert item["assessment_status"] == "ASSESSED"
        assert item["confidence"] == 0.80
        assert item["priority"] == 1
        assert item["importance"] == 1.0
        assert item["priority_score"] > 0  # Specific value depends on formula

    def test_gap_item_with_unassessed_competency(self) -> None:
        """Gap item for an unassessed competency."""
        item = engine.build_gap_item(
            competency_id="xyz789",
            competency_code="TECH_GIS",
            competency_name="GIS",
            domain="TECHNICAL",
            required_level=2.0,
            current_level=None,
            role_priority=3,
            importance=0.5,
        )
        
        assert item["current_level"] is None
        assert item["gap"] == 2.0
        assert item["gap_category"] == "CRITICAL"
        assert item["assessment_status"] == "NOT_ASSESSED"
        assert item["confidence"] == 0.0

    def test_gap_item_with_no_gap(self) -> None:
        """Gap item when employee exceeds requirement."""
        item = engine.build_gap_item(
            competency_id="def456",
            competency_code="TECH_PYTHON",
            competency_name="Python",
            domain="TECHNICAL",
            required_level=3.0,
            current_level=3.40,
            role_priority=2,
            importance=0.75,
            confidence=1.0,
        )
        
        assert item["gap"] == 0.0
        assert item["gap_category"] == "NO_GAP"
        assert item["assessment_status"] == "ASSESSED"


class TestSortGaps:
    """Test deterministic gap sorting by priority."""

    def test_sort_by_priority_score_descending(self) -> None:
        """Gaps sorted by priority_score DESC (highest first)."""
        gaps = [
            {"priority_score": 0.3, "gap": 1.0, "importance": 0.5, "priority": 3, "competency_code": "B"},
            {"priority_score": 0.8, "gap": 2.0, "importance": 1.0, "priority": 1, "competency_code": "A"},
            {"priority_score": 0.5, "gap": 1.5, "importance": 0.75, "priority": 2, "competency_code": "C"},
        ]
        
        sorted_gaps = engine.sort_gaps(gaps)
        
        assert sorted_gaps[0]["priority_score"] == 0.8  # Highest first
        assert sorted_gaps[1]["priority_score"] == 0.5
        assert sorted_gaps[2]["priority_score"] == 0.3

    def test_sort_tie_breaking_by_gap_size(self) -> None:
        """When priority_score ties, larger gap first."""
        gaps = [
            {"priority_score": 0.5, "gap": 0.8, "importance": 0.5, "priority": 2, "competency_code": "B"},
            {"priority_score": 0.5, "gap": 1.2, "importance": 0.5, "priority": 2, "competency_code": "A"},
        ]
        
        sorted_gaps = engine.sort_gaps(gaps)
        
        assert sorted_gaps[0]["gap"] == 1.2
        assert sorted_gaps[1]["gap"] == 0.8

    def test_sort_tie_breaking_by_importance(self) -> None:
        """When priority_score and gap tie, higher importance first."""
        gaps = [
            {"priority_score": 0.5, "gap": 1.0, "importance": 0.5, "priority": 2, "competency_code": "B"},
            {"priority_score": 0.5, "gap": 1.0, "importance": 0.75, "priority": 2, "competency_code": "A"},
        ]
        
        sorted_gaps = engine.sort_gaps(gaps)
        
        assert sorted_gaps[0]["importance"] == 0.75
        assert sorted_gaps[1]["importance"] == 0.5

    def test_sort_tie_breaking_by_role_priority(self) -> None:
        """When priority_score, gap, importance tie, lower priority value first (1 > 2 > 3 > 4)."""
        gaps = [
            {"priority_score": 0.5, "gap": 1.0, "importance": 0.75, "priority": 2, "competency_code": "B"},
            {"priority_score": 0.5, "gap": 1.0, "importance": 0.75, "priority": 1, "competency_code": "A"},
        ]
        
        sorted_gaps = engine.sort_gaps(gaps)
        
        assert sorted_gaps[0]["priority"] == 1
        assert sorted_gaps[1]["priority"] == 2

    def test_sort_tie_breaking_by_code(self) -> None:
        """Final tie-breaker: competency code alphabetically."""
        gaps = [
            {"priority_score": 0.5, "gap": 1.0, "importance": 0.75, "priority": 1, "competency_code": "STAT_Z"},
            {"priority_score": 0.5, "gap": 1.0, "importance": 0.75, "priority": 1, "competency_code": "STAT_A"},
        ]
        
        sorted_gaps = engine.sort_gaps(gaps)
        
        assert sorted_gaps[0]["competency_code"] == "STAT_A"
        assert sorted_gaps[1]["competency_code"] == "STAT_Z"

    def test_realistic_gap_sorting(self) -> None:
        """Realistic example with multiple gaps."""
        gaps = [
            engine.build_gap_item(
                competency_id="1",
                competency_code="STAT_SAMPLING",
                competency_name="Sampling",
                domain="STATISTICAL",
                required_level=4.0,
                current_level=2.63,
                role_priority=1,
                importance=1.0,
                confidence=0.8,
            ),
            engine.build_gap_item(
                competency_id="2",
                competency_code="TECH_SQL",
                competency_name="SQL",
                domain="TECHNICAL",
                required_level=3.0,
                current_level=2.10,
                role_priority=2,
                importance=0.75,
                confidence=0.7,
            ),
            engine.build_gap_item(
                competency_id="3",
                competency_code="TECH_PYTHON",
                competency_name="Python",
                domain="TECHNICAL",
                required_level=3.0,
                current_level=3.40,
                role_priority=2,
                importance=0.75,
                confidence=1.0,
            ),
        ]
        
        sorted_gaps = engine.sort_gaps(gaps)
        
        # Sampling should be first (high gap, high importance, high priority)
        assert sorted_gaps[0]["competency_code"] == "STAT_SAMPLING"
        # SQL should be second (medium gap)
        assert sorted_gaps[1]["competency_code"] == "TECH_SQL"
        # Python should be last (no gap)
        assert sorted_gaps[2]["competency_code"] == "TECH_PYTHON"


class TestCalculateSummary:
    """Test summary statistics calculation."""

    def test_summary_with_mixed_gaps(self) -> None:
        """Summary correctly counts gaps by category."""
        gaps = [
            {"gap_category": "NO_GAP", "assessment_status": "ASSESSED"},
            {"gap_category": "NO_GAP", "assessment_status": "ASSESSED"},
            {"gap_category": "LOW", "assessment_status": "ASSESSED"},
            {"gap_category": "MEDIUM", "assessment_status": "ASSESSED"},
            {"gap_category": "HIGH", "assessment_status": "ASSESSED"},
            {"gap_category": "CRITICAL", "assessment_status": "ASSESSED"},
            {"gap_category": "CRITICAL", "assessment_status": "NOT_ASSESSED"},
        ]
        
        summary = engine.calculate_summary(gaps)
        
        assert summary["required_competencies"] == 7
        assert summary["total_gaps"] == 5  # All except NO_GAP
        assert summary["no_gap_count"] == 2
        assert summary["not_assessed_count"] == 1
        assert summary["critical_gaps"] == 2
        assert summary["high_gaps"] == 1
        assert summary["medium_gaps"] == 1
        assert summary["low_gaps"] == 1

    def test_summary_with_all_gaps(self) -> None:
        """Summary when all competencies have gaps."""
        gaps = [
            {"gap_category": "HIGH", "assessment_status": "ASSESSED"},
            {"gap_category": "MEDIUM", "assessment_status": "ASSESSED"},
        ]
        
        summary = engine.calculate_summary(gaps)
        
        assert summary["required_competencies"] == 2
        assert summary["total_gaps"] == 2
        assert summary["no_gap_count"] == 0
        assert summary["not_assessed_count"] == 0

    def test_summary_with_no_gaps(self) -> None:
        """Summary when all competencies are mastered."""
        gaps = [
            {"gap_category": "NO_GAP", "assessment_status": "ASSESSED"},
            {"gap_category": "NO_GAP", "assessment_status": "ASSESSED"},
            {"gap_category": "NO_GAP", "assessment_status": "ASSESSED"},
        ]
        
        summary = engine.calculate_summary(gaps)
        
        assert summary["required_competencies"] == 3
        assert summary["total_gaps"] == 0
        assert summary["no_gap_count"] == 3
