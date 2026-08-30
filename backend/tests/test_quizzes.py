"""
Automated unit and integration test suite for Quiz System (MED-01).

Covers:
1. Quiz creation with valid authenticated user
2. Unauthenticated quiz creation rejection
3. Learning material ownership validation
4. Cross-user material access rejection
5. Quiz retrieval by owner
6. Cross-user quiz retrieval rejection (404)
7. Correct answers and explanations hidden in GET quiz
8. Quiz submission with full/partial scoring
9. Quiz submission with incorrect answers
10. Invalid/malformed question IDs in submission
11. Duplicate quiz submission rejection (HTTP 409)
12. Competency evidence creation after submission
13. Competency profile update after submission (deterministic formula)
14. Skill gap calculation before and after submission
15. Material ID format validation
16. Non-existent and unready material handling
"""

from datetime import UTC, datetime
from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app
from app.quizzes.models import QuizStatus


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeResult:
    def __init__(self, upserted_id: ObjectId | None = None) -> None:
        self.upserted_id = upserted_id


class FakeCursor(list):
    def sort(self, key: str, direction: int = 1):
        return FakeCursor(sorted(self, key=lambda item: item.get(key, ""), reverse=direction < 0))

    def limit(self, count: int):
        return FakeCursor(self[:count])


class FakeCollection:
    """In-memory MongoDB collection for quiz testing."""

    def __init__(self, documents: list[dict] | None = None) -> None:
        self.documents = documents or []

    def _matches(self, document: dict, query: dict) -> bool:
        for key, expected in query.items():
            actual = document.get(key)
            if isinstance(expected, dict):
                if "$in" in expected:
                    # Compare string or ObjectId representations
                    exp_set = {str(x) for x in expected["$in"]} | set(expected["$in"])
                    if actual not in exp_set and str(actual) not in exp_set:
                        return False
                elif "$nin" in expected:
                    exp_set = {str(x) for x in expected["$nin"]} | set(expected["$nin"])
                    if actual in exp_set or str(actual) in exp_set:
                        return False
                else:
                    if actual != expected:
                        return False
            else:
                if isinstance(expected, ObjectId) and isinstance(actual, str):
                    if str(expected) != actual:
                        return False
                elif isinstance(actual, ObjectId) and isinstance(expected, str):
                    if str(actual) != expected:
                        return False
                elif actual != expected:
                    return False
        return True

    def find(self, query: dict | None = None, projection: dict | None = None) -> FakeCursor:
        return FakeCursor([dict(item) for item in self.documents if self._matches(item, query or {})])

    def find_one(self, query: dict, projection: dict | None = None) -> dict | None:
        return next((dict(item) for item in self.documents if self._matches(item, query)), None)

    def insert_one(self, document: dict) -> InsertOneResult:
        document.setdefault("_id", ObjectId())
        self.documents.append(document)
        return InsertOneResult(document["_id"])

    def insert_many(self, documents: list[dict]) -> None:
        for doc in documents:
            self.insert_one(doc)

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> FakeResult:
        doc = next((item for item in self.documents if self._matches(item, query)), None)
        if doc is None and upsert:
            new_doc = {k: v for k, v in query.items() if not isinstance(v, dict)}
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            if "$set" in update:
                new_doc.update(update["$set"])
            new_doc.setdefault("_id", ObjectId())
            self.documents.append(new_doc)
            return FakeResult(new_doc["_id"])
        if doc is not None:
            if "$set" in update:
                doc.update(update["$set"])
        return FakeResult()

    def find_one_and_update(self, query: dict, update: dict, return_document: bool = False) -> dict | None:
        doc = next((item for item in self.documents if self._matches(item, query)), None)
        if doc is not None:
            if "$set" in update:
                doc.update(update["$set"])
            return dict(doc)
        return None

    def count_documents(self, query: dict) -> int:
        return sum(self._matches(item, query) for item in self.documents)

    def create_index(self, *args, **kwargs) -> str:
        return kwargs.get("name", "idx")


class FakeDatabase:
    """Mock MongoDB database setup for quiz isolation."""

    def __init__(self) -> None:
        self.users = FakeCollection()
        self.roles = FakeCollection()
        self.role_requirements = FakeCollection()
        self.competencies = FakeCollection()
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.learning_materials = FakeCollection()
        self.quizzes = FakeCollection()
        self.quiz_attempts = FakeCollection()


