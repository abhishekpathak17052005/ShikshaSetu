from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillGapCompetency(BaseModel):
    """Individual competency skill gap."""
    
    model_config = ConfigDict(from_attributes=True)

    competency_id: str
    competency_code: str
    competency_name: str
    domain: str
    required_level: float = Field(ge=1, le=5)
    current_level: float | None = Field(default=None, ge=1, le=5)
    gap: float = Field(ge=0, le=4)
    gap_category: str  # NO_GAP, LOW, MEDIUM, HIGH, CRITICAL
    assessment_status: str  # ASSESSED, NOT_ASSESSED
    confidence: float = Field(default=0.0, ge=0, le=1)
    priority: int = Field(ge=1, le=4)
    importance: float = Field(ge=0, le=1)
    priority_score: float = Field(ge=0, le=1)
    last_assessed_at: datetime | None = None


class SkillGapSummary(BaseModel):
    """Summary of all gaps for an employee."""
    
    role_id: str
    role_code: str
    role_name: str
    required_competencies: int
    total_gaps: int
    no_gap_count: int
    not_assessed_count: int
    critical_gaps: int
    high_gaps: int
    medium_gaps: int
    low_gaps: int


class SkillGapResponse(BaseModel):
    """Complete skill gap response."""
    
    model_config = ConfigDict(from_attributes=True)

    role: dict  # {id, code, name}
    summary: SkillGapSummary
    gaps: list[SkillGapCompetency]
