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
