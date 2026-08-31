"""Prototype iGOT Karmayogi Adapter implementation.

Uses the curated, verified iGOT courses already indexed in MongoDB (from igot_courses_enriched.csv).
Does not duplicate data, make fake external network calls, or fabricate unverified API responses.
"""

from typing import List, Dict, Any, Optional
from pymongo.database import Database
from bson import ObjectId

from .adapter import IGOTAdapter


class PrototypeIGOTAdapter(IGOTAdapter):
    """Adapter reading from ShikshaSetu's verified iGOT catalog in MongoDB."""

    def get_integration_mode(self) -> str:
        return "prototype"

    def is_live_available(self) -> bool:
        return False

    def get_status_notice(self) -> str:
        return (
            "iGOT Karmayogi — Curated Catalog Connected. "
            "Course recommendations and deep-linking are fully operational. "
            "Live server-to-server automated enrollment and progress sync "
            "are pending official Karmayogi Bharat API gateway credentials."
        )

    def list_courses(
        self,
        competency_code: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "provider": "IGOT",
            "status": "ACTIVE",
        }

        if competency_code:
            query["competencies"] = competency_code.upper()

        if search_query:
            query["title"] = {"$regex": search_query.strip(), "$options": "i"}

        cursor = (
            self.db.learning_resources.find(query)
            .sort("title", 1)
            .skip(skip)
            .limit(limit)
        )

        return list(cursor)

    def get_course_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        # Try finding by ObjectId or resource_id or provider_specific.course_id
        if ObjectId.is_valid(resource_id):
            doc = self.db.learning_resources.find_one({
                "_id": ObjectId(resource_id),
                "provider": "IGOT",
            })
            if doc:
                return doc

        return self.db.learning_resources.find_one({
            "provider": "IGOT",
            "$or": [
                {"resource_id": resource_id},
                {"provider_specific.course_id": resource_id},
            ],
        })

    def count_courses(
        self,
        competency_code: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> int:
        query: Dict[str, Any] = {
            "provider": "IGOT",
            "status": "ACTIVE",
        }
        if competency_code:
            query["competencies"] = competency_code.upper()

        if search_query:
            query["title"] = {"$regex": search_query.strip(), "$options": "i"}

        return self.db.learning_resources.count_documents(query)
