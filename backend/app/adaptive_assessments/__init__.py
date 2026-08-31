"""Adaptive Capability Assessment Module for ShikshaSetu."""

from .router import router as adaptive_assessments_router
from .service import AdaptiveAssessmentService

__all__ = ["adaptive_assessments_router", "AdaptiveAssessmentService"]
