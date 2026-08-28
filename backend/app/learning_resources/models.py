"""Data models for learning resources - Pydantic schemas for API."""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class ResourceMetadata(BaseModel):
    """Resource metadata."""
    duration_hours: Optional[float] = None
    difficulty: Optional[str] = None  # "Beginner", "Intermediate", "Advanced", None
    target_roles: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


class ResourceSource(BaseModel):
    """Resource source information."""
    source_type: str  # "GOVERNMENT_PUBLICATION", etc.
    source_url: Optional[str] = None
    source_document: str  # "SRC-01", "SRC-05", etc.
    verification_status: str  # "VERIFIED", "TENTATIVE"


class ProviderSpecific(BaseModel):
    """Provider-specific metadata."""
    course_id: Optional[str] = None  # NULL for NSSTA/MoSPI
    programme_id: Optional[str] = None  # For NSSTA
    course_url: Optional[str] = None
    provider_name: Optional[str] = None
    extraction_note: Optional[str] = None


class LearningResource(BaseModel):
    """Complete learning resource document."""
    resource_id: str  # Human-readable ID
    provider: str  # "IGOT", "NSSTA"
    resource_type: str  # "COURSE", "TRAINING_PROGRAMME"
    title: str
    metadata: ResourceMetadata
    competencies: List[str] = Field(default_factory=list)
    source: ResourceSource
    provider_specific: ProviderSpecific
    status: str = "ACTIVE"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetencyLevel(BaseModel):
    """Competency level definition."""
    level: int  # 1-5
    definition: str


class Competency(BaseModel):
    """Competency with prototype levels."""
    code: str
    name: str
    domain: str
    description: Optional[str] = None
    level_definitions: Dict[str, str]  # "1": "...", "2": "...", etc.
    parent_competency_code: Optional[str] = None
    is_subskill: bool = False
    framework_status: str = "prototype"

    class Config:
        from_attributes = True


class ResourceMapping(BaseModel):
    """Resource-to-competency mapping."""
    resource_id: str  # MongoDB ObjectId as string
    competency_id: str  # MongoDB ObjectId as string
    competency_code: str
    competency_name: str
    provider: str  # "IGOT", "NSSTA"
    mapping_type: str  # "DERIVED", "VERIFIED"
    confidence: float  # 0.0 - 1.0
    evidence: Optional[str] = None
    mapping_quality: Dict[str, Any] = Field(default_factory=dict)
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# API Response Models

class ScoreComponent(BaseModel):
    """Individual scoring component."""
    name: str  # "competency_match", "gap_priority", etc.
    weight: float  # 0.0 - 1.0
    score: float  # 0.0 - 1.0
    value: float  # Component value (weight * score)


class RecommendationExplanation(BaseModel):
    """Explanation for why a resource was recommended."""
    summary: str
    competency_gap: str
    current_level: Optional[float] = None
    required_level: Optional[float] = None
    gap_size: float
    score_breakdown: List[ScoreComponent]
    provider_note: Optional[str] = None


class LearningRecommendation(BaseModel):
    """A single learning recommendation."""
    rank: int
    resource: LearningResource
    provider: str
    competency_code: str
    competency_name: str
    current_level: Optional[float] = None  # User's current level (0.0 - 5.0), None if unassessed
    required_level: Optional[float] = None  # Role requirement (0.0 - 5.0)
    gap: float  # required - current
    score: float  # 0.0 - 1.0
    explanation: RecommendationExplanation
    source_verification: str  # "VERIFIED", "TENTATIVE"


class RecommendationResponse(BaseModel):
    """Response containing multiple recommendations."""
    user_id: str
    role: str
    total_recommendations: int
    recommendations: List[LearningRecommendation]
    metadata: Dict[str, Any] = Field(default_factory=dict)
