from datetime import UTC, datetime, timedelta

import jwt
import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import require_admin
from app.auth.schemas import AccessRole
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

    def insert_one(self, document: dict) -> None:
        if self.find_one({"email": document["email"]}) or self.find_one({"employee_id": document["employee_id"]}):
            raise DuplicateKeyError("duplicate user")
        document.setdefault("_id", ObjectId())
        self.documents.append(document)

    def update_one(self, query: dict, update: dict) -> None:
        document = self.find_one(query)
        if document is not None:
            document.update(update.get("$set", {}))


class FakeDatabase:
    def __init__(self) -> None:
        self.role_id = ObjectId()
        self.roles = FakeCollection([{"_id": self.role_id, "role_code": "STATISTICAL_OFFICER", "status": "active"}])
        self.users = FakeCollection()


def make_client() -> tuple[TestClient, FakeDatabase]:
    database = FakeDatabase()
    application = create_app(Settings(
        mongodb_uri="mongodb://test",
        mongodb_database="test",
        jwt_secret="test-secret-with-at-least-32-bytes",
        jwt_access_token_expire_minutes=60,
    ))
    application.state.database = database
    return TestClient(application), database


def registration_payload(role_id: ObjectId, email: str = "Employee@Example.COM", employee_id: str = "EMP-001") -> dict:
    return {
        "email": email,
        "password": "correct-horse-battery",
        "full_name": "Example Employee",
        "role_id": str(role_id),
        "designation": "Statistical Officer",
        "department": "Statistics",
        "employee_id": employee_id,
    }


def register_and_login(client: TestClient, database: FakeDatabase, email: str, employee_id: str) -> str:
    response = client.post("/api/v1/auth/register", json=registration_payload(database.role_id, email, employee_id))
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_registration_normalizes_email_and_never_returns_password_hash() -> None:
    client, database = make_client()

    response = client.post("/api/v1/auth/register", json=registration_payload(database.role_id))

    assert response.status_code == 201
    assert response.json()["email"] == "employee@example.com"
    assert "password_hash" not in response.json()
    assert database.users.documents[0]["password_hash"] != "correct-horse-battery"
    client.close()


def test_duplicate_email_invalid_role_and_weak_password_are_rejected() -> None:
    client, database = make_client()
    payload = registration_payload(database.role_id)
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json={**payload, "employee_id": "EMP-002"}).status_code == 409
    assert client.post("/api/v1/auth/register", json={**payload, "email": "new@example.com", "role_id": str(ObjectId()), "employee_id": "EMP-003"}).status_code == 422
    assert client.post("/api/v1/auth/register", json={**payload, "email": "new@example.com", "employee_id": "EMP-003", "password": "short"}).status_code == 422
    client.close()


def test_login_me_and_profile_update_work_with_custom_jwt_settings() -> None:
    client, database = make_client()
    token = register_and_login(client, database, "employee@example.com", "EMP-001")
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    profile = client.put("/api/v1/users/me", headers=headers, json={"department": "Updated Statistics"})

    assert profile.status_code == 200
    assert profile.json()["department"] == "Updated Statistics"
    assert client.get("/api/v1/users/me", headers=headers).json()["department"] == "Updated Statistics"
    client.close()


def test_protected_routes_reject_missing_invalid_and_expired_tokens() -> None:
    client, database = make_client()
    register_and_login(client, database, "employee@example.com", "EMP-001")
    expired = jwt.encode(
        {"sub": str(database.users.documents[0]["_id"]), "exp": datetime.now(UTC) - timedelta(minutes=1)},
        "test-secret-with-at-least-32-bytes",
        algorithm="HS256",
    )

    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    client.close()


def test_wrong_unknown_and_inactive_logins_are_generic_failures() -> None:
    client, database = make_client()
    register_and_login(client, database, "employee@example.com", "EMP-001")

    assert client.post("/api/v1/auth/login", json={"email": "employee@example.com", "password": "wrong-password"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "unknown@example.com", "password": "wrong-password"}).json() == {"detail": "Invalid email or password"}
    database.users.documents[0]["status"] = "inactive"
    assert client.post("/api/v1/auth/login", json={"email": "employee@example.com", "password": "correct-horse-battery"}).json() == {"detail": "Invalid email or password"}
    client.close()


def test_users_are_isolated_and_profile_cannot_change_role() -> None:
    client, database = make_client()
    token_a = register_and_login(client, database, "a@example.com", "EMP-001")
    token_b = register_and_login(client, database, "b@example.com", "EMP-002")

    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"role_id": str(database.role_id)},
    )

    assert response.status_code == 422
    assert client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_b}"}).json()["email"] == "b@example.com"
    assert client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"department": "A Department"},
    ).json()["department"] == "A Department"
    assert database.users.find_one({"email": "b@example.com"})["department"] == "Statistics"
    client.close()


def test_admin_dependency_distinguishes_application_access_role() -> None:
    with pytest.raises(HTTPException) as error:
        require_admin({"access_role": AccessRole.EMPLOYEE.value})

    assert error.value.status_code == 403
    assert require_admin({"access_role": AccessRole.ADMIN.value})["access_role"] == "ADMIN"
