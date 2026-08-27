import pytest

from app.assessments.schemas import AssessmentScoringConfig
from app.assessments.scoring import prototype_confidence, score_ratio, weighted_competency_score


def test_score_ratio_uses_prototype_boundaries() -> None:
    assert [score_ratio(value) for value in (0, 0.19, 0.20, 0.39, 0.40, 0.59, 0.60, 0.79, 0.80, 1)] == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_weighted_score_matches_documented_example() -> None:
    config = AssessmentScoringConfig()

    assert weighted_competency_score({"self_assessment": 3, "knowledge_test": 2, "scenario_test": 4, "training_evidence": 3}, config) == 2.9


def test_missing_components_are_renormalized_and_confidence_tracks_coverage() -> None:
    config = AssessmentScoringConfig()

    assert weighted_competency_score({"self_assessment": 3, "knowledge_test": None, "scenario_test": None, "training_evidence": None}, config) == 3
    assert prototype_confidence({"self_assessment": 3, "knowledge_test": None, "scenario_test": None, "training_evidence": None}, config) == 0.2
    assert prototype_confidence({"self_assessment": 3, "knowledge_test": 2, "scenario_test": 4, "training_evidence": 3}, config) == 1.0


def test_invalid_weights_and_scores_are_rejected() -> None:
    with pytest.raises(ValueError):
        AssessmentScoringConfig(self_assessment_weight=0, knowledge_test_weight=0, scenario_test_weight=0, training_evidence_weight=0)
    with pytest.raises(ValueError):
        score_ratio(1.1)
    with pytest.raises(ValueError):
        weighted_competency_score({}, AssessmentScoringConfig())
