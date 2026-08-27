from datetime import UTC, datetime

from bson import ObjectId
from fastapi.testclient import TestClient

from app.assessments.seed import HERO_COMPETENCY_CODES, seed_assessment
from app.auth.schemas import AccessRole
from app.auth.security import hash_password
from app.core.config import Settings
from app.main import create_app


class FakeResult:
    def __init__(self, upserted_id: ObjectId | None = None) -> None:
        self.upserted_id = upserted_id


class FakeCursor(list):
    def sort(self, key: str, direction: int):
        return FakeCursor(sorted(self, key=lambda item: item[key], reverse=direction < 0))


class FakeCollection:
    def __init__(self, documents: list[dict] | None = None) -> None:
        self.documents = documents or []

    def _matches(self, document: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = document.get(key)
            if isinstance(expected, dict) and "$in" in expected:
                if actual not in expected["$in"]:
                    return False
            elif actual != expected:
                return False
        return True

    def find(self, query: dict | None = None, projection: dict | None = None):
        return FakeCursor([item for item in self.documents if self._matches(item, query or {})])

    def find_one(self, query: dict, projection: dict | None = None) -> dict | None:
        return next((item for item in self.documents if self._matches(item, query)), None)

    def insert_one(self, document: dict) -> None:
        document.setdefault("_id", ObjectId())
        self.documents.append(document)

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> FakeResult:
        document = self.find_one(query)
        if document is None and upsert:
            document = {key: value for key, value in query.items() if not isinstance(value, dict)}
            document.update(update.get("$setOnInsert", {}))
            document.update(update.get("$set", {}))
            document.setdefault("_id", ObjectId())
            self.documents.append(document)
            return FakeResult(document["_id"])
        if document is not None:
            document.update(update.get("$set", {}))
        return FakeResult()

    def bulk_write(self, operations: list) -> None:
        for operation in operations:
            self.update_one(operation._filter, operation._doc, operation._upsert)

    def create_index(self, *args, **kwargs) -> str:
        return kwargs.get("name", "index")

    def count_documents(self, query: dict) -> int:
        return sum(self._matches(item, query) for item in self.documents)


class FakeDatabase:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.competency_ids = {code: ObjectId() for code in HERO_COMPETENCY_CODES}
        self.competencies = FakeCollection([{"_id": identifier, "code": code} for code, identifier in self.competency_ids.items()])
        role_id = ObjectId()
        self.roles = FakeCollection([{"_id": role_id, "status": "active", "role_code": "STATISTICAL_OFFICER"}])
        self.users = FakeCollection()
        self.assessments = FakeCollection()
        self.assessment_attempts = FakeCollection()
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.now = now


def make_client() -> tuple[TestClient, FakeDatabase]:
    database = FakeDatabase()
    seed_assessment(database)
    application = create_app(Settings(
        mongodb_uri="mongodb://test",
        mongodb_database="test",
        jwt_secret="test-secret-with-at-least-32-bytes",
    ))
    application.state.database = database
    return TestClient(application), database


def register(client: TestClient, database: FakeDatabase, email: str, employee_id: str) -> str:
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "correct-horse-battery",
        "full_name": email,
        "role_id": str(database.roles.documents[0]["_id"]),
        "designation": "Statistical Officer",
        "department": "Statistics",
        "employee_id": employee_id,
    })
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "correct-horse-battery"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_assessment_seed_is_idempotent() -> None:
    database = FakeDatabase()
    assert seed_assessment(database) == {"assessments": 1, "questions": 24, "competencies": 8}
    assert seed_assessment(database) == {"assessments": 1, "questions": 24, "competencies": 8}
    assert len(database.assessments.documents) == 1


def test_assessment_flow_redacts_answers_and_updates_evidence_and_profile() -> None:
    client, database = make_client()
    token = register(client, database, "assessment@example.com", "ASSESS-001")
    headers = {"Authorization": f"Bearer {token}"}

    started = client.post("/api/v1/assessments", headers=headers, json={})
    assert started.status_code == 201
    attempt_id = started.json()["id"]
    assert all("correct_answer" not in question for question in started.json()["questions"])

    questions = started.json()["questions"]
    answers = [{"question_id": question["question_id"], "answer": question["options"][0]} for question in questions if question["question_type"] != "SELF_RATING"]
    self_ratings = {competency_id: 3 for competency_id in [str(identifier) for identifier in database.competency_ids.values()]}
    payload = {"self_ratings": self_ratings, "answers": answers, "training_evidence": [{"training_name": "Sampling Basics", "provider": "Prototype Provider", "competencies": [str(database.competency_ids["STAT_SAMPLING"])]}]}

    submitted = client.post(f"/api/v1/assessments/{attempt_id}/submit", headers=headers, json=payload)

    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"
    assert len(submitted.json()["competency_results"]) == 8
    retrieved = client.get(f"/api/v1/assessments/{attempt_id}", headers=headers)
    assert len(retrieved.json()["competency_results"]) == 8
    assert len(database.competency_profiles.documents) == 8
    assert len(database.competency_evidence.documents) == 25
    assert database.competency_evidence.documents[0]["assessment_id"] == database.assessment_attempts.documents[0]["assessment_id"]
    assert client.post(f"/api/v1/assessments/{attempt_id}/submit", headers=headers, json=payload).status_code == 409
    client.close()


def test_user_cannot_access_another_users_attempt() -> None:
    client, database = make_client()
    token_a = register(client, database, "a-assessment@example.com", "ASSESS-002")
    token_b = register(client, database, "b-assessment@example.com", "ASSESS-003")
    attempt = client.post("/api/v1/assessments", headers={"Authorization": f"Bearer {token_a}"}, json={}).json()

    response = client.get(f"/api/v1/assessments/{attempt['id']}", headers={"Authorization": f"Bearer {token_b}"})

    assert response.status_code == 404
    client.close()
