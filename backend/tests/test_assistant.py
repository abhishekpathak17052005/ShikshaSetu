"""Tests for ShikshaSetu AI Virtual Capability Assistant (Karmayogi AI Co-Pilot)."""

import pytest
from bson import ObjectId
from datetime import datetime, UTC
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app
from app.assistant.service import AssistantService
from app.assistant.schemas import AssistantChatRequest


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, key, direction):
        return self

    def skip(self, n):
        self.documents = self.documents[n:]
        return self

    def limit(self, n):
        self.documents = self.documents[:n]
        return self

    def __iter__(self):
        return iter(self.documents)

    def __list__(self):
        return list(self.documents)


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    def find(self, query=None, projection=None):
        docs = self.documents
        if query:
            filtered = []
            for d in docs:
                match = True
                for k, v in query.items():
                    if k == "$or":
                        or_match = False
                        for sub in v:
                            if any(d.get(sk) == sv for sk, sv in sub.items()):
                                or_match = True
                        if not or_match:
                            match = False
                    elif d.get(k) != v:
                        match = False
                if match:
                    filtered.append(d)
            docs = filtered
        return FakeCursor(docs)

    def find_one(self, query, projection=None):
        if not query:
            return self.documents[0] if self.documents else None
        for d in self.documents:
            match = True
            for k, v in query.items():
                if d.get(k) != v:
                    match = False
            if match:
                return d
        return None

    def count_documents(self, query=None):
        return len(self.find(query).documents)

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = ObjectId()
        self.documents.append(document)
        return type("InsertResult", (), {"inserted_id": document["_id"]})()

    def index_information(self):
        return {}


class FakeDatabase:
    def __init__(self):
        self.users = FakeCollection()
        self.roles = FakeCollection()
        self.role_requirements = FakeCollection()
        self.competencies = FakeCollection()
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.learning_activities = FakeCollection()
        self.learning_resources = FakeCollection()
        self.document_chunks = FakeCollection()


@pytest.fixture
def test_setup():
    db = FakeDatabase()
    settings = Settings(
        jwt_secret="assistant-test-secret-key-32-chars-long",
        api_prefix="/api/v1",
        llm_provider="mock",
    )
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    # Seed User A (Statistical Officer with gaps)
    user_a_id = ObjectId()
    role_id = ObjectId()
    db.roles.insert_one({
        "_id": role_id,
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "status": "active",
    })

    user_a = {
        "_id": user_a_id,
        "email": "officer.a@shikshasetu.gov.in",
        "password_hash": hash_password("Password@123"),
        "full_name": "Rajesh Sharma",
        "designation": "Statistical Officer",
        "department": "Ministry of Statistics",
        "role_id": role_id,
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(user_a)

    # Seed User B
    user_b_id = ObjectId()
    user_b = {
        "_id": user_b_id,
        "email": "officer.b@shikshasetu.gov.in",
        "password_hash": hash_password("Password@123"),
        "full_name": "Ananya Mehta",
        "designation": "Programme Officer",
        "department": "Education",
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(user_b)

    token_a = create_access_token(str(user_a_id), settings)
    token_b = create_access_token(str(user_b_id), settings)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Seed Sample Resource
    db.learning_resources.insert_one({
        "_id": ObjectId(),
        "resource_id": "res-101",
        "provider": "IGOT",
        "title": "Sampling Techniques in Official Statistics",
        "competencies": ["STAT_SAMPLING"],
        "status": "ACTIVE",
        "source": {
            "source_document": "SRC-01",
            "source_url": "https://igotkarmayogi.gov.in/course/101",
            "verification_status": "VERIFIED",
        },
        "provider_specific": {
            "course_url": "https://igotkarmayogi.gov.in/course/101",
        }
    })

    return client, headers_a, headers_b, db, settings, str(user_a_id), str(user_b_id)


def test_assistant_chat_unauthenticated(test_setup):
    client, _, _, _, _, _, _ = test_setup
    res = client.post("/api/v1/assistant/chat", json={"message": "How can I improve my skills?"})
    assert res.status_code == 401


def test_assistant_chat_authenticated(test_setup):
    client, headers_a, _, _, _, _, _ = test_setup
    res = client.post(
        "/api/v1/assistant/chat",
        headers=headers_a,
        json={
            "message": "How can I improve my Sampling Methods competency?",
            "context_page": "Skill Gaps",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0
    assert "suggested_actions" in data
    assert len(data["suggested_actions"]) > 0


def test_assistant_user_isolation(test_setup):
    client, headers_a, headers_b, _, _, user_a_id, user_b_id = test_setup
    res_a = client.post("/api/v1/assistant/chat", headers=headers_a, json={"message": "Who am I?"})
    res_b = client.post("/api/v1/assistant/chat", headers=headers_b, json={"message": "Who am I?"})

    assert res_a.status_code == 200
    assert res_b.status_code == 200

    data_a = res_a.json()
    data_b = res_b.json()

    assert data_a["context_summary"]["profile"]["full_name"] == "Rajesh Sharma"
    assert data_b["context_summary"]["profile"]["full_name"] == "Ananya Mehta"


def test_assistant_suggested_actions_by_intent(test_setup):
    client, headers_a, _, _, _, _, _ = test_setup
    # Skill gap query
    res_gap = client.post("/api/v1/assistant/chat", headers=headers_a, json={"message": "What is my biggest gap?"})
    assert any(a["target_page"] == "Skill Gaps" for a in res_gap.json()["suggested_actions"])

    # Course query
    res_rec = client.post("/api/v1/assistant/chat", headers=headers_a, json={"message": "What iGOT course should I learn?"})
    assert any(a["target_page"] == "Recommendations" for a in res_rec.json()["suggested_actions"])

    # Quiz query
    res_quiz = client.post("/api/v1/assistant/chat", headers=headers_a, json={"message": "I want to take a test to validate my competency."})
    assert any(a["target_page"] in ("Quizzes", "Assessments") for a in res_quiz.json()["suggested_actions"])


def test_assistant_service_direct_fallback(test_setup):
    _, _, _, db, settings, user_a_id, _ = test_setup
    service = AssistantService(db, settings)
    resp = service.process_chat(
        user_id=user_a_id,
        request=AssistantChatRequest(message="Explain the governance rule for course completion"),
    )
    assert resp.answer
    assert "Supporting Evidence" in resp.answer or "Authoritative" in resp.answer or "SRC-01" in str(resp.sources)
