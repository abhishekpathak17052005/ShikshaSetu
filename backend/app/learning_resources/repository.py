"""Repository layer for learning resources database access."""

from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.database import Database

from .models import LearningResource, Competency, ResourceMapping


class LearningResourceRepository:
    """Repository for learning resources queries."""

    def __init__(self, database: Database):
        self.db = database
        self.resources = database.learning_resources
        self.competencies = database.competencies
        self.mappings = database.learning_resource_mappings

    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource by its resource_id string (e.g., 'IGOT-123', 'NSSTA-PROTO-xxx')."""
        return self.resources.find_one({"resource_id": resource_id})

    def get_resource_by_mongo_id(self, mongo_id: str) -> Optional[Dict[str, Any]]:
        """Get a resource by its MongoDB ObjectId."""
        try:
            obj_id = ObjectId(mongo_id)
            return self.resources.find_one({"_id": obj_id})
        except Exception:
            return None

    def get_resources_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all resources from a specific provider."""
        return list(self.resources.find({"provider": provider, "status": "ACTIVE"}))

    def get_resources_by_competency(self, competency_code: str) -> List[Dict[str, Any]]:
        """Get all resources mapped to a specific competency."""
        # Get mappings for this competency
        mappings = list(self.mappings.find({"competency_code": competency_code}))

        resources = []
        for mapping in mappings:
            resource = self.get_resource_by_mongo_id(str(mapping["resource_id"]))
            if resource:
                resources.append(resource)

        return resources

    def get_resources_by_competency_and_provider(
        self, competency_code: str, provider: str
    ) -> List[Dict[str, Any]]:
        """Get resources for a competency from a specific provider."""
        mappings = list(
            self.mappings.find(
                {"competency_code": competency_code, "provider": provider}
            )
        )

        resources = []
        for mapping in mappings:
            resource = self.get_resource_by_mongo_id(str(mapping["resource_id"]))
            if resource and resource.get("provider") == provider:
                resources.append(resource)

        return resources

    def get_competency_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get a competency by its code."""
        return self.competencies.find_one({"code": code})

    def get_all_competencies(self) -> List[Dict[str, Any]]:
        """Get all competencies."""
        return list(self.competencies.find())

    def get_mapping(
        self, resource_id: str, competency_code: str
    ) -> Optional[Dict[str, Any]]:
        """Get mapping between a resource and competency."""
        return self.mappings.find_one(
            {"resource_id": ObjectId(resource_id), "competency_code": competency_code}
        )

    def get_mappings_for_resource(self, resource_id: str) -> List[Dict[str, Any]]:
        """Get all competency mappings for a resource."""
        return list(self.mappings.find({"resource_id": ObjectId(resource_id)}))

    def get_mappings_for_competency(self, competency_code: str) -> List[Dict[str, Any]]:
        """Get all resource mappings for a competency."""
        return list(self.mappings.find({"competency_code": competency_code}))

    def count_resources_by_provider(self, provider: str) -> int:
        """Count resources by provider."""
        return self.resources.count_documents({"provider": provider, "status": "ACTIVE"})

    def count_mapped_competencies(self) -> int:
        """Count competencies that have at least one resource mapping."""
        unique_codes = self.mappings.distinct("competency_code")
        return len(unique_codes)

    def get_resources_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        """Get resources by difficulty level."""
        return list(
            self.resources.find(
                {"metadata.difficulty": difficulty, "status": "ACTIVE"}
            )
        )

    def get_iGOT_resources(self) -> List[Dict[str, Any]]:
        """Get all iGOT resources."""
        return self.get_resources_by_provider("IGOT")

    def get_NSSTA_resources(self) -> List[Dict[str, Any]]:
        """Get all NSSTA resources."""
        return self.get_resources_by_provider("NSSTA")
