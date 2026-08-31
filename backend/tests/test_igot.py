"""Tests for iGOT Karmayogi Ecosystem Integration Boundary & Endpoints."""

import pytest
from bson import ObjectId
from datetime import datetime, UTC
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app
from app.igot.adapter import IGOTAdapter
from app.igot.prototype_adapter import PrototypeIGOTAdapter
from app.igot.service import IGOTEcosystemService


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


class FakeLearningResourcesCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    def find(self, query=None, projection=None):
        docs = self.documents
        if query:
            filtered = []
            for d in docs:
                match = True
                for k, v in query.items():
                    if k == "competencies":
                        if v not in d.get("competencies", []):
                            match = False
                    elif k == "title" and isinstance(v, dict) and "$regex" in v:
                        if v["$regex"].lower() not in d.get("title", "").lower():
                            match = False
                    elif k == "$or":
                        or_match = False
                        for sub in v:
                            if any(d.get(sk) == sv or d.get("provider_specific", {}).get(sk.replace("provider_specific.", "")) == sv for sk, sv in sub.items()):
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
        cursor = self.find(query)
        docs = list(cursor.documents)
        return docs[0] if docs else None

    def count_documents(self, query=None):
        cursor = self.find(query)
        return len(cursor.documents)

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = ObjectId()
        self.documents.append(document)
        return type("InsertResult", (), {"inserted_id": document["_id"]})()


class FakeUserCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    def find_one(self, query, projection=None):
        for d in self.documents:
            if "_id" in query and d.get("_id") == query["_id"]:
                return d
            if "email" in query and d.get("email") == query["email"]:
                return d
        return None

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = ObjectId()
        self.documents.append(document)
        return type("InsertResult", (), {"inserted_id": document["_id"]})()


class FakeDatabase:
    def __init__(self):
        self.users = FakeUserCollection()
        self.learning_resources = FakeLearningResourcesCollection()


@pytest.fixture
def test_setup():
    db = FakeDatabase()
    settings = Settings(
        jwt_secret="igot-test-secret-key-32-chars-long",
        api_prefix="/api/v1",
        igot_integration_mode="prototype",
    )
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    # Seed User
    user_id = ObjectId()
    user = {
        "_id": user_id,
        "email": "official@shikshasetu.gov.in",
        "password_hash": hash_password("Password@123"),
        "full_name": "Test Officer",
        "designation": "Statistical Officer",
        "department": "Ministry of Statistics",
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(user)
    token = create_access_token(str(user_id), settings)
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Seed Sample iGOT Courses
    course_1 = {
        "_id": ObjectId(),
        "resource_id": "igot-001",
        "provider": "IGOT",
        "resource_type": "COURSE",
        "title": "Python for Public Policy Analysis",
        "metadata": {
            "duration_hours": 4.5,
            "difficulty": "Intermediate",
            "target_roles": ["Statistical Officer"],
        },
        "competencies": ["TECH_PYTHON", "DATA_ANALYSIS"],
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": "https://igotkarmayogi.gov.in/course/py-101",
            "source_document": "SRC-01",
            "verification_status": "VERIFIED",
        },
        "provider_specific": {
            "course_id": "do_113884879201",
            "course_url": "https://igotkarmayogi.gov.in/course/py-101",
            "provider_name": "iGOT Karmayogi",
        },
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    course_2 = {
        "_id": ObjectId(),
        "resource_id": "igot-002",
        "provider": "IGOT",
        "resource_type": "COURSE",
        "title": "Sampling Methods in Official Surveys",
        "metadata": {
            "duration_hours": 3.0,
            "difficulty": "Advanced",
            "target_roles": ["Statistical Officer"],
        },
        "competencies": ["STAT_SAMPLING"],
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": "https://igotkarmayogi.gov.in/course/stat-201",
            "source_document": "SRC-01",
            "verification_status": "VERIFIED",
        },
        "provider_specific": {
            "course_id": "do_113884879202",
            "course_url": "https://igotkarmayogi.gov.in/course/stat-201",
            "provider_name": "iGOT Karmayogi",
        },
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Non-iGOT course to ensure filtering works
    course_nssta = {
        "_id": ObjectId(),
        "resource_id": "nssta-001",
        "provider": "NSSTA",
        "resource_type": "TRAINING_PROGRAMME",
        "title": "NSSTA In-Service Training",
        "competencies": ["STAT_SAMPLING"],
        "status": "ACTIVE",
    }

    db.learning_resources.insert_one(course_1)
    db.learning_resources.insert_one(course_2)
    db.learning_resources.insert_one(course_nssta)

    return client, auth_headers, db, settings


def test_igot_status_unauthenticated(test_setup):
    client, _, _, _ = test_setup
    res = client.get("/api/v1/igot/status")
    assert res.status_code == 401


def test_igot_status_authenticated(test_setup):
    client, auth_headers, _, _ = test_setup
    res = client.get("/api/v1/igot/status", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["integration_mode"] == "prototype"
    assert data["catalog_available"] is True
    assert data["total_courses_available"] == 2
    assert data["live_gateway_available"] is False
    assert data["official_credentials_configured"] is False
    assert "Pending official" in data["status_notice"] or "Curated Catalog Connected" in data["status_notice"]
    assert len(data["supported_capabilities"]) > 0


def test_igot_courses_list_all(test_setup):
    client, auth_headers, _, _ = test_setup
    res = client.get("/api/v1/igot/courses", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["provider"] == "IGOT"
    assert len(data["courses"]) == 2
    titles = [c["title"] for c in data["courses"]]
    assert "Python for Public Policy Analysis" in titles
    assert "Sampling Methods in Official Surveys" in titles


def test_igot_courses_filter_by_competency(test_setup):
    client, auth_headers, _, _ = test_setup
    res = client.get("/api/v1/igot/courses?competency=TECH_PYTHON", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["courses"][0]["title"] == "Python for Public Policy Analysis"
    assert "TECH_PYTHON" in data["courses"][0]["competencies"]


def test_igot_courses_search_query(test_setup):
    client, auth_headers, _, _ = test_setup
    res = client.get("/api/v1/igot/courses?search=Sampling", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["courses"][0]["title"] == "Sampling Methods in Official Surveys"


def test_prototype_adapter_direct_methods(test_setup):
    _, _, db, _ = test_setup
    adapter = PrototypeIGOTAdapter(db)
    assert adapter.get_integration_mode() == "prototype"
    assert adapter.is_live_available() is False
    assert adapter.count_courses() == 2
    assert adapter.count_courses("STAT_SAMPLING") == 1

    course = adapter.get_course_by_id("igot-001")
    assert course is not None
    assert course["title"] == "Python for Public Policy Analysis"

    course_by_karmayogi_id = adapter.get_course_by_id("do_113884879202")
    assert course_by_karmayogi_id is not None
    assert course_by_karmayogi_id["title"] == "Sampling Methods in Official Surveys"
