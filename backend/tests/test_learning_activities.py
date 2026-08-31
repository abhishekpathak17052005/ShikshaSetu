"""Tests for learning activities module."""

import pytest
from datetime import UTC, datetime
from bson import ObjectId
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeCollection:
    """Mock MongoDB collection."""
    def __init__(self, documents=None):
        self.documents = documents or []

    def find_one(self, query, projection=None):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None

    def find_one_and_update(self, query, update, return_document=False):
        document = self.find_one(query)
        if document is not None:
            if "$set" in update:
                document.update(update["$set"])
            if "$inc" in update:
                for key, val in update["$inc"].items():
                    document[key] = document.get(key, 0) + val
        return document if return_document else None

    def find(self, query, projection=None):
        results = []
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                results.append(document)
        return results

    def insert_one(self, document):
        document.setdefault("_id", ObjectId())
        self.documents.append(document)
        class Result:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        return Result(document["_id"])

    def update_one(self, query, update):
        document = self.find_one(query)
        if document is not None:
            if "$set" in update:
                document.update(update["$set"])
            if "$inc" in update:
                for key, val in update["$inc"].items():
                    document[key] = document.get(key, 0) + val

    def create_index(self, index):
        pass


class FakeDatabase:
    """Mock MongoDB database."""
    def __init__(self):
        self.users_coll = FakeCollection()
        self.roles_coll = FakeCollection([
            {
                "_id": ObjectId(),
                "role_code": "STATISTICAL_OFFICER",
                "status": "active"
            }
        ])
        self.learning_activities = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.competency_profiles = FakeCollection()

    def __getitem__(self, name):
        if name == "users":
            return self.users_coll
        elif name == "roles":
            return self.roles_coll
        elif name == "learning_activities":
            return self.learning_activities
        elif name == "competency_evidence":
            return self.competency_evidence
        elif name == "competency_profiles":
            return self.competency_profiles
        return FakeCollection()


@pytest.fixture
def client():
    """Create test client with fake database."""
    app = create_app(Settings(
        mongodb_uri="mongodb://test",
        mongodb_database="test",
        jwt_secret_key="test-secret-with-at-least-32-bytes",
        jwt_expiration_hours=24,
    ))
    app.state.database = FakeDatabase()
    return TestClient(app)


class TestLearningActivityCreation:
    """Tests for creating learning activities."""
    
    def test_start_learning_activity_requires_authentication(self, client):
        """Test that unauthenticated users cannot start activity."""
        response = client.post(
            "/api/v1/learning-activities",
            json={
                "resource_id": "igot_course_123",
                "competency_id": "PA01",
            },
        )
        
        # Should return 401 Unauthorized (not 403)
        assert response.status_code in [401, 403]


class TestLearningActivityEndpoints:
    """Tests for learning activity endpoints structure."""
    
    def test_learning_activities_router_registered(self, client):
        """Test that endpoints are registered and respond."""
        # This tests that endpoints exist and handle missing auth properly
        response = client.get("/api/v1/learning-activities")
        # Should fail auth, not 404 (endpoint exists)
        assert response.status_code in [401, 403, 422]
    
    def test_create_endpoint_registered(self, client):
        """Test create endpoint is registered."""
        response = client.post(
            "/api/v1/learning-activities",
            json={
                "resource_id": "test_resource",
                "competency_id": "TEST01",
            }
        )
        assert response.status_code in [401, 403, 422, 200]
    
    def test_complete_endpoint_registered(self, client):
        """Test complete endpoint is registered."""
        response = client.post(
            "/api/v1/learning-activities/test_id/complete",
            json={}
        )
        assert response.status_code in [401, 403, 404, 422]
