"""iGOT Karmayogi Ecosystem Integration Module for ShikshaSetu."""

from .adapter import IGOTAdapter
from .prototype_adapter import PrototypeIGOTAdapter
from .service import IGOTEcosystemService
from .router import router as igot_router

__all__ = [
    "IGOTAdapter",
    "PrototypeIGOTAdapter",
    "IGOTEcosystemService",
    "igot_router",
]
