"""Tests for capability assessment configuration system."""
from datetime import UTC, datetime

from bson import ObjectId
import pytest

from app.assessments import service, repository
from app.assessments.schemas import AssessmentConfiguration


class TestAssessmentConfiguration:
    """Test assessment configuration CRUD and retrieval."""

    @pytest.fixture
    def sample_config(self):
        """Sample assessment configuration."""
        return {
            "competency_code": "TECH_SQL",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
            "time_limit_minutes": 30,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    def test_assessment_configuration_schema_valid(self, sample_config):
        """Test that sample configuration validates."""
        config = AssessmentConfiguration(**sample_config)
        assert config.competency_code == "TECH_SQL"
        assert config.assessment_types == ["MCQ", "SCENARIO"]
        assert config.number_of_questions == 10
        assert config.passing_threshold == 70.0

    def test_assessment_configuration_schema_invalid_types(self, sample_config):
        """Test that invalid assessment types are rejected."""
        sample_config["assessment_types"] = ["MCQ", "INVALID"]
        with pytest.raises(ValueError, match="Invalid assessment types"):
            AssessmentConfiguration(**sample_config)

    def test_assessment_configuration_schema_invalid_threshold(self, sample_config):
        """Test that invalid passing threshold is rejected."""
        sample_config["passing_threshold"] = 150.0  # > 100
        with pytest.raises(ValueError):
            AssessmentConfiguration(**sample_config)

    def test_assessment_configuration_schema_invalid_difficulty(self, sample_config):
        """Test that invalid difficulty is rejected."""
        sample_config["difficulty"] = "IMPOSSIBLE"
        with pytest.raises(ValueError):
            AssessmentConfiguration(**sample_config)

    def test_assessment_configuration_defaults(self):
        """Test that configuration has reasonable defaults."""
        config = AssessmentConfiguration(competency_code="TECH_PYTHON")
        assert config.assessment_types == ["MCQ", "SCENARIO"]
        assert config.number_of_questions == 10
        assert config.difficulty == "MIXED"
        assert config.passing_threshold == 60.0
        assert config.allow_retake is True
        assert config.show_correct_answers_after is True

    def test_assessment_configuration_response_has_id(self):
        """Test that response model properly aliases _id to id."""
        from app.assessments.schemas import AssessmentConfigurationResponse
        
        oid = ObjectId()
        doc = {
            "_id": str(oid),
            "competency_code": "TECH_SQL",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
            "time_limit_minutes": 30,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }
        response = AssessmentConfigurationResponse(**doc)
        assert response.id == str(oid)


class FakeCollection:
    """Fake MongoDB collection for testing."""
    
    def __init__(self):
        self.documents = []
    
    def find_one(self, query):
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None
    
    def find(self, query):
        return [doc for doc in self.documents if all(doc.get(k) == v for k, v in query.items())]
    
    def insert_one(self, doc):
        doc["_id"] = doc.get("_id", ObjectId())
        self.documents.append(doc)
        class Result:
            def __init__(self, oid):
                self.inserted_id = oid
        return Result(doc["_id"])
    
    def find_one_and_update(self, query, update, return_document=False):
        doc = self.find_one(query)
        if doc is None:
            return None
        if "$set" in update:
            doc.update(update["$set"])
        return doc if return_document else None
    
    def delete_many(self, query):
        self.documents = [d for d in self.documents if not all(d.get(k) == v for k, v in query.items())]


class FakeDatabase:
    """Fake MongoDB database for testing."""
    
    def __init__(self):
        self.assessment_configurations = FakeCollection()


class TestAssessmentConfigurationRepository:
    """Test repository functions."""
    
    def test_get_assessment_configuration_found(self):
        """Test retrieving existing configuration."""
        db = FakeDatabase()
        config = {
            "_id": ObjectId(),
            "competency_code": "TECH_SQL",
            "status": "ACTIVE",
            "assessment_types": ["MCQ"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
        }
        db.assessment_configurations.insert_one(config)
        
        result = repository.get_assessment_configuration(db, "TECH_SQL")
        assert result is not None
        assert result["competency_code"] == "TECH_SQL"
    
    def test_get_assessment_configuration_not_found(self):
        """Test retrieving nonexistent configuration."""
        db = FakeDatabase()
        result = repository.get_assessment_configuration(db, "NONEXISTENT")
        assert result is None
    
    def test_get_assessment_configuration_inactive(self):
        """Test that inactive configurations are not returned."""
        db = FakeDatabase()
        config = {
            "_id": ObjectId(),
            "competency_code": "TECH_SQL",
            "status": "INACTIVE",
            "assessment_types": ["MCQ"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
        }
        db.assessment_configurations.insert_one(config)
        
        result = repository.get_assessment_configuration(db, "TECH_SQL")
        assert result is None
    
    def test_get_all_assessment_configurations(self):
        """Test retrieving all active configurations."""
        db = FakeDatabase()
        configs = [
            {
                "_id": ObjectId(),
                "competency_code": "TECH_SQL",
                "status": "ACTIVE",
                "assessment_types": ["MCQ"],
                "number_of_questions": 10,
                "difficulty": "MIXED",
                "passing_threshold": 70.0,
            },
            {
                "_id": ObjectId(),
                "competency_code": "TECH_PYTHON",
                "status": "ACTIVE",
                "assessment_types": ["MCQ", "SCENARIO"],
                "number_of_questions": 12,
                "difficulty": "MIXED",
                "passing_threshold": 70.0,
            },
            {
                "_id": ObjectId(),
                "competency_code": "INACTIVE_COMP",
                "status": "INACTIVE",
                "assessment_types": ["MCQ"],
                "number_of_questions": 10,
                "difficulty": "MIXED",
                "passing_threshold": 70.0,
            },
        ]
        for config in configs:
            db.assessment_configurations.insert_one(config)
        
        results = repository.get_all_assessment_configurations(db)
        assert len(results) == 2
        assert all(r["status"] == "ACTIVE" for r in results)


class TestAssessmentConfigurationService:
    """Test service functions."""
    
    def test_get_assessment_configuration_service(self):
        """Test service retrieval of configuration."""
        from unittest.mock import MagicMock, patch
        
        db = MagicMock()
        config = {
            "_id": ObjectId(),
            "competency_code": "TECH_SQL",
            "status": "ACTIVE",
            "assessment_types": ["MCQ"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
        }
        
        # Mock repository function
        with patch.object(repository, 'get_assessment_configuration', return_value=config):
            result = service.get_assessment_configuration(db, "TECH_SQL")
            assert result["competency_code"] == "TECH_SQL"
            assert "id" in result
    
    def test_get_assessment_configuration_service_not_found(self):
        """Test service when configuration not found."""
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        
        db = MagicMock()
        
        with patch.object(repository, 'get_assessment_configuration', return_value=None):
            with pytest.raises(HTTPException, match="not found"):
                service.get_assessment_configuration(db, "NONEXISTENT")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
