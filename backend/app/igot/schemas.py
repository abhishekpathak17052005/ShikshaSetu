"""Pydantic schemas for iGOT Karmayogi Ecosystem Integration."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class IGOTEcosystemStatusResponse(BaseModel):
    """Status of iGOT Karmayogi ecosystem connectivity and integration boundary."""
    integration_mode: str = Field(..., description="'prototype' or 'live'")
    catalog_available: bool = Field(..., description="Whether iGOT course catalog is indexed in ShikshaSetu")
    total_courses_available: int = Field(..., description="Number of indexed iGOT learning resources")
    live_gateway_available: bool = Field(..., description="Whether live Karmayogi Bharat API gateway is connected")
    official_credentials_configured: bool = Field(..., description="Whether official API keys/client secrets are present")
    status_notice: str = Field(..., description="Human-readable integration notice for civil services audit")
    supported_capabilities: List[str] = Field(
        default_factory=lambda: [
            "Catalog Browsing & Competency Mapping",
            "5-Factor Personalized Recommendation Ranking",
            "Direct Portal Deep-Linking",
            "Self-Paced Learning Activity Tracking",
            "Immutable Supporting Evidence Ledger (0.30 confidence)",
        ]
    )
    pending_live_capabilities: List[str] = Field(
        default_factory=lambda: [
            "Live Parichay SSO Token Exchange",
            "Automated Server-to-Server Course Enrollment",
            "Bi-directional SCORM/xAPI Telemetry Push",
            "W3C Verifiable Credential Digital Certificate Verification",
        ]
    )


class IGOTCourseSummary(BaseModel):
    """Summary representation of an indexed iGOT course."""
    id: str
    resource_id: str
    course_id: Optional[str] = None
    title: str
    provider: str = "IGOT"
    duration_hours: Optional[float] = None
    difficulty: Optional[str] = None
    competencies: List[str] = Field(default_factory=list)
    course_url: Optional[str] = None
    source_document: Optional[str] = None
    verification_status: str = "VERIFIED"


class IGOTCourseListResponse(BaseModel):
    """Response schema for listing available iGOT courses."""
    total: int
    page: int
    limit: int
    provider: str = "IGOT"
    courses: List[IGOTCourseSummary]
    metadata: Dict[str, Any] = Field(default_factory=dict)
