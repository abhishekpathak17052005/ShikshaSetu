"""Pydantic schemas for the AI Virtual Capability Assistant."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    """Incoming user message and optional client context."""
    message: str = Field(..., min_length=1, max_length=2000, description="User question or prompt")
    context_page: Optional[str] = Field(None, description="Page the user is currently browsing (e.g. Skill Gaps, Recommendations)")
    current_competency_code: Optional[str] = Field(None, description="Active competency in focus")
    current_resource_id: Optional[str] = Field(None, description="Active learning resource in focus")


class AssistantSourceCitation(BaseModel):
    """Verified curriculum source or catalog citation."""
    source_id: str
    title: str
    source_type: str  # "CURRICULUM_DOCUMENT", "COMPETENCY_FRAMEWORK", "IGOT_CATALOG", "NSSTA_PROGRAMME"
    url: Optional[str] = None
    excerpt: Optional[str] = None


class SuggestedAction(BaseModel):
    """Actionable navigation or workflow suggestion."""
    action_type: str  # "NAVIGATE", "VIEW_GAP", "START_LEARNING", "TAKE_ASSESSMENT"
    label: str
    target_page: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class AssistantChatResponse(BaseModel):
    """Grounded capability advisor response."""
    answer: str
    sources: List[AssistantSourceCitation] = Field(default_factory=list)
    context_summary: Dict[str, Any] = Field(default_factory=dict)
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    model_provider: str = "gemini"
