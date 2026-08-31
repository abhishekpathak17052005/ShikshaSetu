"""ShikshaSetu AI Virtual Capability Assistant (Karmayogi AI Co-Pilot)."""

from .router import router as assistant_router
from .service import AssistantService

__all__ = ["assistant_router", "AssistantService"]
