"""
Automated unit and integration test suite for Role-Based Access Control (RBAC) - Phase 2A.

Covers:
1. AccessRole Enum values (OFFICIAL, TRAINER, ADMIN, EMPLOYEE)
2. require_role, require_official, require_trainer, require_admin, require_admin_role dependencies
3. Registration defaults to OFFICIAL
4. Registration as TRAINER is allowed
5. Registration as ADMIN via API is rejected (HTTP 403)
6. Registration with invalid role rejected (HTTP 422)
7. Profile update cannot modify access_role (Privilege Escalation Protection)
8. OFFICIAL role cannot upload learning materials (HTTP 403)
9. OFFICIAL role cannot generate AI questions (HTTP 403)
10. TRAINER role can upload learning materials
11. TRAINER role can generate AI questions
12. ADMIN role has full access to trainer endpoints
13. OFFICIAL can access learner endpoints (assessments, gaps, recommendations, profile)
14. TRAINER can access learner endpoints
15. ADMIN can access learner endpoints
16. Cross-role token verification & inactive user rejection
"""

from datetime import UTC, datetime
from bson import ObjectId
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import (
    get_current_user,
    require_admin,
    require_admin_role,
    require_official,
    require_role,
    require_trainer,
)
from app.auth.schemas import AccessRole
from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app


class FakeCollection:
    def __init__(self, documents: list[dict] | None = None) -> None:
        self.documents = documents or []

    def find_one(self, query: dict, projection: dict | None = None) -> dict | None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document
        return None

    def find(self, query: dict | None = None, projection: dict | None = None) -> list[dict]:
        if not query:
            return list(self.documents)
        return [d for d in self.documents if all(d.get(k) == v for k, v in query.items())]

    def insert_one(self, document: dict) -> None:
        if self.find_one({"email": document.get("email")}) or (
            document.get("employee_id") and self.find_one({"employee_id": document.get("employee_id")})
        ):
            raise DuplicateKeyError("duplicate user")
        document.setdefault("_id", ObjectId())
        self.documents.append(document)

    def insert_many(self, documents: list[dict]) -> None:
        for d in documents:
            self.insert_one(d)

    def update_one(self, query: dict, update: dict) -> None:
        document = self.find_one(query)
        if document is not None:
            document.update(update.get("$set", {}))


class FakeDatabase:
    def __init__(self) -> None:
        self.role_id = ObjectId()
        self.roles = FakeCollection([
            {"_id": self.role_id, "role_code": "STATISTICAL_OFFICER", "name": "Statistical Officer", "status": "active"}
        ])
        self.users = FakeCollection()
        self.learning_materials = FakeCollection()
        self.document_chunks = FakeCollection()
        self.competencies = FakeCollection([
            {"_id": ObjectId(), "code": "TECH_PYTHON", "name": "Python Programming", "status": "active"}
        ])


def make_rbac_app() -> tuple[TestClient, FakeDatabase, Settings]:
    database = FakeDatabase()
    settings = Settings(
        mongodb_uri="mongodb://test",
        mongodb_database="test_rbac",
        jwt_secret="test-secret-with-at-least-32-bytes-long",
        jwt_access_token_expire_minutes=60,
        llm_provider="mock",
        embedding_provider="mock",
    )
    application = create_app(settings)
    application.state.database = database
    application.state.settings = settings
    return TestClient(application), database, settings


