from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.competencies.models import (
    Domain,
    EvidenceType,
    FrameworkStatus,
    SourceType,
)

Code = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")]


class CompetencyProfile(BaseModel):
    user_id: str
    competency_id: str
    current_level: float = Field(ge=1.0, le=5.0)
    confidence: float = Field(ge=0.0, le=1.0)
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class CompetencyEvidence(BaseModel):
    user_id: str
    competency_id: str
    evidence_type: EvidenceType
    score: float = Field(ge=0.0, le=5.0)
    weight: float = Field(ge=0.0, le=1.0)
    source: str
    created_at: datetime




class CompetencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: Code
    name: str
    domain: Domain
    description: str
    level_definitions: dict[str, str]
    status: str
    framework_status: FrameworkStatus
    source_type: SourceType
    source_reference: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("level_definitions")
    @classmethod
    def validate_level_definitions(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) != {"1", "2", "3", "4", "5"}:
            raise ValueError("level_definitions must contain levels 1 through 5")
        return value


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role_code: Code
    role_name: str
    description: str
    status: str
    framework_status: FrameworkStatus = FrameworkStatus.PROTOTYPE
    source_type: SourceType = SourceType.PROTOTYPE
    source_reference: str | None = None
    department: str | None = None
    department_code: str | None = None
    designations: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class RoleRequirementResponse(BaseModel):
    role_id: str
    competency_id: str
    required_level: float = Field(ge=1, le=5)
    priority: int = Field(ge=1, le=4)
    importance: float = Field(ge=0, le=1)
    framework_status: FrameworkStatus
    created_at: datetime
    updated_at: datetime


class CompetencyProfile(BaseModel):
    user_id: str
    competency_id: str
    current_level: float = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    last_assessed_at: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class UserApplicableCompetencyResponse(BaseModel):
    id: str
    code: str
    name: str
    domain: str
    description: str
    required_level: float
    priority: int
    importance: float
    current_level: float | None = None
    confidence: float = 0.0
    gap: float = 0.0
    gap_category: str = "NOT_ASSESSED"
    last_assessed_at: datetime | None = None
    indicator: str = "Not Assessed"
    level_definitions: dict[str, str] = Field(default_factory=dict)

