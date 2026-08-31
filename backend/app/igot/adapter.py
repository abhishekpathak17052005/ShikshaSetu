"""Abstract base adapter interface for iGOT Karmayogi integration.

This interface ensures that the recommendation engine, official portal, and
evidence recording services remain completely decoupled from the underlying
iGOT connection mechanism (whether Prototype catalog or future Live API).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pymongo.database import Database


class IGOTAdapter(ABC):
    """Abstract interface defining the iGOT Karmayogi integration boundary."""

    def __init__(self, database: Database):
        self.db = database

    @abstractmethod
    def get_integration_mode(self) -> str:
        """Return 'prototype' or 'live'."""
        pass

    @abstractmethod
    def is_live_available(self) -> bool:
        """Return True if live official credentials and gateway connectivity exist."""
        pass

    @abstractmethod
    def get_status_notice(self) -> str:
        """Return an explainable audit notice for the current integration status."""
        pass

    @abstractmethod
    def list_courses(
        self,
        competency_code: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """List iGOT courses with optional competency and search filters."""
        pass

    @abstractmethod
    def get_course_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific iGOT course by its resource_id or course_id."""
        pass

    @abstractmethod
    def count_courses(
        self,
        competency_code: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Count total available iGOT courses."""
        pass
