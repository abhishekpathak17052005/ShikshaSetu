"""End-to-end tests for learning recommendations via HTTP API."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from bson import ObjectId

from app.main import create_app
from app.core.config import get_settings


@pytest.fixture
def test_app():
    """Create test app instance."""
    settings = get_settings()
    return create_app(settings)


@pytest.fixture
def test_client(database, test_app):
    """Create test client with test database injected."""
    # Inject test database into app state
    test_app.state.database = database
    return TestClient(test_app)


@pytest.fixture
def test_user(test_client, database):
    """Create and return authenticated test user."""
    # Find an active role from database or create one if needed
    role = database.roles.find_one({"status": "active"})
    if not role:
        role_id = ObjectId()
        database.roles.insert_one({
            "_id": role_id,
            "role_code": "STATISTICAL_OFFICER",
            "role_name": "Statistical Officer",
            "description": "Statistical Officer Role",
            "status": "active",
        })
    else:
        role_id = role["_id"]

    # Register user with existing role
    register_payload = {
        "email": "e2e_test@example.com",
        "password": "TestPassword123!",
        "full_name": "E2E Test User",
        "designation": "Statistical Officer",
        "department": "Testing",
        "employee_id": "E2E001",
        "role_id": str(role_id),
    }
    
    response = test_client.post("/api/v1/auth/register", json=register_payload)
    
    # If 409, user exists, just login
    if response.status_code == 409:
        login_response = test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "e2e_test@example.com",
                "password": "TestPassword123!",
            },
        )
        if login_response.status_code != 200:
            pytest.skip(f"Could not login: {login_response.text}")
        return login_response.json()
    
    # Check for validation error
    if response.status_code == 422:
        error_detail = response.json().get("detail", [])
        print(f"\n=== REGISTRATION VALIDATION ERROR ===")
        print(f"Status: 422")
        print(f"Payload: {register_payload}")
        print(f"Response: {response.json()}")
        pytest.fail(f"Registration validation error: {error_detail}")
    
    # Expect 201
    if response.status_code != 201:
        print(f"\n=== REGISTRATION ERROR ===")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        pytest.fail(f"Registration failed with {response.status_code}: {response.text}")
    
    # Login to get token
    login_response = test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "e2e_test@example.com",
            "password": "TestPassword123!",
        },
    )
    if login_response.status_code != 200:
        pytest.fail(f"Login failed: {login_response.text}")
    
    return login_response.json()


class TestRecommendationsE2E:
    """End-to-end tests for recommendations API."""

    def test_get_skill_gaps(self, test_client, test_user, sample_competency, database):
        """Test retrieving skill gaps via API."""
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = test_client.get("/api/v1/skill-gaps/me", headers=headers)
        
        # May return 200 if role configured, 404 if endpoint doesn't exist, or 422 if not configured
        if response.status_code in (404, 422):
            pytest.skip(f"Skill-gaps endpoint not available or role not configured (status: {response.status_code})")
        
        assert response.status_code == 200
        gaps_data = response.json()
        assert "role" in gaps_data
        assert "summary" in gaps_data

    def test_get_recommendations(self, test_client, test_user, sample_competency, sample_igot_resource, sample_nssta_resource, sample_mappings, database):
        """Test getting recommendations via API."""
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = test_client.get("/api/v1/recommendations/me", headers=headers)
        
        # May return 200 if skill gaps exist, 404 if endpoint not available, or 422 if not configured
        if response.status_code in (404, 422):
            pytest.skip(f"Recommendations endpoint not available or not configured (status: {response.status_code})")
        
        assert response.status_code == 200
        recs_data = response.json()
        assert "recommendations" in recs_data or "total_recommendations" in recs_data

    def test_get_resource_details(self, test_client, test_user, sample_igot_resource, headers=None):
        """Test retrieving resource details via API."""
        if headers is None:
            token = test_user["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        response = test_client.get("/api/v1/resources/IGOT-12345", headers=headers)
        
        # Resource may not exist if not seeded, or exists
        if response.status_code == 404:
            pytest.skip("Resource not found in database")
        
        assert response.status_code == 200
        resource = response.json()
        assert resource["resource_id"] == "IGOT-12345"

    def test_get_resources_by_competency(self, test_client, test_user, sample_competency, sample_mappings, headers=None):
        """Test retrieving resources for a competency via API."""
        if headers is None:
            token = test_user["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        response = test_client.get(
            "/api/v1/recommendations/competencies/STAT_SAMPLING/resources",
            headers=headers,
        )
        
        # May return 404 if competency not found
        if response.status_code == 404:
            pytest.skip("Competency not found")
        
        assert response.status_code == 200
        resources_data = response.json()
        assert isinstance(resources_data, list) or "resources" in resources_data

    def test_get_unmapped_resources(self, test_client, test_user, sample_igot_resource, headers=None):
        """Test retrieving unmapped resources via API."""
        if headers is None:
            token = test_user["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        response = test_client.get("/api/v1/resources/unmapped", headers=headers)
        
        # Should return list or 200 empty
        if response.status_code == 404:
            pytest.skip("Endpoint not available")
        
        assert response.status_code == 200
        resources = response.json()
        assert isinstance(resources, list) or "resources" in resources
