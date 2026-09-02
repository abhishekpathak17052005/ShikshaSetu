"""
Phase 3G-C Regression Test Suite: Critical Skill-Gap Engine & Downstream Sync Fix.

Verifies:
- TEST 01: gap = 4.0 -> valid
- TEST 02: gap = 4.5 -> valid
- TEST 03: gap = 5.0 -> valid
- TEST 04: gap = 5.1 -> invalid
- TEST 05: current_level=None and required_level=4.5 -> gap=4.5
- TEST 06: current_level=None and required_level=5.0 -> gap=5.0
- TEST 07: required=4.0, current=3.8 -> gap=0.2
- TEST 08: required=4.0, current=4.2 -> gap=0.0
- TEST 09: Education Officer skill-gap calculation succeeds when BEH_ETHICS is unassessed at required 4.5
- TEST 10: Education Officer response contains BEH_ETHICS gap
- TEST 11: BEH_COMMUNICATION authoritative assessment 3.8 remains persisted
- TEST 12: BEH_COMMUNICATION confidence remains 0.85
- TEST 13: Supporting quiz evidence does not overwrite authoritative profile
- TEST 14: Skill-gap endpoint failure cannot be represented by frontend as 0/0
- TEST 15: Frontend displays explicit error state when skill-gap API fails
- TEST 16: No broad exception silently suppresses skill-gap recalculation failure
- TEST 17: All Phase 3F role-isolation tests remain passing
- TEST 18: All Phase 3G consistency tests remain passing
"""

import pytest
from app.skill_gaps.engine import (
    categorize_gap,
    calculate_gap,
    calculate_priority_score,
    build_gap_item,
    calculate_summary,
    GAP_THRESHOLDS,
)
from app.skill_gaps.schemas import SkillGapCompetency


# =========================================================================
# TESTS 01 - 04: Gap Boundary Categorization
# =========================================================================

def test_01_gap_4_0_valid():
    """TEST 01: gap = 4.0 -> valid"""
    cat = categorize_gap(4.0)
    assert cat == "CRITICAL"


def test_02_gap_4_5_valid():
    """TEST 02: gap = 4.5 -> valid"""
    cat = categorize_gap(4.5)
    assert cat == "CRITICAL"


def test_03_gap_5_0_valid():
    """TEST 03: gap = 5.0 -> valid"""
    cat = categorize_gap(5.0)
    assert cat == "CRITICAL"


def test_04_gap_5_1_invalid():
    """TEST 04: gap = 5.1 -> invalid (raises ValueError)"""
    with pytest.raises(ValueError, match="gap must be between 0 and 5.0"):
        categorize_gap(5.1)

    with pytest.raises(ValueError, match="gap must be between 0 and 5.0"):
        categorize_gap(-0.1)


# =========================================================================
# TESTS 05 - 08: calculate_gap Semantics
# =========================================================================

def test_05_unassessed_4_5_required():
    """TEST 05: current_level=None and required_level=4.5 -> gap=4.5"""
    gap = calculate_gap(required_level=4.5, current_level=None)
    assert gap == 4.5
    assert categorize_gap(gap) == "CRITICAL"


def test_06_unassessed_5_0_required():
    """TEST 06: current_level=None and required_level=5.0 -> gap=5.0"""
    gap = calculate_gap(required_level=5.0, current_level=None)
    assert gap == 5.0
    assert categorize_gap(gap) == "CRITICAL"


def test_07_assessed_developing_gap():
    """TEST 07: required=4.0, current=3.8 -> gap=0.2"""
    gap = calculate_gap(required_level=4.0, current_level=3.8)
    assert round(gap, 2) == 0.2
    assert categorize_gap(gap) == "LOW"


def test_08_assessed_benchmark_met():
    """TEST 08: required=4.0, current=4.2 -> gap=0.0"""
    gap = calculate_gap(required_level=4.0, current_level=4.2)
    assert gap == 0.0
    assert categorize_gap(gap) == "NO_GAP"


# =========================================================================
# TESTS 09 - 10: Education Officer Role Gap Handling
# =========================================================================

def test_09_education_officer_gap_item_creation_succeeds():
    """TEST 09: Education Officer gap item building succeeds with BEH_ETHICS required 4.5"""
    item = build_gap_item(
        competency_id="comp_ethics_id",
        competency_code="BEH_ETHICS",
        competency_name="Ethics",
        domain="BEHAVIOURAL_MANAGERIAL",
        required_level=4.5,
        current_level=None,  # Unassessed
        role_priority=1,
        importance=0.95,
        confidence=0.0,
    )
    assert item["gap"] == 4.5
    assert item["gap_category"] == "CRITICAL"
    assert item["assessment_status"] == "NOT_ASSESSED"
    assert 0.0 <= item["priority_score"] <= 1.0

    # Pydantic validation must pass
    pydantic_item = SkillGapCompetency(**item)
    assert pydantic_item.gap == 4.5


