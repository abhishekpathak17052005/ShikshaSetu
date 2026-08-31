"""Pydantic schemas for learning activities."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.learning_activities.models import LearningActivityStatus


class LearningActivityCreate(BaseModel):
    """Request schema for creating a learning activity."""

    resource_id: str = Field(..., description="ID of the learning resource")
    competency_id: str = Field(..., description="Competency this resource addresses")


class LearningActivityUpdate(BaseModel):
    """Request schema for updating a learning activity."""

    progress_percent: Optional[float] = Field(None, ge=0, le=100, description="Learning progress (0-100%)")
    duration_minutes: Optional[float] = Field(None, ge=0, description="Time spent learning in minutes")
    notes: Optional[str] = Field(None, description="Optional notes about the learning")


class LearningActivityComplete(BaseModel):
    """Request schema for completing a learning activity."""

    final_score: Optional[float] = Field(None, ge=0, le=100, description="Optional final assessment score")
    notes: Optional[str] = Field(None, description="Completion notes")


class LearningActivityResponse(BaseModel):
    """Response schema for a learning activity."""

    activity_id: str = Field(..., description="Activity ID")
    user_id: str = Field(..., description="User ID")
    resource_id: str = Field(..., description="Resource ID")
    competency_id: str = Field(..., description="Competency ID")
    status: LearningActivityStatus = Field(..., description="Current status")
    started_at: datetime = Field(..., description="When activity started")
    completed_at: Optional[datetime] = Field(None, description="When activity completed")
    last_accessed_at: datetime = Field(..., description="Last time user engaged")
    progress_percent: float = Field(0, ge=0, le=100, description="Progress percentage")
    duration_minutes: float = Field(0, ge=0, description="Total time spent")
    notes: Optional[str] = Field(None, description="Notes")


class LearningActivityListResponse(BaseModel):
    """Response for listing learning activities."""

    activities: list[LearningActivityResponse] = Field(..., description="List of activities")
    total_count: int = Field(..., description="Total number of activities")


class LearningActivityCompleteResponse(BaseModel):
    """Response after completing a learning activity."""

    activity: LearningActivityResponse
    evidence_created: bool = Field(..., description="Whether evidence was created")
    evidence_id: Optional[str] = Field(None, description="ID of created evidence record")
    competency_updated: dict = Field(..., description="Competency update details (before, after, change)")
    gap_recalculated: dict = Field(..., description="Skill gap update details (before, after, change)")
