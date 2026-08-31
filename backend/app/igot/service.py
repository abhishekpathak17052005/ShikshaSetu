"""Service layer for iGOT Karmayogi Ecosystem Integration."""

from typing import Optional, List, Dict, Any
from pymongo.database import Database

from app.core.config import Settings
from .adapter import IGOTAdapter
from .prototype_adapter import PrototypeIGOTAdapter
from .schemas import (
    IGOTEcosystemStatusResponse,
    IGOTCourseSummary,
    IGOTCourseListResponse,
)


class IGOTEcosystemService:
    """Coordinates iGOT integration adapters and status diagnostics."""

    def __init__(self, database: Database, settings: Settings):
        self.db = database
        self.settings = settings
        self.adapter: IGOTAdapter = self._init_adapter()

    def _init_adapter(self) -> IGOTAdapter:
        # If live credentials become configured in the future, LiveIGOTAdapter can be returned here
        mode = getattr(self.settings, "igot_integration_mode", "prototype").lower()
        has_creds = bool(
            getattr(self.settings, "igot_client_id", None)
            and getattr(self.settings, "igot_client_secret", None)
        )

        if mode == "live" and has_creds:
            # Future live adapter placeholder
            return PrototypeIGOTAdapter(self.db)

        return PrototypeIGOTAdapter(self.db)

    def get_ecosystem_status(self) -> IGOTEcosystemStatusResponse:
        """Returns the current connection and indexing status of the iGOT ecosystem."""
        has_creds = bool(
            getattr(self.settings, "igot_client_id", None)
            and getattr(self.settings, "igot_client_secret", None)
        )
        total_courses = self.adapter.count_courses()

        return IGOTEcosystemStatusResponse(
            integration_mode=self.adapter.get_integration_mode(),
            catalog_available=total_courses > 0,
            total_courses_available=total_courses,
            live_gateway_available=self.adapter.is_live_available(),
            official_credentials_configured=has_creds,
            status_notice=self.adapter.get_status_notice(),
        )

    def list_courses(
        self,
        competency_code: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> IGOTCourseListResponse:
        """Returns paginated list of indexed iGOT courses."""
        page = max(1, page)
        limit = max(1, min(100, limit))
        skip = (page - 1) * limit

        raw_docs = self.adapter.list_courses(
            competency_code=competency_code,
            search_query=search_query,
            limit=limit,
            skip=skip,
        )
        total = self.adapter.count_courses(
            competency_code=competency_code,
            search_query=search_query,
        )

        summaries = []
        for doc in raw_docs:
            meta = doc.get("metadata", {})
            prov = doc.get("provider_specific", {})
            source = doc.get("source", {})

            summaries.append(
                IGOTCourseSummary(
                    id=str(doc.get("_id", "")),
                    resource_id=doc.get("resource_id", ""),
                    course_id=prov.get("course_id"),
                    title=doc.get("title", "Untitled Course"),
                    provider="IGOT",
                    duration_hours=meta.get("duration_hours"),
                    difficulty=meta.get("difficulty"),
                    competencies=doc.get("competencies", []),
                    course_url=prov.get("course_url") or source.get("source_url"),
                    source_document=source.get("source_document"),
                    verification_status=source.get("verification_status", "VERIFIED"),
                )
            )

        return IGOTCourseListResponse(
            total=total,
            page=page,
            limit=limit,
            courses=summaries,
            metadata={
                "integration_mode": self.adapter.get_integration_mode(),
                "filter_competency": competency_code,
                "search_query": search_query,
            },
        )
