from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.competencies.models import Domain, EvidenceType, FrameworkStatus, SourceType
from app.competencies.schemas import CompetencyEvidence, CompetencyProfile, CompetencyResponse, RoleRequirementResponse


VALID_LEVELS = {str(level): f"Level {level}" for level in range(1, 6)}


def test_competency_schema_requires_all_prototype_levels() -> None:
    with pytest.raises(ValidationError):
        CompetencyResponse(
            id="id",
            code="TECH_SQL",
            name="SQL",
            domain=Domain.TECHNICAL,
            description="Prototype competency.",
            level_definitions={"1": "Awareness"},
            status="active",
            framework_status=FrameworkStatus.PROTOTYPE,
            source_type=SourceType.PROTOTYPE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_profile_rejects_invalid_level_and_confidence() -> None:
    with pytest.raises(ValidationError):
        CompetencyProfile(
            user_id="user",
            competency_id="competency",
            current_level=6,
            confidence=1.1,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_requirement_and_evidence_validate_ranges_and_types() -> None:
    requirement = RoleRequirementResponse(
        role_id="role",
        competency_id="competency",
        required_level=4,
        priority=1,
        importance=1,
        framework_status=FrameworkStatus.PROTOTYPE,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    evidence = CompetencyEvidence(
        user_id="user",
        competency_id="competency",
        evidence_type=EvidenceType.QUIZ,
        score=4.0,
        weight=0.4,
        source="quiz_attempt",
        created_at=datetime.now(UTC),
    )
    assert requirement.required_level == 4
    assert evidence.evidence_type is EvidenceType.QUIZ
