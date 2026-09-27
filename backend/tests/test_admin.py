"""Tests for Admin Organizational Intelligence endpoints and RBAC enforcement."""

import pytest
from bson import ObjectId
from datetime import datetime, UTC
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    def find(self, query=None, projection=None):
        if not query:
            return list(self.documents)
        return [d for d in self.documents if all(d.get(k) == v for k, v in query.items())]

    def find_one(self, query, projection=None):
        for d in self.documents:
            if all(d.get(k) == v for k, v in query.items()):
                return d
        return None

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = ObjectId()
        self.documents.append(document)
        return type("InsertResult", (), {"inserted_id": document["_id"]})()


class FakeDatabase:
    def __init__(self):
        self.users = FakeCollection()
        self.roles = FakeCollection()
        self.role_requirements = FakeCollection()
        self.competencies = FakeCollection()
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.learning_activities = FakeCollection()
        self.quizzes = FakeCollection()
        self.quiz_attempts = FakeCollection()
        self.capability_assessments = FakeCollection()
        self.learning_resources = FakeCollection()


@pytest.fixture
def test_setup():
    db = FakeDatabase()
    settings = Settings(jwt_secret="admin-test-secret-key-32-chars-long", api_prefix="/api/v1")
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    # Seed Admin User
    admin_id = ObjectId()
    admin_user = {
        "_id": admin_id,
        "email": "admin@shikshasetu.test",
        "full_name": "Admin User",
        "access_role": "ADMIN",
        "status": "active",
        "password_hash": hash_password("pass123"),
        "department": "DoPT",
        "designation": "Director",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(admin_user)
    admin_token = create_access_token(str(admin_id), settings)

    # Seed Trainer User
    trainer_id = ObjectId()
    trainer_user = {
        "_id": trainer_id,
        "email": "trainer@shikshasetu.test",
        "full_name": "Trainer User",
        "access_role": "TRAINER",
        "status": "active",
        "password_hash": hash_password("pass123"),
        "department": "CBC",
        "designation": "Lead Trainer",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(trainer_user)
    trainer_token = create_access_token(str(trainer_id), settings)

    # Seed Official User
    official_id = ObjectId()
    official_user = {
        "_id": official_id,
        "email": "official@shikshasetu.test",
        "full_name": "Official User",
        "access_role": "OFFICIAL",
        "status": "active",
        "password_hash": hash_password("pass123"),
        "department": "MoSPI",
        "designation": "Statistical Officer",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(official_user)
    official_token = create_access_token(str(official_id), settings)

    # Seed Competency
    comp_id = ObjectId()
    db.competencies.insert_one({
        "_id": comp_id,
        "code": "STAT_DATA_ANALYSIS",
        "name": "Statistical Data Analysis",
        "domain": "DOMAIN",
    })

    return {
        "client": client,
        "admin_token": admin_token,
        "trainer_token": trainer_token,
        "official_token": official_token,
        "db": db,
    }


ADMIN_ENDPOINTS = [
    "/api/v1/admin/dashboard",
    "/api/v1/admin/workforce",
    "/api/v1/admin/competencies",
    "/api/v1/admin/skill-gaps",
    "/api/v1/admin/training-effectiveness",
    "/api/v1/admin/emerging-skills",
    "/api/v1/admin/capacity-planning",
    "/api/v1/admin/users",
    "/api/v1/admin/reports",
    "/api/v1/admin/workforce-intelligence",
    "/api/v1/admin/talent-discovery",
]


@pytest.mark.parametrize("endpoint", ADMIN_ENDPOINTS)
def test_admin_access_allowed_for_admin_role(test_setup, endpoint):
    client = test_setup["client"]
    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}
    res = client.get(endpoint, headers=headers)
    assert res.status_code == 200, f"Failed for {endpoint}: {res.text}"


@pytest.mark.parametrize("endpoint", ADMIN_ENDPOINTS)
def test_admin_access_forbidden_for_official(test_setup, endpoint):
    client = test_setup["client"]
    headers = {"Authorization": f"Bearer {test_setup['official_token']}"}
    res = client.get(endpoint, headers=headers)
    assert res.status_code == 403, f"Expected 403 for official on {endpoint}, got {res.status_code}"


@pytest.mark.parametrize("endpoint", ADMIN_ENDPOINTS)
def test_admin_access_forbidden_for_trainer(test_setup, endpoint):
    client = test_setup["client"]
    headers = {"Authorization": f"Bearer {test_setup['trainer_token']}"}
    res = client.get(endpoint, headers=headers)
    assert res.status_code == 403, f"Expected 403 for trainer on {endpoint}, got {res.status_code}"


@pytest.mark.parametrize("endpoint", ADMIN_ENDPOINTS)
def test_admin_access_unauthorized_without_token(test_setup, endpoint):
    client = test_setup["client"]
    res = client.get(endpoint)
    assert res.status_code == 401, f"Expected 401 on {endpoint}, got {res.status_code}"


def test_emerging_skills_uses_observed_gaps_and_no_forecast(test_setup):
    db = test_setup["db"]
    competency = db.competencies.documents[0]
    role_id = ObjectId()
    official = db.users.documents[2]
    official["role_id"] = role_id
    db.role_requirements.insert_one({
        "_id": ObjectId(),
        "role_id": role_id,
        "competency_id": competency["_id"],
        "required_level": 4,
    })
    db.competency_profiles.insert_one({
        "_id": ObjectId(),
        "user_id": official["_id"],
        "competency_id": competency["_id"],
        "current_level": 2,
    })

    response = test_setup["client"].get(
        "/api/v1/admin/emerging-skills",
        headers={"Authorization": f"Bearer {test_setup['admin_token']}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["historical_trend_available"] is False
    assert payload["emerging_capabilities"][0]["officials_in_deficit"] == 1
    assert payload["emerging_capabilities"][0]["average_gap_size"] == 2.0
    assert "urgency_score" not in payload["emerging_capabilities"][0]
    assert "demand_index" not in payload["emerging_capabilities"][0]


def test_workforce_intelligence_filters_department_and_reports_missing_history(test_setup):
    db = test_setup["db"]
    official = db.users.documents[2]
    official["role_id"] = ObjectId()
    response = test_setup["client"].get(
        "/api/v1/admin/workforce-intelligence?department=MoSPI",
        headers={"Authorization": f"Bearer {test_setup['admin_token']}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filters"]["department"] == "MoSPI"
    assert payload["overview"]["total_officials"] == 1
    assert payload["trends"]["available"] is False
    assert payload["trends"]["message"] == "Insufficient historical data"


def test_talent_discovery_requires_opt_in_and_paginates(test_setup):
    db = test_setup["db"]
    db.talent_preferences = FakeCollection()
    official = db.users.documents[2]
    competency = db.competencies.documents[0]
    db.competency_profiles.insert_one({
        "_id": ObjectId(),
        "user_id": official["_id"],
        "competency_id": competency["_id"],
        "current_level": 4.2,
        "confidence": 0.87,
    })
    db.competency_evidence.insert_one({
        "_id": ObjectId(),
        "user_id": official["_id"],
        "competency_id": competency["_id"],
        "evidence_type": "CAPABILITY_ASSESSMENT",
    })

    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}
    hidden = test_setup["client"].get("/api/v1/admin/talent-discovery", headers=headers)
    assert hidden.status_code == 200
    assert hidden.json()["total"] == 0

    db.talent_preferences.insert_one({"user_id": official["_id"], "opt_in_enabled": True})
    visible = test_setup["client"].get("/api/v1/admin/talent-discovery?page=1&limit=1", headers=headers)
    assert visible.status_code == 200
    payload = visible.json()
    assert payload["total"] == 1
    assert len(payload["results"]) == 1
    assert payload["results"][0]["evidence_backed"] is True
    assert payload["results"][0]["competencies"][0]["supporting_evidence_count"] == 1


def test_sparse_analytics_does_not_invent_emerging_or_capacity_values(test_setup):
    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}
    client = test_setup["client"]

    emerging = client.get("/api/v1/admin/emerging-skills", headers=headers)
    capacity = client.get("/api/v1/admin/capacity-planning", headers=headers)

    assert emerging.status_code == 200
    assert emerging.json()["emerging_capabilities"] == []
    assert emerging.json()["historical_trend_available"] is False
    assert capacity.status_code == 200
    assert capacity.json()["interventions"] == []
    assert capacity.json()["total_officials_requiring_intervention"] == 0
    assert capacity.json()["total_training_hours_required"] is None


def test_capacity_planning_uses_real_gaps_and_does_not_fabricate_resource_data(test_setup):
    db = test_setup["db"]
    competency = db.competencies.documents[0]
    role_id = ObjectId()
    official = db.users.documents[2]
    official["role_id"] = role_id
    db.role_requirements.insert_one({
        "_id": ObjectId(),
        "role_id": role_id,
        "competency_id": competency["_id"],
        "required_level": 4,
    })
    db.competency_profiles.insert_one({
        "_id": ObjectId(),
        "user_id": official["_id"],
        "competency_id": competency["_id"],
        "current_level": 3,
    })

    response = test_setup["client"].get(
        "/api/v1/admin/capacity-planning",
        headers={"Authorization": f"Bearer {test_setup['admin_token']}"},
    )

    assert response.status_code == 200
    intervention = response.json()["interventions"][0]
    assert intervention["target_officials_count"] == 1
    assert intervention["estimated_training_hours"] is None
    assert intervention["suggested_cohort_size"] is None
    assert intervention["recommended_courses_count"] == 0
    assert intervention["top_resource_title"] is None
    assert intervention["top_resource_provider"] is None


def test_unresolved_user_shows_role_mapping_pending_in_admin_workforce(test_setup):
    db = test_setup["db"]
    # Seed unresolved official (role_id is None)
    unresolved_id = ObjectId()
    unresolved_user = {
        "_id": unresolved_id,
        "email": "unresolved@shikshasetu.test",
        "full_name": "Unresolved Officer",
        "access_role": "OFFICIAL",
        "status": "active",
        "department": "Unknown Department",
        "designation": "Specialist",
        "role_id": None,
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(unresolved_user)

    headers = {"Authorization": f"Bearer {test_setup['admin_token']}"}
    client = test_setup["client"]

    workforce_res = client.get("/api/v1/admin/workforce", headers=headers)
    assert workforce_res.status_code == 200
    workforce_data = workforce_res.json()
    unresolved_emp = next((e for e in workforce_data["employees"] if e["id"] == str(unresolved_id)), None)
    assert unresolved_emp is not None
    assert unresolved_emp["professional_role"] == "Role Mapping Pending"

    users_res = client.get("/api/v1/admin/users", headers=headers)
    assert users_res.status_code == 200
    users_data = users_res.json()
    unresolved_u = next((u for u in users_data["users"] if u["id"] == str(unresolved_id)), None)
    assert unresolved_u is not None
    assert unresolved_u["professional_role"] in ("Unresolved", "Role Mapping Pending")