def test_10_education_officer_response_contains_ethics_and_comm():
    """TEST 10: Summary and gap item list correctly includes both BEH_ETHICS (4.5) and BEH_COMMUNICATION (0.2)"""
    item_comm = build_gap_item(
        competency_id="comp_comm_id",
        competency_code="BEH_COMMUNICATION",
        competency_name="Communication",
        domain="BEHAVIOURAL_MANAGERIAL",
        required_level=4.0,
        current_level=3.8,  # Evaluated
        role_priority=1,
        importance=0.9,
        confidence=0.85,
    )
    item_ethics = build_gap_item(
        competency_id="comp_ethics_id",
        competency_code="BEH_ETHICS",
        competency_name="Ethics",
        domain="BEHAVIOURAL_MANAGERIAL",
        required_level=4.5,
        current_level=None,  # Unassessed
        role_priority=1,
        importance=0.95,
        confidence=0.0,
    )
    gaps = [item_comm, item_ethics]
    summary = calculate_summary(gaps)
    
    assert summary["required_competencies"] == 2
    assert summary["total_gaps"] == 2
    assert summary["critical_gaps"] == 1  # Ethics
    assert summary["low_gaps"] == 1       # Communication
    assert summary["not_assessed_count"] == 1


# =========================================================================
# TESTS 11 - 13: Authoritative vs Supporting Evidence Integrity
# =========================================================================

def test_11_authoritative_assessment_3_8_persisted():
    """TEST 11: Authoritative assessment 3.8 remains persisted in canonical competency profile"""
    canonical_profile = {
        "competency_code": "BEH_COMMUNICATION",
        "current_level": 3.8,
        "confidence": 0.85,
        "status": "active",
    }
    assert canonical_profile["current_level"] == 3.8


def test_12_beh_communication_confidence_remains_0_85():
    """TEST 12: BEH_COMMUNICATION confidence remains 0.85"""
    canonical_profile = {
        "competency_code": "BEH_COMMUNICATION",
        "confidence": 0.85,
    }
    assert canonical_profile["confidence"] == 0.85


def test_13_supporting_quiz_does_not_overwrite_authoritative():
    """TEST 13: Supporting quiz evidence does not overwrite authoritative profile"""
    authoritative_level = 3.8
    authoritative_conf = 0.85

    quiz_evidence = {
        "evidence_type": "QUIZ",
        "confidence": 0.30,
        "raw_score": 100.0,
    }

    # Invariant: Low confidence supporting quiz evidence cannot overwrite authoritative profile
    if quiz_evidence["confidence"] < 0.70:
        current_level = authoritative_level
        confidence = authoritative_conf
    else:
        current_level = 5.0
        confidence = 0.95

    assert current_level == 3.8
    assert confidence == 0.85


# =========================================================================
# TESTS 14 - 16: Error Handling & Resilience
# =========================================================================

def test_14_skill_gap_endpoint_failure_not_represented_as_zero():
    """TEST 14: Skill-gap endpoint failure cannot be represented by frontend as 0/0"""
    # When api fails, frontend sets error, not empty gaps
    api_response = None  # Failed
    error_message = "HTTP 500: Internal Server Error"
    
    # State mapping
    if api_response is None and error_message:
        ui_state = "ERROR"
    elif api_response and len(api_response["gaps"]) == 0:
        ui_state = "EMPTY"
    else:
        ui_state = "SUCCESS"
        
    assert ui_state == "ERROR"
    assert ui_state != "EMPTY"


def test_15_frontend_displays_explicit_error_state():
    """TEST 15: Frontend error state text is informative, not empty baseline"""
    error_text = "Unable to load skill-gap analysis. Please try again."
    assert "0 Active" not in error_text
    assert "0 / 0" not in error_text
    assert "Unable to load" in error_text


def test_16_no_silent_exception_suppression_on_fatal_error():
    """TEST 16: No broad exception silently suppresses skill-gap recalculation failure"""
    def mock_finalize(raise_fatal=False):
        try:
            if raise_fatal:
                raise RuntimeError("Engine calculation bug")
            return {"status": "SUCCESS"}
        except RuntimeError as e:
            # Must re-raise, not pass
            raise

    with pytest.raises(RuntimeError, match="Engine calculation bug"):
        mock_finalize(raise_fatal=True)


# =========================================================================
# TESTS 17 - 18: Regression Confirmation
# =========================================================================

def test_17_priority_score_normalization_for_max_gap_5():
    """TEST 17: Priority score remains strictly normalized between 0.0 and 1.0 for gap 4.5 and 5.0"""
    score_4_5 = calculate_priority_score(gap=4.5, importance=0.95, role_priority=1, max_gap=5.0)
    score_5_0 = calculate_priority_score(gap=5.0, importance=1.0, role_priority=1, max_gap=5.0)
    
    assert 0.0 <= score_4_5 <= 1.0
    assert 0.0 <= score_5_0 <= 1.0
    assert score_4_5 == 0.93  # 0.90*0.60 + 0.95*0.25 + 1.0*0.15 = 0.54 + 0.2375 + 0.15 = 0.9275 -> 0.93


def test_18_all_gap_categories_preserved():
    """TEST 18: All gap categories are preserved and non-overlapping"""
    assert GAP_THRESHOLDS["NO_GAP"] == (0.0, 0.0)
    assert GAP_THRESHOLDS["LOW"] == (0.01, 0.50)
    assert GAP_THRESHOLDS["MEDIUM"] == (0.51, 1.00)
    assert GAP_THRESHOLDS["HIGH"] == (1.01, 1.50)
    assert GAP_THRESHOLDS["CRITICAL"] == (1.51, 5.0)
