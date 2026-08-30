"""Candidate generation service - identifies learning resources for skill gaps."""

from typing import List, Dict, Any, Optional, Set
from pymongo.database import Database

from .repository import LearningResourceRepository
from .provider import ProviderFactory, LearningResourceProvider


class CandidateResource:
    """A candidate resource for a specific skill gap."""

    def __init__(
        self,
        resource: Dict[str, Any],
        competency_code: str,
        competency_name: str,
        gap: Dict[str, Any],  # Gap item dict from engine
        provider: LearningResourceProvider,
        mapping_confidence: float,
    ):
        self.resource = resource
        self.competency_code = competency_code
        self.competency_name = competency_name
        self.gap = gap
        self.provider = provider
        self.mapping_confidence = mapping_confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "resource_id": self.resource.get("_id"),
            "resource_human_id": self.resource.get("resource_id"),
            "title": self.resource.get("title"),
            "provider": self.resource.get("provider"),
            "competency_code": self.competency_code,
            "competency_name": self.competency_name,
            "mapping_confidence": self.mapping_confidence,
            "gap": {
                "competency_code": self.gap.get("competency_code"),
                "current_level": self.gap.get("current_level"),
                "required_level": self.gap.get("required_level"),
                "gap": self.gap.get("gap"),
                "gap_category": self.gap.get("gap_category"),
                "priority_score": self.gap.get("priority_score"),
            },
        }


class CandidateGenerationService:
    """Service to generate candidate resources for skill gaps."""

    def __init__(self, database: Database):
        self.db = database
        self.repo = LearningResourceRepository(database)
        self.providers = ProviderFactory.get_all_providers(database)

    def generate_candidates_for_gaps(
        self, gaps: List[Dict[str, Any]], user_role: Optional[str] = None
    ) -> Dict[str, List[CandidateResource]]:
        """
        Generate candidate resources for a list of skill gaps.

        Returns a dict mapping competency_code -> list of CandidateResource objects.
        """
        candidates: Dict[str, List[CandidateResource]] = {}

        for gap in gaps:
            candidates[gap["competency_code"]] = self.generate_candidates_for_gap(gap)

        return candidates

    def generate_candidates_for_gap(
        self, gap: Dict[str, Any]
    ) -> List[CandidateResource]:
        """
        Generate candidate resources for a single skill gap.

        Only includes resources with valid competency mappings.
        """
        candidates: List[CandidateResource] = []
        seen_resources: Set[str] = set()  # Avoid duplicates

        # Get competency
        competency = self.repo.get_competency_by_code(gap["competency_code"])
        if not competency:
            return []

        competency_name = competency.get("name", gap["competency_code"])

        # Try each provider
        for provider_name, provider in self.providers.items():
            resources = provider.get_resources_for_competency(gap["competency_code"])

            for resource in resources:
                # Avoid duplicates
                resource_id = str(resource.get("_id"))
                if resource_id in seen_resources:
                    continue
                seen_resources.add(resource_id)

                # Validate resource
                if not provider.validate_resource(resource):
                    continue

                # Get mapping confidence
                mapping_confidence = provider.get_resource_confidence(
                    resource_id, gap["competency_code"]
                )

                # Create candidate
                candidate = CandidateResource(
                    resource=resource,
                    competency_code=gap["competency_code"],
                    competency_name=competency_name,
                    gap=gap,
                    provider=provider,
                    mapping_confidence=mapping_confidence,
                )

                candidates.append(candidate)

        return candidates

    def filter_candidates_by_difficulty(
        self, candidates: List[CandidateResource], current_level: float
    ) -> List[CandidateResource]:
        """
        Filter candidates based on resource difficulty and user's current level.

        Returns candidates that are appropriate for the user's current level.
        """
        filtered = []

        for candidate in candidates:
            difficulty = candidate.provider.get_resource_difficulty(candidate.resource)

            # If difficulty unknown, include it (neutral treatment)
            if difficulty is None:
                filtered.append(candidate)
                continue

            # Map difficulty to numeric level
            difficulty_level_map = {
                "Beginner": 1.0,
                "Intermediate": 2.5,
                "Advanced": 4.0,
            }

            difficulty_level = difficulty_level_map.get(difficulty)
            if difficulty_level is None:
                # Unknown difficulty string, include it
                filtered.append(candidate)
                continue

            # Include if difficulty matches or slightly exceeds current level
            # (allow stretch goals)
            if difficulty_level <= current_level + 1.5:
                filtered.append(candidate)

        return filtered

    def filter_candidates_by_prerequisites(
        self, candidates: List[CandidateResource]
    ) -> List[CandidateResource]:
        """
        Filter candidates based on prerequisites.

        For now: no prerequisite data available, so all candidates pass.
        When prerequisite data is available, filter accordingly.
        """
        # Placeholder for future prerequisite filtering
        # For prototype: all candidates pass (prerequisites unknown)
        return candidates

    def deduplicate_candidates(
        self, candidates: List[CandidateResource]
    ) -> List[CandidateResource]:
        """
        Remove duplicate resources, keeping the one with highest confidence.

        Multiple candidates might point to the same resource if it has multiple
        competency mappings. Keep only the best one per resource.
        """
        best_by_resource: Dict[str, CandidateResource] = {}

        for candidate in candidates:
            resource_id = str(candidate.resource.get("_id"))

            if resource_id not in best_by_resource:
                best_by_resource[resource_id] = candidate
            else:
                # Keep the one with higher confidence
                if (
                    candidate.mapping_confidence
                    > best_by_resource[resource_id].mapping_confidence
                ):
                    best_by_resource[resource_id] = candidate

        return list(best_by_resource.values())

    def get_unmapped_resources(
        self, provider_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get resources that have no competency mappings.

        These are browseable but not part of competency-based recommendations.
        """
        mapped_resource_ids = set()
        for mapping in self.repo.mappings.find({}, {"resource_id": 1}):
            mapped_resource_ids.add(str(mapping.get("resource_id")))

        query = {"status": "ACTIVE"}
        if provider_name:
            query["provider"] = provider_name

        unmapped = []
        for resource in self.repo.resources.find(query):
            if str(resource.get("_id")) not in mapped_resource_ids:
                unmapped.append(resource)

        return unmapped
