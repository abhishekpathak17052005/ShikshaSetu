"""Provider abstraction for learning resources - supports multiple sources."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pymongo.database import Database

from .repository import LearningResourceRepository


class LearningResourceProvider(ABC):
    """Abstract base class for learning resource providers."""

    def __init__(self, database: Database):
        self.db = database
        self.repo = LearningResourceRepository(database)
        self.provider_name: str = ""

    @abstractmethod
    def get_resources_for_competency(
        self, competency_code: str
    ) -> List[Dict[str, Any]]:
        """Get candidate resources for a competency."""
        pass

    @abstractmethod
    def get_resource_confidence(
        self, resource_id: str, competency_code: str
    ) -> float:
        """Get confidence score (0.0-1.0) for resource-competency mapping."""
        pass

    @abstractmethod
    def get_resource_difficulty(self, resource: Dict[str, Any]) -> Optional[str]:
        """Get difficulty level of a resource (or None if unknown)."""
        pass

    @abstractmethod
    def get_resource_prerequisites(self, resource: Dict[str, Any]) -> List[str]:
        """Get list of prerequisites (or empty list if unknown)."""
        pass

    @abstractmethod
    def get_resource_role_match(
        self, resource: Dict[str, Any], required_role: str
    ) -> Optional[float]:
        """
        Get role match score (0.0-1.0) for resource vs required role.
        Returns None if match cannot be determined.
        """
        pass

    @abstractmethod
    def validate_resource(self, resource: Dict[str, Any]) -> bool:
        """Validate that a resource is in usable state."""
        pass


class PrototypeIGOTProvider(LearningResourceProvider):
    """Provider implementation for iGOT (Karmayogi) resources."""

    def __init__(self, database: Database):
        super().__init__(database)
        self.provider_name = "IGOT"

    def get_resources_for_competency(
        self, competency_code: str
    ) -> List[Dict[str, Any]]:
        """Get iGOT courses mapped to a competency."""
        return self.repo.get_resources_by_competency_and_provider(
            competency_code, "IGOT"
        )

    def get_resource_confidence(
        self, resource_id: str, competency_code: str
    ) -> float:
        """Get mapping confidence from iGOT mapping metadata."""
        mapping = self.repo.get_mapping(str(resource_id), competency_code)
        if mapping:
            return float(mapping.get("confidence", 0.5))
        return 0.0

    def get_resource_difficulty(self, resource: Dict[str, Any]) -> Optional[str]:
        """Get difficulty from resource metadata."""
        difficulty = resource.get("metadata", {}).get("difficulty")
        # Return None if not set, otherwise return the string value
        return difficulty if difficulty else None

    def get_resource_prerequisites(self, resource: Dict[str, Any]) -> List[str]:
        """Get prerequisites from resource metadata."""
        return resource.get("metadata", {}).get("prerequisites", [])

    def get_resource_role_match(
        self, resource: Dict[str, Any], required_role: str
    ) -> Optional[float]:
        """
        For iGOT prototype: no role matching data yet.
        Return neutral unknown value (0.5).
        """
        # Placeholder for future role matching logic
        return None

    def validate_resource(self, resource: Dict[str, Any]) -> bool:
        """Validate iGOT resource."""
        return (
            resource.get("status") == "ACTIVE"
            and resource.get("provider") == "IGOT"
            and resource.get("source", {}).get("verification_status") == "VERIFIED"
        )


class PrototypeNSSTAProvider(LearningResourceProvider):
    """Provider implementation for NSSTA/MoSPI training programmes."""

    def __init__(self, database: Database):
        super().__init__(database)
        self.provider_name = "NSSTA"

    def get_resources_for_competency(
        self, competency_code: str
    ) -> List[Dict[str, Any]]:
        """Get NSSTA programmes mapped to a competency."""
        return self.repo.get_resources_by_competency_and_provider(
            competency_code, "NSSTA"
        )

    def get_resource_confidence(
        self, resource_id: str, competency_code: str
    ) -> float:
        """Get mapping confidence from NSSTA mapping metadata."""
        mapping = self.repo.get_mapping(str(resource_id), competency_code)
        if mapping:
            return float(mapping.get("confidence", 0.5))
        return 0.0

    def get_resource_difficulty(self, resource: Dict[str, Any]) -> Optional[str]:
        """Get difficulty from resource metadata."""
        difficulty = resource.get("metadata", {}).get("difficulty")
        return difficulty if difficulty else None

    def get_resource_prerequisites(self, resource: Dict[str, Any]) -> List[str]:
        """Get prerequisites from resource metadata."""
        return resource.get("metadata", {}).get("prerequisites", [])

    def get_resource_role_match(
        self, resource: Dict[str, Any], required_role: str
    ) -> Optional[float]:
        """
        For NSSTA prototype: no role matching data yet.
        Return neutral unknown value (0.5).
        """
        # Placeholder for future role matching logic
        return None

    def validate_resource(self, resource: Dict[str, Any]) -> bool:
        """Validate NSSTA resource (TENTATIVE allowed for official calendar)."""
        return (
            resource.get("status") == "ACTIVE"
            and resource.get("provider") == "NSSTA"
            and resource.get("source", {}).get("verification_status")
            in ("VERIFIED", "TENTATIVE")
        )


class ProviderFactory:
    """Factory for creating provider instances."""

    _providers = {
        "IGOT": PrototypeIGOTProvider,
        "NSSTA": PrototypeNSSTAProvider,
    }

    @staticmethod
    def get_provider(
        provider_name: str, database: Database
    ) -> LearningResourceProvider:
        """Get a provider instance by name."""
        provider_class = ProviderFactory._providers.get(provider_name)
        if not provider_class:
            raise ValueError(
                f"Unknown provider: {provider_name}. Available: {list(ProviderFactory._providers.keys())}"
            )
        return provider_class(database)

    @staticmethod
    def get_all_providers(database: Database) -> Dict[str, LearningResourceProvider]:
        """Get all available provider instances."""
        return {
            name: provider_class(database)
            for name, provider_class in ProviderFactory._providers.items()
        }