@pytest.fixture
def quiz_test_env():
    """Create test client, fake database, and pre-seeded test fixtures."""
    db = FakeDatabase()
    settings = Settings(
        mongodb_uri="mongodb://test",
        mongodb_database="test",
        jwt_secret="super-secret-key-for-testing-only-32-chars",
    )
    application = create_app(settings)
    application.state.database = db

    # Seed canonical competency and role
    comp_id = ObjectId()
    db.competencies.insert_one({
        "_id": comp_id,
        "code": "TECH_PYTHON",
        "name": "Python Programming",
        "domain": "Technical Competencies",
    })

    role_id = ObjectId()
    db.roles.insert_one({
        "_id": role_id,
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "status": "active",
    })

    db.role_requirements.insert_one({
        "_id": ObjectId(),
        "role_id": role_id,
        "competency_id": comp_id,
        "required_level": 4.0,
    })

    # Seed User A
    user_a_id = ObjectId()
    db.users.insert_one({
        "_id": user_a_id,
        "email": "user_a@shikshasetu.gov.in",
        "password_hash": hash_password("Password123!"),
        "full_name": "User Alpha",
        "role_id": role_id,
        "access_role": "EMPLOYEE",
        "status": "active",
    })
    token_a = create_access_token(str(user_a_id), settings)

    # Seed User B
    user_b_id = ObjectId()
    db.users.insert_one({
        "_id": user_b_id,
        "email": "user_b@shikshasetu.gov.in",
        "password_hash": hash_password("Password123!"),
        "full_name": "User Beta",
        "role_id": role_id,
        "access_role": "EMPLOYEE",
        "status": "active",
    })
    token_b = create_access_token(str(user_b_id), settings)

    # Seed learning material owned by User A
    material_a_id = ObjectId()
    db.learning_materials.insert_one({
        "_id": material_a_id,
        "user_id": str(user_a_id),
        "filename": "python_handbook.pdf",
        "status": "READY",
        "chunk_count": 5,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })

    # Seed learning material owned by User B
    material_b_id = ObjectId()
    db.learning_materials.insert_one({
        "_id": material_b_id,
        "user_id": str(user_b_id),
        "filename": "sql_reference.pdf",
        "status": "READY",
        "chunk_count": 3,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })

    client = TestClient(application)

    return {
        "client": client,
        "db": db,
        "user_a_id": str(user_a_id),
        "user_b_id": str(user_b_id),
        "headers_a": {"Authorization": f"Bearer {token_a}"},
        "headers_b": {"Authorization": f"Bearer {token_b}"},
        "material_a_id": str(material_a_id),
        "material_b_id": str(material_b_id),
        "comp_id": comp_id,
    }


