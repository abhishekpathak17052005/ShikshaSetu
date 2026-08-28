"""Tests for learning resources and recommendation engine."""

import pytest
from datetime import datetime, UTC
from bson import ObjectId

from app.learning_resources.repository import LearningResourceRepository
from app.learning_resources.provider import (
    ProviderFactory,
    PrototypeIGOTProvider,
    PrototypeNSSTAProvider,
)
from app.learning_resources.candidates import CandidateGenerationService
from app.learning_resources.scoring import ScoringFormula, ScoringService
from app.learning_resources.service import RecommendationService


@pytest.fixture
def sample_competency(database):
    """Insert a sample competency."""
    comp_id = ObjectId()
    database.competencies.insert_one({
        "_id": comp_id,
        "code": "STAT-SAMPLING",
        "name": "Sampling",
        "domain": "Statistical Competencies",
        "description": "Sampling theory",
        "level_definitions": {
            "1": "Aware",
            "2": "Basic",
            "3": "Intermediate",
            "4": "Advanced",
            "5": "Expert",
        },
        "framework_status": "prototype",
    })
    return comp_id


@pytest.fixture
def sample_igot_resource(database, sample_competency):
    """Insert a sample iGOT resource."""
    res_id = ObjectId()
    database.learning_resources.insert_one({
        "_id": res_id,
        "resource_id": "IGOT-12345",
        "provider": "IGOT",
        "resource_type": "COURSE",
        "title": "Advanced Sampling Techniques",
        "metadata": {
            "duration_hours": 24.0,
            "difficulty": "Intermediate",
            "target_roles": ["Statistical Officer"],
            "prerequisites": [],
        },
        "competencies": ["STAT-SAMPLING"],
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": "https://igot.example.com/course/12345",
            "source_document": "SRC-01",
            "verification_status": "VERIFIED",
        },
        "provider_specific": {
            "course_id": "12345",
            "course_url": "https://igot.example.com/course/12345",
            "provider_name": "iGOT Karmayogi",
            "extraction_note": None,
        },
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    return res_id


@pytest.fixture
def sample_nssta_resource(database, sample_competency):
    """Insert a sample NSSTA resource."""
    res_id = ObjectId()
    database.learning_resources.insert_one({
        "_id": res_id,
        "resource_id": "NSSTA-PROTO-ABC123",
        "provider": "NSSTA",
        "resource_type": "TRAINING_PROGRAMME",
        "title": "NSSTA Sampling Programme",
        "metadata": {
            "duration_hours": 16.0,
            "difficulty": "Beginner",
            "target_roles": [],
            "prerequisites": [],
        },
        "competencies": ["STAT-SAMPLING"],
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": "https://mospi.gov.in/nssta",
            "source_document": "SRC-05",
            "verification_status": "TENTATIVE",
        },
        "provider_specific": {
            "course_id": None,  # NULL for NSSTA
            "programme_id": "PROG-001",
            "course_url": None,
            "provider_name": "NSSTA",
            "extraction_note": "From official NSSTA calendar",
        },
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    return res_id


@pytest.fixture
def sample_mappings(database, sample_competency, sample_igot_resource, sample_nssta_resource):
    """Insert sample resource-to-competency mappings."""
    database.learning_resource_mappings.insert_many([
        {
            "resource_id": sample_igot_resource,
            "competency_code": "STAT-SAMPLING",
            "competency_name": "Sampling",
            "provider": "IGOT",
            "mapping_confidence": 0.9,
            "evidence": "Course covers sampling theory and practice",
            "verified_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
        },
        {
            "resource_id": sample_nssta_resource,
            "competency_code": "STAT-SAMPLING",
            "competency_name": "Sampling",
            "provider": "NSSTA",
            "mapping_confidence": 0.7,
            "evidence": "Programme title matches competency",
            "verified_at": None,
            "created_at": datetime.now(UTC),
        },
    ])


class TestLearningResourceRepository:
    """Tests for LearningResourceRepository."""

    def test_get_resource_by_id(self, database, sample_igot_resource):
        """Test retrieving resource by resource_id string."""
        repo = LearningResourceRepository(database)
        resource = repo.get_resource_by_id("IGOT-12345")
        
        assert resource is not None
        assert resource["resource_id"] == "IGOT-12345"
        assert resource["provider"] == "IGOT"

    def test_get_resources_by_provider(self, database, sample_igot_resource, sample_nssta_resource):
        """Test retrieving all resources from a provider."""
        repo = LearningResourceRepository(database)
        
        igot_resources = repo.get_resources_by_provider("IGOT")
        assert len(igot_resources) >= 1
        assert all(r["provider"] == "IGOT" for r in igot_resources)

    def test_get_resources_by_competency(self, database, sample_competency, sample_mappings):
        """Test retrieving resources for a competency."""
        repo = LearningResourceRepository(database)
        resources = repo.get_resources_by_competency("STAT-SAMPLING")
        
        assert len(resources) >= 2
        providers = {r["provider"] for r in resources}
        assert "IGOT" in providers
        assert "NSSTA" in providers

    def test_get_resources_by_competency_and_provider(self, database, sample_competency, sample_mappings):
        """Test filtering resources by competency and provider."""
        repo = LearningResourceRepository(database)
        resources = repo.get_resources_by_competency_and_provider("STAT-SAMPLING", "IGOT")
        
        assert len(resources) >= 1
        assert all(r["provider"] == "IGOT" for r in resources)


class TestProviders:
    """Tests for provider implementations."""

    def test_igot_provider_initialization(self, database):
        """Test iGOT provider can be created."""
        provider = PrototypeIGOTProvider(database)
        assert provider.provider_name == "IGOT"

    def test_nssta_provider_initialization(self, database):
        """Test NSSTA provider can be created."""
        provider = PrototypeNSSTAProvider(database)
        assert provider.provider_name == "NSSTA"

    def test_provider_factory_get_provider(self, database):
        """Test factory can create providers."""
        igot_provider = ProviderFactory.get_provider("IGOT", database)
        assert isinstance(igot_provider, PrototypeIGOTProvider)

        nssta_provider = ProviderFactory.get_provider("NSSTA", database)
        assert isinstance(nssta_provider, PrototypeNSSTAProvider)

    def test_provider_factory_unknown_provider(self, database):
        """Test factory raises error for unknown provider."""
        with pytest.raises(ValueError):
            ProviderFactory.get_provider("UNKNOWN", database)

    def test_igot_provider_get_resources_for_competency(
        self, database, sample_competency, sample_mappings
    ):
        """Test iGOT provider retrieves resources."""
        provider = PrototypeIGOTProvider(database)
        resources = provider.get_resources_for_competency("STAT-SAMPLING")
        
        assert len(resources) >= 1
        assert all(r["provider"] == "IGOT" for r in resources)

    def test_igot_provider_validate_resource(self, database, sample_igot_resource):
        """Test iGOT provider validates resources."""
        provider = PrototypeIGOTProvider(database)
        resource = database.learning_resources.find_one({"_id": sample_igot_resource})
        
        assert provider.validate_resource(resource) is True

    def test_nssta_provider_validate_resource(self, database, sample_nssta_resource):
        """Test NSSTA provider validates resources."""
        provider = PrototypeNSSTAProvider(database)
        resource = database.learning_resources.find_one({"_id": sample_nssta_resource})
        
        assert provider.validate_resource(resource) is True


class TestScoringFormula:
    """Tests for scoring formula."""

    def test_scoring_formula_initialization(self):
        """Test formula can be created with default weights."""
        formula = ScoringFormula()
        assert sum(formula.weights.values()) == pytest.approx(1.0)

    def test_scoring_formula_custom_weights(self):
        """Test formula accepts custom weights."""
        custom_weights = {
            "competency_match": 0.5,
            "gap_priority": 0.2,
            "role_match": 0.15,
            "difficulty_match": 0.1,
            "prerequisite_match": 0.05,
        }
        formula = ScoringFormula(custom_weights)
        assert formula.weights == custom_weights

    def test_scoring_formula_invalid_weights(self):
        """Test formula rejects weights that don't sum to 1.0."""
        invalid_weights = {
            "competency_match": 0.5,
            "gap_priority": 0.3,
            "role_match": 0.1,
            "difficulty_match": 0.05,
            "prerequisite_match": 0.0,  # Sum = 0.95, not 1.0
        }
        with pytest.raises(ValueError):
            ScoringFormula(invalid_weights)

    def test_difficulty_match_calculation(self):
        """Test difficulty matching calculation."""
        from unittest.mock import Mock
        
        formula = ScoringFormula()
        
        # Create a mock provider
        mock_provider = Mock()
        mock_provider.get_resource_difficulty.return_value = "Intermediate"
        
        # Create a mock candidate
        mock_candidate = Mock()
        mock_candidate.resource = Mock()
        
        # Perfect match (resource difficulty 2.5 = user level 2.5)
        score = formula._score_difficulty_match(
            candidate=mock_candidate,
            provider=mock_provider,
            user_current_level=2.5,
        )
        assert score == 1.0  # Perfect match


class TestCandidateGeneration:
    """Tests for candidate generation."""

    def test_unmapped_resources(self, database, sample_igot_resource):
        """Test identifying unmapped resources."""
        service = CandidateGenerationService(database)
        unmapped = service.get_unmapped_resources()
        
        # sample_igot_resource has no mapping, so should appear
        unmapped_ids = [str(r["_id"]) for r in unmapped]
        assert str(sample_igot_resource) in unmapped_ids


class TestRecommendationService:
    """Tests for recommendation service."""

    def test_service_initialization(self, database):
        """Test service can be created."""
        service = RecommendationService(database)
        assert service.db is not None

    def test_get_resource_details(self, database, sample_igot_resource):
        """Test retrieving resource details."""
        service = RecommendationService(database)
        resource = service.get_resource_details("IGOT-12345")
        
        assert resource is not None
        assert resource["resource_id"] == "IGOT-12345"

    def test_get_resources_by_competency(self, database, sample_competency, sample_mappings):
        """Test getting resources for a competency."""
        service = RecommendationService(database)
        resources = service.get_resources_by_competency("STAT-SAMPLING")
        
        assert len(resources) >= 2

    def test_get_resources_by_competency_filtered(self, database, sample_competency, sample_mappings):
        """Test getting resources for a competency filtered by provider."""
        service = RecommendationService(database)
        resources = service.get_resources_by_competency("STAT-SAMPLING", "IGOT")
        
        assert len(resources) >= 1
        assert all(r["provider"] == "IGOT" for r in resources)


class TestProviderNullCourseId:
    """Tests specific to NULL course_id handling for NSSTA/MoSPI."""

    def test_nssta_resource_has_null_course_id(self, database, sample_nssta_resource):
        """Verify NSSTA resource preserves NULL course_id."""
        resource = database.learning_resources.find_one({"_id": sample_nssta_resource})
        
        assert resource["provider"] == "NSSTA"
        assert resource["provider_specific"]["course_id"] is None
        assert resource["resource_id"].startswith("NSSTA-PROTO-")

    def test_nssta_provider_handles_null_course_id(self, database, sample_nssta_resource):
        """Test NSSTA provider correctly handles NULL course_id."""
        provider = PrototypeNSSTAProvider(database)
        resource = database.learning_resources.find_one({"_id": sample_nssta_resource})
        
        assert provider.validate_resource(resource) is True

    def test_igot_resources_never_have_null_course_id(self, database, sample_igot_resource):
        """Verify iGOT resources always have valid course_id."""
        resource = database.learning_resources.find_one({"_id": sample_igot_resource})
        
        assert resource["provider"] == "IGOT"
        assert resource["provider_specific"]["course_id"] is not None
        assert resource["provider_specific"]["course_id"] == "12345"


class TestProviderSeparation:
    """Tests for provider separation in recommendations."""

    def test_candidates_separated_by_provider(self, database, sample_competency, sample_mappings):
        """Test that candidates correctly identify their provider."""
        repo = LearningResourceRepository(database)
        resources = repo.get_resources_by_competency("STAT-SAMPLING")
        
        igot_resources = [r for r in resources if r["provider"] == "IGOT"]
        nssta_resources = [r for r in resources if r["provider"] == "NSSTA"]
        
        assert len(igot_resources) >= 1
        assert len(nssta_resources) >= 1
