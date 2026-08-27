"""
Integration tests for skill gaps API.

Tests the full flow: authentication → role resolution → gap calculation → response.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeCollection:
    """Mock MongoDB collection for testing."""

    def __init__(self):
        self.documents = []

    def find_one(self, query: dict, projection: dict = None) -> dict | None:
        for doc in self.documents:
            if self._matches_query(doc, query):
                if projection:
                    result = {}
                    for k in projection:
                        if k in doc:
                            result[k] = doc[k]
                    return result
                return doc
        return None

    def _matches_query(self, doc: dict, query: dict) -> bool:
        """Check if document matches MongoDB-like query."""
        for key, value in query.items():
            if key not in doc:
                return False
            if isinstance(value, dict):
                # Handle MongoDB operators like {"$in": [...]}
                if "$in" in value:
                    if doc[key] not in value["$in"]:
                        return False
                else:
                    if doc[key] != value:
                        return False
            else:
                if doc[key] != value:
                    return False
        return True

    def find(self, query: dict, projection: dict = None):
        results = []
        for doc in self.documents:
            if self._matches_query(doc, query):
                if projection:
                    result = {}
                    for k in projection:
                        if k in doc:
                            result[k] = doc[k]
                    results.append(result)
                else:
                    results.append(doc)
        return results

    def insert_one(self, document: dict) -> None:
        self.documents.append(document)

    def insert_many(self, documents: list[dict]) -> None:
        self.documents.extend(documents)

    def update_one(self, query: dict, update: dict) -> None:
        for doc in self.documents:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                return

    def create_index(self, keys, **kwargs) -> None:
        pass

    def sort(self, key_list, direction):
        sorted_docs = sorted(
            self.documents,
            key=lambda x: tuple(x.get(k) for k, _ in key_list),
            reverse=direction == -1,
        )
        return sorted_docs


class FakeDatabase:
    """Mock MongoDB database for testing."""

    def __init__(self):
        self.users = FakeCollection()
        self.roles = FakeCollection()
        self.competencies = FakeCollection()
        self.role_requirements = FakeCollection()
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.assessments = FakeCollection()
        self.assessment_attempts = FakeCollection()

    def __getitem__(self, name: str):
        return getattr(self, name, FakeCollection())


@pytest.fixture
def test_database() -> FakeDatabase:
    """Create a fresh fake database for each test."""
    return FakeDatabase()


@pytest.fixture
def sample_data(test_database: FakeDatabase) -> dict:
    """Seed test database with sample data."""
    now = datetime.now(UTC)

    # Create role
    role_id = ObjectId()
    test_database.roles.insert_one(
        {
            "_id": role_id,
            "role_code": "STAT_OFFICER",
            "role_name": "Statistical Officer",
            "description": "Handles statistical analysis and surveys",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
    )

    # Create competencies
    competencies = [
        {
            "_id": ObjectId(),
            "code": "STAT_SAMPLING",
            "name": "Sampling",
            "domain": "STATISTICAL",
            "created_at": now,
        },
        {
            "_id": ObjectId(),
            "code": "TECH_SQL",
            "name": "SQL",
            "domain": "TECHNICAL",
            "created_at": now,
        },
        {
            "_id": ObjectId(),
            "code": "TECH_PYTHON",
            "name": "Python",
            "domain": "TECHNICAL",
            "created_at": now,
        },
    ]
    for comp in competencies:
        test_database.competencies.insert_one(comp)

    # Create role requirements
    test_database.role_requirements.insert_many(
        [
            {
                "role_id": role_id,
                "competency_id": competencies[0]["_id"],
                "required_level": 4.0,
                "priority": 1,
                "importance": 1.0,
            },
            {
                "role_id": role_id,
                "competency_id": competencies[1]["_id"],
                "required_level": 3.0,
                "priority": 2,
                "importance": 0.75,
            },
            {
                "role_id": role_id,
                "competency_id": competencies[2]["_id"],
                "required_level": 3.0,
                "priority": 2,
                "importance": 0.75,
            },
        ]
    )

    # Create user
    user_id = ObjectId()
    test_database.users.insert_one(
        {
            "_id": user_id,
            "email": "officer@example.com",
            "password_hash": "hashed",
            "full_name": "Officer Name",
            "role_id": role_id,
            "designation": "Statistical Officer",
            "department": "Statistics",
            "employee_id": "EMP-001",
            "status": "active",
            "access_role": "EMPLOYEE",
            "created_at": now,
            "updated_at": now,
            "last_login_at": None,
        }
    )

    # Create competency profiles for user
    test_database.competency_profiles.insert_many(
        [
            {
                "user_id": user_id,
                "competency_id": competencies[0]["_id"],
                "current_level": 2.63,
                "confidence": 0.80,
                "last_assessed_at": now,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            {
                "user_id": user_id,
                "competency_id": competencies[1]["_id"],
                "current_level": 2.10,
                "confidence": 0.70,
                "last_assessed_at": now,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            },
            # Python not assessed (no profile)
        ]
    )

    return {
        "user_id": user_id,
        "role_id": role_id,
        "competencies": competencies,
        "now": now,
    }


@pytest.fixture
def client(test_database: FakeDatabase) -> TestClient:
    """Create a test client with mocked database."""
    settings = Settings(
        app_name="ShikshaSetu Test",
        app_env="test",
        debug=True,
        mongodb_uri="mongodb://test",
        mongodb_database="test",
    )
    app = create_app(settings)

    # Mock the database
    app.state.database = test_database
    app.state.database_client = MagicMock()

    return TestClient(app)


class TestSkillGapsAPI:
    """Test the skill gaps API endpoint."""

    def test_get_skill_gaps_authenticated_employee(
        self,
        client: TestClient,
        sample_data: dict,
    ) -> None:
        """Authenticated employee can retrieve their skill gaps."""
        from app.auth.security import create_access_token
        from app.core.config import get_settings

        settings = get_settings()
        token = create_access_token(str(sample_data["user_id"]), settings)

        response = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify role
        assert data["role"]["code"] == "STAT_OFFICER"
        assert data["role"]["name"] == "Statistical Officer"

        # Verify summary
        assert data["summary"]["required_competencies"] == 3
        assert data["summary"]["total_gaps"] == 3  # Sampling, SQL, and Python
        assert data["summary"]["no_gap_count"] == 0
        assert data["summary"]["not_assessed_count"] == 1  # Python

        # Verify gaps are sorted by priority
        gaps = data["gaps"]
        assert len(gaps) == 3

        # Find competencies by code (order may vary by priority score)
        sampling_gap = [g for g in gaps if g["competency_code"] == "STAT_SAMPLING"][0]
        sql_gap = [g for g in gaps if g["competency_code"] == "TECH_SQL"][0]
        python_gap = [g for g in gaps if g["competency_code"] == "TECH_PYTHON"][0]

        # Verify Sampling details (HIGH gap, priority 1, importance 1.0)
        assert sampling_gap["required_level"] == 4.0
        assert sampling_gap["current_level"] == 2.63
        assert sampling_gap["gap"] == 1.37
        assert sampling_gap["gap_category"] == "HIGH"
        assert sampling_gap["assessment_status"] == "ASSESSED"
        assert sampling_gap["priority"] == 1

        # Verify SQL details (MEDIUM gap, priority 2, importance 0.75)
        assert sql_gap["required_level"] == 3.0
        assert sql_gap["current_level"] == 2.10
        assert sql_gap["gap"] == 0.9
        assert sql_gap["gap_category"] == "MEDIUM"
        assert sql_gap["assessment_status"] == "ASSESSED"
        assert sql_gap["priority"] == 2

        # Verify Python details (CRITICAL gap unassessed, priority 2, importance 0.75)
        assert python_gap["required_level"] == 3.0
        assert python_gap["current_level"] is None
        assert python_gap["gap"] == 3.0
        assert python_gap["gap_category"] == "CRITICAL"
        assert python_gap["assessment_status"] == "NOT_ASSESSED"
        assert python_gap["priority"] == 2

    def test_get_skill_gaps_unauthenticated_rejected(self, client: TestClient) -> None:
        """Unauthenticated request is rejected."""
        response = client.get("/api/v1/skill-gaps/me")
        assert response.status_code == 401

    def test_get_skill_gaps_invalid_token_rejected(self, client: TestClient) -> None:
        """Invalid token is rejected."""
        response = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    def test_get_skill_gaps_user_without_role(
        self,
        client: TestClient,
        test_database: FakeDatabase,
    ) -> None:
        """User without a professional role returns 422."""
        from app.auth.security import create_access_token
        from app.core.config import get_settings

        now = datetime.now(UTC)
        user_id = ObjectId()

        # Create user without role_id
        test_database.users.insert_one(
            {
                "_id": user_id,
                "email": "norrole@example.com",
                "password_hash": "hashed",
                "full_name": "No Role",
                "role_id": None,  # No role assigned
                "designation": "Unknown",
                "department": "Unknown",
                "employee_id": "EMP-999",
                "status": "active",
                "access_role": "EMPLOYEE",
                "created_at": now,
                "updated_at": now,
            }
        )

        settings = get_settings()
        token = create_access_token(str(user_id), settings)

        response = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422
        assert "professional role" in response.json()["detail"]

    def test_get_skill_gaps_role_without_requirements(
        self,
        client: TestClient,
        test_database: FakeDatabase,
    ) -> None:
        """Role without competency requirements returns 404."""
        from app.auth.security import create_access_token
        from app.core.config import get_settings

        now = datetime.now(UTC)

        # Create empty role (no requirements)
        role_id = ObjectId()
        test_database.roles.insert_one(
            {
                "_id": role_id,
                "role_code": "EMPTY_ROLE",
                "role_name": "Empty Role",
                "status": "active",
                "created_at": now,
            }
        )

        # Create user with empty role
        user_id = ObjectId()
        test_database.users.insert_one(
            {
                "_id": user_id,
                "email": "empty@example.com",
                "password_hash": "hashed",
                "full_name": "Empty Role User",
                "role_id": role_id,
                "designation": "Empty",
                "department": "None",
                "employee_id": "EMP-888",
                "status": "active",
                "access_role": "EMPLOYEE",
                "created_at": now,
                "updated_at": now,
            }
        )

        settings = get_settings()
        token = create_access_token(str(user_id), settings)

        response = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404
        assert "No competency requirements" in response.json()["detail"]

    def test_get_skill_gaps_user_isolation(
        self,
        client: TestClient,
        sample_data: dict,
        test_database: FakeDatabase,
    ) -> None:
        """User A cannot access User B's skill gaps."""
        from app.auth.security import create_access_token
        from app.core.config import get_settings

        now = datetime.now(UTC)

        # Create a different user with same role
        other_user_id = ObjectId()
        test_database.users.insert_one(
            {
                "_id": other_user_id,
                "email": "other@example.com",
                "password_hash": "hashed",
                "full_name": "Other User",
                "role_id": sample_data["role_id"],
                "designation": "Statistical Officer",
                "department": "Statistics",
                "employee_id": "EMP-002",
                "status": "active",
                "access_role": "EMPLOYEE",
                "created_at": now,
                "updated_at": now,
            }
        )

        # Add different competency profile for other user
        test_database.competency_profiles.insert_one(
            {
                "user_id": other_user_id,
                "competency_id": sample_data["competencies"][0]["_id"],
                "current_level": 5.0,  # Different level
                "confidence": 1.0,
                "last_assessed_at": now,
                "status": "active",
                "created_at": now,
                "updated_at": now,
            }
        )

        settings = get_settings()
        # Authenticate as first user
        token = create_access_token(str(sample_data["user_id"]), settings)

        response = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        
        # Verify we got FIRST user's data (not second user's)
        gaps = data["gaps"]
        
        # Sort gaps by code to find Sampling
        sampling_gap = [g for g in gaps if g["competency_code"] == "STAT_SAMPLING"][0]
        
        # First user has Sampling level 2.63 (gap 1.37)
        assert sampling_gap["current_level"] == 2.63
        assert sampling_gap["gap"] == 1.37

    def test_skill_gaps_dynamic_calculation(
        self,
        client: TestClient,
        sample_data: dict,
        test_database: FakeDatabase,
    ) -> None:
        """Skill gaps are calculated dynamically from current state."""
        from app.auth.security import create_access_token
        from app.core.config import get_settings

        settings = get_settings()
        token = create_access_token(str(sample_data["user_id"]), settings)

        # Get initial gaps
        response1 = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        gaps1 = response1.json()["gaps"]
        
        # Find sampling gap (first competency assessed, should have gap)
        sampling_gap_initial = [g for g in gaps1 if g["competency_code"] == "STAT_SAMPLING"][0]
        assert sampling_gap_initial["gap"] == 1.37  # Sampling gap initially
        
        # Update competency profile in database
        now = datetime.now(UTC)
        for doc in test_database.competency_profiles.documents:
            if (doc.get("user_id") == sample_data["user_id"] and
                str(doc.get("competency_id")) == str(sample_data["competencies"][0]["_id"])):
                doc["current_level"] = 4.0  # Increase to required level
                doc["updated_at"] = now
                break

        # Get gaps again
        response2 = client.get(
            "/api/v1/skill-gaps/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        gaps2 = response2.json()["gaps"]

        # Sampling gap should now be 0
        sampling_gap_updated = [g for g in gaps2 if g["competency_code"] == "STAT_SAMPLING"][0]
        assert sampling_gap_updated["gap"] == 0.0
        assert sampling_gap_updated["gap_category"] == "NO_GAP"

        # Summary should be updated
        assert response2.json()["summary"]["total_gaps"] == 2  # Only SQL and Python now