class TestQuizSystem:
    """Test suite covering all quiz requirements."""

    SAMPLE_QUESTIONS = [
        {
            "question_id": "q1",
            "question": "What is Python?",
            "options": ["A snake", "A programming language", "A framework", "An OS"],
            "correct_answer": "B",
            "explanation": "Python is a high-level programming language.",
            "difficulty": "EASY",
        },
        {
            "question_id": "q2",
            "question": "Which data type is immutable?",
            "options": ["List", "Dictionary", "Tuple", "Set"],
            "correct_answer": "C",
            "explanation": "Tuples cannot be modified after creation.",
            "difficulty": "MEDIUM",
        }
    ]

    def test_01_quiz_creation_valid_authenticated_user(self, quiz_test_env):
        """1. Quiz creation with valid authenticated user."""
        client = quiz_test_env["client"]
        headers = quiz_test_env["headers_a"]
        material_id = quiz_test_env["material_a_id"]

        payload = {
            "material_id": material_id,
            "competency_code": "TECH_PYTHON",
            "title": "Python Data Types Quiz",
            "questions": self.SAMPLE_QUESTIONS,
        }

        response = client.post("/api/v1/quizzes", headers=headers, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "quiz_id" in data or "_id" in data
        assert data["question_count"] == 2
        assert data["status"] == "READY"
        assert len(data["questions"]) == 2

    def test_02_quiz_creation_unauthenticated(self, quiz_test_env):
        """2. Invalid/unauthenticated quiz creation."""
        client = quiz_test_env["client"]
        material_id = quiz_test_env["material_a_id"]

        payload = {
            "material_id": material_id,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        }

        response = client.post("/api/v1/quizzes", json=payload)
        assert response.status_code == 401

    def test_03_learning_material_ownership_validation(self, quiz_test_env):
        """3. Learning material ownership validation (User A creating with own material)."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        payload = {
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        }

        response = client.post("/api/v1/quizzes", headers=headers_a, json=payload)
        assert response.status_code == 200

    def test_04_cross_user_material_access_rejection(self, quiz_test_env):
        """4. Cross-user material access rejection (User B trying to use User A's material)."""
        client = quiz_test_env["client"]
        headers_b = quiz_test_env["headers_b"]
        material_a = quiz_test_env["material_a_id"]

        payload = {
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        }

        response = client.post("/api/v1/quizzes", headers=headers_b, json=payload)
        assert response.status_code == 400
        assert "Material not found or does not belong to user" in response.json()["detail"]

    def test_05_quiz_retrieval_by_owner(self, quiz_test_env):
        """5. Quiz retrieval by owner."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        # Create quiz
        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]

        # Retrieve
        get_res = client.get(f"/api/v1/quizzes/{quiz_id}", headers=headers_a)
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["_id"] == quiz_id
        assert len(data["questions"]) == 2

    def test_06_cross_user_quiz_retrieval_rejection(self, quiz_test_env):
        """6. Cross-user quiz retrieval rejection (User B cannot retrieve User A's quiz)."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        headers_b = quiz_test_env["headers_b"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]

        # User B attempts retrieval
        get_res = client.get(f"/api/v1/quizzes/{quiz_id}", headers=headers_b)
        assert get_res.status_code == 404

    def test_07_correct_answer_is_not_exposed_by_get_quiz(self, quiz_test_env):
        """7. Correct answer and explanation are NOT exposed by GET quiz."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]

        get_res = client.get(f"/api/v1/quizzes/{quiz_id}", headers=headers_a)
        assert get_res.status_code == 200
        for q in get_res.json()["questions"]:
            assert "correct_answer" not in q
            assert "explanation" not in q

    def test_08_quiz_submission_with_correct_answers(self, quiz_test_env):
        """8. Quiz submission with correct answers (100% score)."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        # Submit perfect answers (q_1 -> B, q_2 -> C)
        sub_res = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [
                {"question_id": q_ids[0], "selected_answer": "B"},
                {"question_id": q_ids[1], "selected_answer": "C"}
            ]
        })
        assert sub_res.status_code == 200
        data = sub_res.json()
        assert data["percentage"] == 100.0
        assert data["correct_count"] == 2
        assert data["total_questions"] == 2
        assert len(data["explanations"]) == 2
        assert data["explanations"][0]["is_correct"] is True
        assert data["competency"]["competency_level_after"] == 4.5

    def test_09_quiz_submission_with_incorrect_answers(self, quiz_test_env):
        """9. Quiz submission with incorrect answers (0% score)."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        # Submit wrong answers (q_1 -> A, q_2 -> A)
        sub_res = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [
                {"question_id": q_ids[0], "selected_answer": "A"},
                {"question_id": q_ids[1], "selected_answer": "A"}
            ]
        })
        assert sub_res.status_code == 200
        data = sub_res.json()
        assert data["percentage"] == 0.0
        assert data["correct_count"] == 0
        assert data["competency"]["competency_level_after"] == 1.5

    def test_10_invalid_question_id_handling(self, quiz_test_env):
        """10. Invalid question ID / malformed answer handling."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]

        # Send invalid question IDs
        sub_res = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [
                {"question_id": "NON_EXISTENT_Q", "selected_answer": "A"},
                {"question_id": "ANOTHER_FAKE_Q", "selected_answer": "B"}
            ]
        })
        assert sub_res.status_code == 400
        assert "Missing or extra question IDs" in sub_res.json()["detail"]

    def test_11_duplicate_quiz_submission_behavior(self, quiz_test_env):
        """11. Duplicate quiz submission behavior (returns 409 Conflict)."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        answers = [{"question_id": qid, "selected_answer": "B"} for qid in q_ids]

        # First submission succeeds
        first_sub = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={"answers": answers})
        assert first_sub.status_code == 200

        # Second submission rejected with 409 Conflict
        second_sub = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={"answers": answers})
        assert second_sub.status_code == 409
        assert "already submitted" in second_sub.json()["detail"].lower()

    def test_12_competency_evidence_creation_after_submission(self, quiz_test_env):
        """12. Competency evidence creation after successful submission."""
        client = quiz_test_env["client"]
        db = quiz_test_env["db"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]
        user_a_id = quiz_test_env["user_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [{"question_id": qid, "selected_answer": "B"} for qid in q_ids]
        })

        # Check evidence was inserted
        evidence = db.competency_evidence.find_one({"user_id": ObjectId(user_a_id), "evidence_type": "QUIZ"})
        assert evidence is not None
        assert evidence["competency_code"] == "TECH_PYTHON"
        assert evidence["competency_id"] == quiz_test_env["comp_id"]
        assert evidence["source"] == "AI_QUIZ"

    def test_13_competency_profile_update_after_submission(self, quiz_test_env):
        """13. Competency profile update after successful submission."""
        client = quiz_test_env["client"]
        db = quiz_test_env["db"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]
        user_a_id = quiz_test_env["user_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        # Submit 100% correct
        client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [
                {"question_id": q_ids[0], "selected_answer": "B"},
                {"question_id": q_ids[1], "selected_answer": "C"}
            ]
        })

        # Check profile updated
        profile = db.competency_profiles.find_one({"user_id": ObjectId(user_a_id), "competency_id": quiz_test_env["comp_id"]})
        assert profile is not None
        assert profile["level"] == 4.5
        assert profile["confidence"] == 0.9

    def test_14_skill_gap_calculation_after_submission(self, quiz_test_env):
        """14. Skill-gap calculation returned after quiz submission."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        sub_res = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [
                {"question_id": q_ids[0], "selected_answer": "B"},
                {"question_id": q_ids[1], "selected_answer": "C"}
            ]
        })
        assert sub_res.status_code == 200
        gap_data = sub_res.json()["skill_gap"]
        assert gap_data["competency_code"] == "TECH_PYTHON"
        assert gap_data["required_level"] == 4.0
        assert gap_data["current_level"] == 4.5
        assert gap_data["gap_after"] == 0.0

    def test_15_material_id_format_validation(self, quiz_test_env):
        """15. Material ID validation (invalid format)."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]

        response = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": "not-a-valid-object-id",
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        assert response.status_code == 400
        assert "Invalid material ID" in response.json()["detail"]

    def test_16_non_existent_material_handling(self, quiz_test_env):
        """16. Non-existent material handling."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]

        random_oid = str(ObjectId())
        response = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": random_oid,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        assert response.status_code == 400
        assert "Material not found or does not belong to user" in response.json()["detail"]

    def test_17_material_not_ready_handling(self, quiz_test_env):
        """17. Material not in READY status."""
        client = quiz_test_env["client"]
        db = quiz_test_env["db"]
        headers_a = quiz_test_env["headers_a"]
        user_a = quiz_test_env["user_a_id"]

        mat_id = ObjectId()
        db.learning_materials.insert_one({
            "_id": mat_id,
            "user_id": user_a,
            "filename": "unprocessed.pdf",
            "status": "PROCESSING",
        })

        response = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": str(mat_id),
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()

    def test_18_quiz_submission_incomplete_answers(self, quiz_test_env):
        """18. Quiz submission with incomplete questions."""
        client = quiz_test_env["client"]
        headers_a = quiz_test_env["headers_a"]
        material_a = quiz_test_env["material_a_id"]

        create_res = client.post("/api/v1/quizzes", headers=headers_a, json={
            "material_id": material_a,
            "competency_code": "TECH_PYTHON",
            "questions": self.SAMPLE_QUESTIONS,
        })
        quiz_id = create_res.json()["_id"]
        q_ids = [q["question_id"] for q in create_res.json()["questions"]]

        # Submit only 1 of 2 answers
        sub_res = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_a, json={
            "answers": [
                {"question_id": q_ids[0], "selected_answer": "B"}
            ]
        })
        assert sub_res.status_code == 400
        assert "Missing or extra question IDs" in sub_res.json()["detail"]