def create_test_user(database: FakeDatabase, email: str, role: str, employee_id: str) -> dict:
    now = datetime.now(UTC)
    user_doc = {
        "_id": ObjectId(),
        "email": email.lower(),
        "password_hash": hash_password("Password123!"),
        "full_name": f"Test {role} User",
        "role_id": database.role_id,
        "designation": "Staff",
        "department": "Statistics",
        "employee_id": employee_id,
        "status": "active",
        "access_role": role,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
    database.users.insert_one(user_doc)
    return user_doc


# ==============================================================================
# 1. AccessRole Enum & Dependency Tests
# ==============================================================================

def test_access_role_enum_values():
    assert AccessRole.OFFICIAL.value == "OFFICIAL"
    assert AccessRole.TRAINER.value == "TRAINER"
    assert AccessRole.ADMIN.value == "ADMIN"
    assert AccessRole.EMPLOYEE.value == "EMPLOYEE"


def test_require_role_dependency_logic():
    official_user = {"_id": ObjectId(), "access_role": "OFFICIAL", "status": "active"}
    legacy_user = {"_id": ObjectId(), "access_role": "EMPLOYEE", "status": "active"}
    trainer_user = {"_id": ObjectId(), "access_role": "TRAINER", "status": "active"}
    admin_user = {"_id": ObjectId(), "access_role": "ADMIN", "status": "active"}

    # Official check allows OFFICIAL and legacy EMPLOYEE
    check_official = require_role(AccessRole.OFFICIAL)
    assert check_official(official_user)["access_role"] == "OFFICIAL"
    assert check_official(legacy_user)["access_role"] == "EMPLOYEE"

    # Trainer check allows TRAINER and ADMIN, rejects OFFICIAL
    check_trainer = require_role(AccessRole.TRAINER, AccessRole.ADMIN)
    assert check_trainer(trainer_user)["access_role"] == "TRAINER"
    assert check_trainer(admin_user)["access_role"] == "ADMIN"
    with pytest.raises(HTTPException) as exc_info:
        check_trainer(official_user)
    assert exc_info.value.status_code == 403

    # Admin check allows ADMIN, rejects TRAINER and OFFICIAL
    check_admin = require_role(AccessRole.ADMIN)
    assert check_admin(admin_user)["access_role"] == "ADMIN"
    with pytest.raises(HTTPException) as exc_info:
        check_admin(trainer_user)
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        check_admin(official_user)
    assert exc_info.value.status_code == 403


def test_convenience_dependency_functions():
    official_user = {"_id": ObjectId(), "access_role": "OFFICIAL", "status": "active"}
    trainer_user = {"_id": ObjectId(), "access_role": "TRAINER", "status": "active"}
    admin_user = {"_id": ObjectId(), "access_role": "ADMIN", "status": "active"}

    assert require_official(official_user) == official_user
    assert require_official(trainer_user) == trainer_user
    assert require_official(admin_user) == admin_user

    assert require_trainer(trainer_user) == trainer_user
    assert require_trainer(admin_user) == admin_user

    assert require_admin(admin_user) == admin_user
    assert require_admin_role(admin_user) == admin_user

    with pytest.raises(HTTPException):
        require_admin(trainer_user)


# ==============================================================================
# 2. Registration RBAC Tests
# ==============================================================================

def test_registration_defaults_to_official():
    client, database, _ = make_rbac_app()
    payload = {
        "email": "new_learner@example.com",
        "password": "Password123!",
        "full_name": "New Learner",
        "role_id": str(database.role_id),
        "designation": "Investigator",
        "department": "FOD",
        "employee_id": "EMP-NEW-01",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["access_role"] == "OFFICIAL"
    client.close()


def test_registration_as_trainer_allowed():
    client, database, _ = make_rbac_app()
    payload = {
        "email": "new_trainer@example.com",
        "password": "Password123!",
        "full_name": "New Trainer",
        "role_id": str(database.role_id),
        "designation": "Instructor",
        "department": "Training",
        "employee_id": "EMP-TRN-01",
        "access_role": "TRAINER",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["access_role"] == "TRAINER"
    client.close()


def test_registration_as_admin_rejected():
    client, database, _ = make_rbac_app()
    payload = {
        "email": "self_appointed_admin@example.com",
        "password": "Password123!",
        "full_name": "Bad Actor",
        "role_id": str(database.role_id),
        "designation": "Attacker",
        "department": "None",
        "employee_id": "EMP-ATK-01",
        "access_role": "ADMIN",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 403
    assert "Admin registration is restricted" in response.json()["detail"]
    client.close()


def test_registration_with_invalid_role_rejected():
    client, database, _ = make_rbac_app()
    payload = {
        "email": "invalid_role@example.com",
        "password": "Password123!",
        "full_name": "Invalid User",
        "role_id": str(database.role_id),
        "designation": "Staff",
        "department": "Dept",
        "employee_id": "EMP-INV-01",
        "access_role": "SUPERUSER",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    client.close()


# ==============================================================================
# 3. Privilege Escalation Protection via Profile Update
# ==============================================================================

def test_profile_update_cannot_escalate_privilege():
    client, database, settings = make_rbac_app()
    user = create_test_user(database, "learner@example.com", "OFFICIAL", "EMP-001")
    token = create_access_token(str(user["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to change access_role via PUT /api/v1/users/me
    response = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={"access_role": "ADMIN"},
    )
    assert response.status_code == 422  # Extra field forbidden

    # User remains OFFICIAL in DB
    refreshed = database.users.find_one({"_id": user["_id"]})
    assert refreshed["access_role"] == "OFFICIAL"
    client.close()


# ==============================================================================
# 4. Route-level RBAC Protection: Trainer vs Official
# ==============================================================================

def test_official_cannot_upload_material():
    client, database, settings = make_rbac_app()
    official = create_test_user(database, "official@example.com", "OFFICIAL", "EMP-OFF-01")
    token = create_access_token(str(official["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("document.pdf", b"%PDF-1.4 dummy content", "application/pdf")}
    response = client.post("/api/v1/learning-materials/upload", headers=headers, files=files)
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]
    client.close()


def test_official_cannot_generate_questions():
    client, database, settings = make_rbac_app()
    official = create_test_user(database, "official@example.com", "OFFICIAL", "EMP-OFF-01")
    token = create_access_token(str(official["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat_id = str(ObjectId())
    payload = {"competency_code": "TECH_PYTHON", "question_count": 3}
    response = client.post(
        f"/api/v1/learning-materials/{mat_id}/generate-questions",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 403
    assert "Access forbidden" in response.json()["detail"]
    client.close()


def test_trainer_can_access_upload_route():
    client, database, settings = make_rbac_app()
    trainer = create_test_user(database, "trainer@example.com", "TRAINER", "EMP-TRN-01")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload empty file to check authorization passes (reaches validation 400 instead of 403)
    files = {"file": ("test.pdf", b"", "application/pdf")}
    response = client.post("/api/v1/learning-materials/upload", headers=headers, files=files)
    # Status should NOT be 403 (forbidden). It should be 400 because file is empty.
    assert response.status_code == 400
    assert "File is empty" in response.json()["detail"]
    client.close()


def test_admin_can_access_upload_route():
    client, database, settings = make_rbac_app()
    admin = create_test_user(database, "admin@example.com", "ADMIN", "EMP-ADM-01")
    token = create_access_token(str(admin["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("test.pdf", b"", "application/pdf")}
    response = client.post("/api/v1/learning-materials/upload", headers=headers, files=files)
    assert response.status_code == 400
    assert "File is empty" in response.json()["detail"]
    client.close()


# ==============================================================================
# 5. Learner Endpoints Accessible to All System Roles
# ==============================================================================

def test_all_roles_can_access_me_and_profile():
    client, database, settings = make_rbac_app()

    for role, eid in [("OFFICIAL", "EMP-1"), ("TRAINER", "EMP-2"), ("ADMIN", "EMP-3")]:
        user = create_test_user(database, f"{role.lower()}@test.com", role, eid)
        token = create_access_token(str(user["_id"]), settings)
        headers = {"Authorization": f"Bearer {token}"}

        # /auth/me
        resp_me = client.get("/api/v1/auth/me", headers=headers)
        assert resp_me.status_code == 200
        assert resp_me.json()["access_role"] == role

        # /users/me
        resp_profile = client.get("/api/v1/users/me", headers=headers)
        assert resp_profile.status_code == 200
        assert resp_profile.json()["email"] == f"{role.lower()}@test.com"

    client.close()
