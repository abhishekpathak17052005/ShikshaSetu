from collections.abc import Mapping

from app.assessments.schemas import AssessmentScoringConfig


def score_ratio(ratio: float) -> float:
    if ratio < 0 or ratio > 1:
        raise ValueError("ratio must be between 0 and 1")
    if ratio < 0.20:
        return 1.0
    if ratio < 0.40:
        return 2.0
    if ratio < 0.60:
        return 3.0
    if ratio < 0.80:
        return 4.0
    return 5.0


def weighted_competency_score(
    components: Mapping[str, float | None],
    config: AssessmentScoringConfig,
) -> float:
    component_weights = {
        "self_assessment": config.self_assessment_weight,
        "knowledge_test": config.knowledge_test_weight,
        "scenario_test": config.scenario_test_weight,
        "training_evidence": config.training_evidence_weight,
    }
    available = [
        (score, component_weights[name])
        for name, score in components.items()
        if score is not None and component_weights.get(name, 0) > 0
    ]
    if not available:
        raise ValueError("at least one weighted evidence component is required")
    total_weight = sum(weight for _, weight in available)
    return round(sum(score * weight for score, weight in available) / total_weight, 2)


def prototype_confidence(components: Mapping[str, float | None], config: AssessmentScoringConfig) -> float:
    weights = {
        "self_assessment": config.self_assessment_weight,
        "knowledge_test": config.knowledge_test_weight,
        "scenario_test": config.scenario_test_weight,
        "training_evidence": config.training_evidence_weight,
    }
    return round(sum(weights[name] for name, score in components.items() if score is not None), 2)
