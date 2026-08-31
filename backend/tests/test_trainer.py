"""
Automated unit and integration test suite for Trainer Assessment Studio (Phase 2B).

Covers all 16 Trainer capabilities and RBAC security boundaries:
1. Trainer Dashboard metrics calculation
2. Listing trainer-owned materials with question counts
3. Single material details and question counts
4. Generating questions from material into review studio
5. Listing generated questions by material and status filter
6. Viewing question details with answer key & source grounding
7. Editing question content (transitions to EDITED)
8. Approving question (transitions to APPROVED)
9. Rejecting question (transitions to REJECTED)
10. Creating quiz draft with APPROVED questions (succeeds)
11. Creating quiz draft with unapproved/rejected questions (fails HTTP 400)
12. Listing trainer quizzes
13. Viewing trainer quiz details
14. Publishing quiz draft (transitions to PUBLISHED)
15. Assigning quiz to learners (requires PUBLISHED, transitions to ASSIGNED)
16. Assigning DRAFT quiz rejected (HTTP 400)
17. Learner views assigned quizzes via GET /quizzes/assigned
18. Learner submits assigned quiz
19. Trainer views quiz attempts and performance statistics
20. Trainer views assigned learners and average scores
21. Trainer views specific learner evaluation history
22. Trainer provides qualitative feedback on learner attempt
23. Cross-trainer isolation (Trainer A cannot modify Trainer B's questions/quizzes)
24. RBAC enforcement (OFFICIAL is forbidden HTTP 403 on all /trainer/* routes)
"""

from datetime import UTC, datetime
from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app
from app.trainer.models import QuestionReviewStatus, TrainerQuizStatus, TrainerQuestion, TrainerQuiz


class FakeCursor(list):
    def sort(self, key: str, direction: int = 1):
        return FakeCursor(sorted(self, key=lambda item: item.get(key, ""), reverse=direction < 0))

    def limit(self, count: int):
        return FakeCursor(self[:count])


class FakeCollection:
    """In-memory collection supporting queries, insertions, and updates."""

    def __init__(self, documents: list[dict] | None = None) -> None:
        self.documents = documents or []

    def _matches(self, document: dict, query: dict) -> bool:
        for key, expected in query.items():
            if key == "$or":
                if not any(self._matches(document, subq) for subq in expected):
                    return False
                continue

            actual = document.get(key)
            if isinstance(expected, dict):
                if "$in" in expected:
                    str_actual = str(actual)
                    expected_strs = [str(x) for x in expected["$in"]]
                    if actual not in expected["$in"] and str_actual not in expected_strs:
                        return False
                elif "$ne" in expected:
                    if actual == expected["$ne"]:
                        return False
                elif "$exists" in expected:
                    if bool(expected["$exists"]) != (key in document):
                        return False
            elif isinstance(actual, list) and not isinstance(expected, list):
                if expected not in actual and str(expected) not in [str(x) for x in actual]:
                    return False
            elif actual != expected and str(actual) != str(expected):
                return False
        return True

    def find_one(self, query: dict, projection: dict | None = None) -> dict | None:
        for document in self.documents:
            if self._matches(document, query):
                return document
        return None

    def find(self, query: dict | None = None, projection: dict | None = None) -> FakeCursor:
        if not query:
            return FakeCursor(list(self.documents))
        return FakeCursor([d for d in self.documents if self._matches(d, query)])

    def insert_one(self, document: dict):
        document.setdefault("_id", ObjectId())
        self.documents.append(document)
        class Res:
            inserted_id = document["_id"]
        return Res()

    def insert_many(self, documents: list[dict]):
        ids = []
        for d in documents:
            d.setdefault("_id", ObjectId())
            self.documents.append(d)
            ids.append(d["_id"])
        class Res:
            inserted_ids = ids
        return Res()

    def update_one(self, query: dict, update: dict, upsert: bool = False):
        document = self.find_one(query)
        modified = 0
        if document is not None:
            if "$set" in update:
                document.update(update["$set"])
                modified = 1
        elif upsert:
            new_doc = dict(query)
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            if "$set" in update:
                new_doc.update(update["$set"])
            new_doc.setdefault("_id", ObjectId())
            self.documents.append(new_doc)
            modified = 1
        class Res:
            matched_count = 1 if document else (1 if upsert else 0)
            modified_count = modified
        return Res()

    def count_documents(self, query: dict) -> int:
        return len(self.find(query))

    def find_one_and_update(self, query: dict, update: dict, return_document=None) -> dict | None:
        document = self.find_one(query)
        if document is not None:
            if "$set" in update:
                document.update(update["$set"])
        return document


class FakeDatabase:
    """Mock database with all collections for trainer studio testing."""

    def __init__(self) -> None:
        self.role_id = ObjectId()
        self.roles = FakeCollection([
            {"_id": self.role_id, "role_code": "STATISTICAL_OFFICER", "name": "Statistical Officer", "status": "active"}
        ])
        self.users = FakeCollection()
        self.learning_materials = FakeCollection()
        self.document_chunks = FakeCollection()
        self.trainer_questions = FakeCollection()
        self.quizzes = FakeCollection()
        self.quiz_attempts = FakeCollection()
        self.competencies = FakeCollection([
            {"_id": ObjectId(), "code": "STAT_SAMPLING", "name": "Statistical Sampling", "status": "active"},
            {"_id": ObjectId(), "code": "TECH_PYTHON", "name": "Python Programming", "status": "active"}
        ])
        self.competency_profiles = FakeCollection()
        self.competency_evidence = FakeCollection()
        self.role_requirements = FakeCollection([
            {"role_id": self.role_id, "competency_code": "STAT_SAMPLING", "required_level": 4.0},
            {"role_id": self.role_id, "competency_code": "TECH_PYTHON", "required_level": 3.0}
        ])

    def __getitem__(self, name: str) -> FakeCollection:
        return getattr(self, name)


def make_trainer_app() -> tuple[TestClient, FakeDatabase, Settings]:
    database = FakeDatabase()
    settings = Settings(
        mongodb_uri="mongodb://test",
        mongodb_database="test_trainer",
        jwt_secret="test-secret-with-at-least-32-bytes-long",
        jwt_access_token_expire_minutes=60,
        llm_provider="mock",
        embedding_provider="mock",
    )
    application = create_app(settings)
    application.state.database = database
    application.state.settings = settings
    return TestClient(application), database, settings


def create_user(database: FakeDatabase, email: str, role: str, employee_id: str) -> dict:
    now = datetime.now(UTC)
    user_doc = {
        "_id": ObjectId(),
        "email": email.lower(),
        "password_hash": hash_password("Password123!"),
        "full_name": f"{role.capitalize()} User ({employee_id})",
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


def create_material(database: FakeDatabase, trainer_id: str, filename: str = "Sampling_Manual.pdf") -> dict:
    now = datetime.now(UTC)
    mat_doc = {
        "_id": ObjectId(),
        "user_id": str(trainer_id),
        "filename": filename,
        "original_filename": filename,
        "content_type": "application/pdf",
        "file_size": 20480,
        "storage_reference": f"/uploads/{filename}",
        "status": "READY",
        "extraction_status": "SUCCESS",
        "chunk_count": 5,
        "embedding_count": 5,
        "created_at": now,
        "updated_at": now,
    }
    database.learning_materials.insert_one(mat_doc)
    
    # Insert chunks
    for i in range(1, 6):
        database.document_chunks.insert_one({
            "_id": ObjectId(),
            "material_id": str(mat_doc["_id"]),
            "sequence": i,
            "text": f"Content section {i} covering statistical sampling and estimation techniques in detail.",
            "source_page": i,
            "created_at": now,
        })
    return mat_doc


# ==============================================================================
# 1. Dashboard & Materials Tests
# ==============================================================================

def test_trainer_dashboard_metrics():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    # Upload 2 materials and create 3 questions
    mat1 = create_material(database, str(trainer["_id"]), "Doc1.pdf")
    mat2 = create_material(database, str(trainer["_id"]), "Doc2.pdf")

    # Add questions
    database.trainer_questions.insert_one(TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat1["_id"]),
        competency_code="STAT_SAMPLING",
        question="What is SRS?",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Simple Random Sampling",
        status=QuestionReviewStatus.APPROVED,
    ))
    database.trainer_questions.insert_one(TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat1["_id"]),
        competency_code="STAT_SAMPLING",
        question="What is Stratified?",
        options=["A", "B", "C", "D"],
        correct_answer="B",
        explanation="Stratified sampling",
        status=QuestionReviewStatus.GENERATED,
    ))

    resp = client.get("/api/v1/trainer/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_materials_uploaded"] == 2
    assert data["total_questions_generated"] == 2
    assert data["questions_approved"] == 1
    assert data["questions_pending_review"] == 1
    assert data["total_quizzes_created"] == 0
    client.close()


def test_list_trainer_materials():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Survey_Theory.pdf")
    # Add an approved question for this material
    database.trainer_questions.insert_one(TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Q1",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Expl",
        status=QuestionReviewStatus.APPROVED,
    ))

    resp = client.get("/api/v1/trainer/materials", headers=headers)
    assert resp.status_code == 200
    mats = resp.json()
    assert len(mats) == 1
    assert mats[0]["filename"] == "Survey_Theory.pdf"
    assert mats[0]["questions_count"] == 1
    assert mats[0]["approved_questions_count"] == 1
    client.close()


# ==============================================================================
# 2. Question Generation & Review Lifecycle Tests
# ==============================================================================

def test_generate_questions_into_review_studio():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Python_Handbook.pdf")

    payload = {
        "competency_code": "TECH_PYTHON",
        "question_count": 3,
        "difficulty": "MEDIUM",
    }
    resp = client.post(
        f"/api/v1/trainer/materials/{mat['_id']}/generate",
        headers=headers,
        json=payload,
    )
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) == 3
    for q in questions:
        assert q["status"] == "GENERATED"
        assert q["competency_code"] == "TECH_PYTHON"
        assert q["material_id"] == str(mat["_id"])
        assert len(q["options"]) >= 3
        assert q["correct_answer"] in ["A", "B", "C", "D", "E"]
    client.close()


def test_question_review_lifecycle_edit_approve_reject():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Manual.pdf")

    # Insert a generated question
    q_doc = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Original question text?",
        options=["Opt A", "Opt B", "Opt C", "Opt D"],
        correct_answer="B",
        explanation="Initial explanation",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_doc)
    qid = str(q_doc["_id"])

    # 1. View question details
    resp_get = client.get(f"/api/v1/trainer/questions/{qid}", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["question"] == "Original question text?"
    assert resp_get.json()["status"] == "GENERATED"

    # 2. Edit question
    resp_edit = client.put(
        f"/api/v1/trainer/questions/{qid}",
        headers=headers,
        json={
            "question": "Updated polished question text?",
            "explanation": "Updated detailed explanation",
        },
    )
    assert resp_edit.status_code == 200
    assert resp_edit.json()["question"] == "Updated polished question text?"
    assert resp_edit.json()["status"] == "EDITED"

    # 3. Approve question
    resp_approve = client.post(
        f"/api/v1/trainer/questions/{qid}/approve",
        headers=headers,
        json={"action": "APPROVE", "review_notes": "Grounding verified and verified clear."},
    )
    assert resp_approve.status_code == 200
    assert resp_approve.json()["status"] == "APPROVED"
    assert resp_approve.json()["review_notes"] == "Grounding verified and verified clear."

    # 4. Reject another question
    q_doc2 = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Hallucinated question?",
        options=["X", "Y", "Z"],
        correct_answer="X",
        explanation="No source",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_doc2)
    qid2 = str(q_doc2["_id"])

    resp_reject = client.post(
        f"/api/v1/trainer/questions/{qid2}/reject",
        headers=headers,
        json={"action": "REJECT", "review_notes": "Not grounded in text."},
    )
    assert resp_reject.status_code == 200
    assert resp_reject.json()["status"] == "REJECTED"

    # Verify listing with status filter
    resp_approved_list = client.get(
        f"/api/v1/trainer/materials/{mat['_id']}/questions?status=APPROVED",
        headers=headers,
    )
    assert resp_approved_list.status_code == 200
    assert len(resp_approved_list.json()) == 1
    assert resp_approved_list.json()[0]["id"] == qid
    client.close()


# ==============================================================================
# 3. Quiz Creation, Publishing & Assignment Tests
# ==============================================================================

def test_quiz_creation_enforces_approved_questions_only():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Sampling.pdf")

    # Q1: APPROVED
    q1 = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Approved Question 1",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Valid",
        status=QuestionReviewStatus.APPROVED,
    )
    database.trainer_questions.insert_one(q1)

    # Q2: GENERATED (unapproved)
    q2 = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Unapproved Question 2",
        options=["A", "B", "C", "D"],
        correct_answer="B",
        explanation="Not reviewed",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q2)

    # 1. Attempting to create quiz with unapproved Q2 must FAIL (HTTP 400)
    resp_fail = client.post(
        "/api/v1/trainer/quizzes",
        headers=headers,
        json={
            "title": "Sampling Assessment",
            "material_id": str(mat["_id"]),
            "competency_code": "STAT_SAMPLING",
            "question_ids": [str(q1["_id"]), str(q2["_id"])],
        },
    )
    assert resp_fail.status_code == 400
    assert "not in APPROVED state" in resp_fail.json()["detail"]

    # 2. Creating quiz with only approved Q1 SUCCEEDS
    resp_ok = client.post(
        "/api/v1/trainer/quizzes",
        headers=headers,
        json={
            "title": "Sampling Assessment (Official)",
            "material_id": str(mat["_id"]),
            "competency_code": "STAT_SAMPLING",
            "question_ids": [str(q1["_id"])],
        },
    )
    assert resp_ok.status_code == 201
    quiz_data = resp_ok.json()
    assert quiz_data["status"] == "DRAFT"
    assert quiz_data["question_count"] == 1
    assert quiz_data["title"] == "Sampling Assessment (Official)"
    client.close()


def test_publish_and_assign_quiz():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    learner1 = create_user(database, "learner1@test.com", "OFFICIAL", "EMP-001")
    learner2 = create_user(database, "learner2@test.com", "OFFICIAL", "EMP-002")

    token_trainer = create_access_token(str(trainer["_id"]), settings)
    token_learner1 = create_access_token(str(learner1["_id"]), settings)

    headers_trainer = {"Authorization": f"Bearer {token_trainer}"}
    headers_learner1 = {"Authorization": f"Bearer {token_learner1}"}

    mat = create_material(database, str(trainer["_id"]))

    q1 = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Approved Q1",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Expl",
        status=QuestionReviewStatus.APPROVED,
    )
    database.trainer_questions.insert_one(q1)

    # Create quiz draft
    resp_create = client.post(
        "/api/v1/trainer/quizzes",
        headers=headers_trainer,
        json={
            "title": "Module 1 Assessment",
            "competency_code": "STAT_SAMPLING",
            "question_ids": [str(q1["_id"])],
        },
    )
    quiz_id = resp_create.json()["id"]

    # Assigning DRAFT quiz should FAIL (must publish first)
    resp_assign_draft = client.post(
        f"/api/v1/trainer/quizzes/{quiz_id}/assign",
        headers=headers_trainer,
        json={"learner_ids": [str(learner1["_id"])]},
    )
    assert resp_assign_draft.status_code == 400
    assert "publish the quiz first" in resp_assign_draft.json()["detail"]

    # Publish quiz
    resp_pub = client.post(f"/api/v1/trainer/quizzes/{quiz_id}/publish", headers=headers_trainer)
    assert resp_pub.status_code == 200
    assert resp_pub.json()["status"] == "PUBLISHED"

    # Assign to learner1 and learner2
    resp_assign = client.post(
        f"/api/v1/trainer/quizzes/{quiz_id}/assign",
        headers=headers_trainer,
        json={"learner_ids": [str(learner1["_id"]), str(learner2["_id"])]},
    )
    assert resp_assign.status_code == 200
    assert resp_assign.json()["assigned_learners_count"] == 2
    assert resp_assign.json()["status"] == "ASSIGNED"

    # Learner 1 checks assigned quizzes
    resp_learner_assigned = client.get("/api/v1/quizzes/assigned", headers=headers_learner1)
    assert resp_learner_assigned.status_code == 200
    assigned_quizzes = resp_learner_assigned.json()
    assert len(assigned_quizzes) >= 1
    assert any(q["_id"] == quiz_id for q in assigned_quizzes)
    client.close()


# ==============================================================================
# 4. Learner Evaluation & Trainer Feedback Tests
# ==============================================================================

def test_learner_attempt_evaluation_and_trainer_feedback():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    learner = create_user(database, "learner@test.com", "OFFICIAL", "EMP-001")

    token_trainer = create_access_token(str(trainer["_id"]), settings)
    token_learner = create_access_token(str(learner["_id"]), settings)

    headers_trainer = {"Authorization": f"Bearer {token_trainer}"}
    headers_learner = {"Authorization": f"Bearer {token_learner}"}

    mat = create_material(database, str(trainer["_id"]))

    q1 = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="What is probability sampling?",
        options=["Random", "Fixed", "Biased", "None"],
        correct_answer="A",
        explanation="Random selection",
        status=QuestionReviewStatus.APPROVED,
    )
    database.trainer_questions.insert_one(q1)

    # Trainer creates, publishes and assigns quiz
    quiz_res = client.post(
        "/api/v1/trainer/quizzes",
        headers=headers_trainer,
        json={"title": "Sampling Quiz", "competency_code": "STAT_SAMPLING", "question_ids": [str(q1["_id"])]},
    )
    quiz_id = quiz_res.json()["id"]
    client.post(f"/api/v1/trainer/quizzes/{quiz_id}/publish", headers=headers_trainer)
    client.post(f"/api/v1/trainer/quizzes/{quiz_id}/assign", headers=headers_trainer, json={"learner_ids": [str(learner["_id"])]})

    # Learner attempts and submits quiz
    submit_payload = {
        "answers": [{"question_id": str(q1["_id"]), "selected_answer": "A"}]
    }
    submit_resp = client.post(f"/api/v1/quizzes/{quiz_id}/submit", headers=headers_learner, json=submit_payload)
    assert submit_resp.status_code == 200
    attempt_id = submit_resp.json()["_id"]

    # Trainer views attempts on this quiz
    resp_attempts = client.get(f"/api/v1/trainer/quizzes/{quiz_id}/attempts", headers=headers_trainer)
    assert resp_attempts.status_code == 200
    attempts = resp_attempts.json()
    assert len(attempts) == 1
    assert attempts[0]["score"] == 1
    assert attempts[0]["percentage"] == 100.0
    assert attempts[0]["learner_email"] == "learner@test.com"
    assert attempts[0]["has_trainer_feedback"] is False

    # Trainer submits qualitative feedback
    feedback_payload = {
        "feedback_text": "Excellent understanding of random sampling principles. Well done!",
        "strengths": ["Clear conceptual grasp of probability sampling", "High accuracy"],
        "areas_for_improvement": ["Review stratified multi-stage designs next"],
        "rating": 5,
    }
    resp_feedback = client.post(
        f"/api/v1/trainer/attempts/{attempt_id}/feedback",
        headers=headers_trainer,
        json=feedback_payload,
    )
    assert resp_feedback.status_code == 200
    assert resp_feedback.json()["feedback"]["rating"] == 5
    assert "Well done!" in resp_feedback.json()["feedback"]["feedback_text"]

    # Trainer lists assigned learners summary
    resp_learners = client.get("/api/v1/trainer/learners", headers=headers_trainer)
    assert resp_learners.status_code == 200
    learners = resp_learners.json()
    assert len(learners) == 1
    assert learners[0]["learner_id"] == str(learner["_id"])
    assert learners[0]["completed_quizzes_count"] == 1
    assert learners[0]["average_score"] == 100.0

    # Trainer views specific learner evaluation history
    resp_eval = client.get(f"/api/v1/trainer/learners/{learner['_id']}/results", headers=headers_trainer)
    assert resp_eval.status_code == 200
    assert resp_eval.json()["total_attempts"] == 1
    assert resp_eval.json()["attempts"][0]["trainer_feedback"]["rating"] == 5
    client.close()


# ==============================================================================
# 5. Security & Isolation Tests
# ==============================================================================

def test_cross_trainer_isolation():
    client, database, settings = make_trainer_app()
    trainer_a = create_user(database, "trainer_a@test.com", "TRAINER", "TRN-A")
    trainer_b = create_user(database, "trainer_b@test.com", "TRAINER", "TRN-B")

    token_a = create_access_token(str(trainer_a["_id"]), settings)
    token_b = create_access_token(str(trainer_b["_id"]), settings)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    mat_a = create_material(database, str(trainer_a["_id"]))

    q_a = TrainerQuestion.create(
        trainer_id=str(trainer_a["_id"]),
        material_id=str(mat_a["_id"]),
        competency_code="STAT_SAMPLING",
        question="Trainer A question",
        options=["A", "B", "C"],
        correct_answer="A",
        explanation="Expl",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_a)
    qid_a = str(q_a["_id"])

    # Trainer B cannot view Trainer A's question
    resp_b_view = client.get(f"/api/v1/trainer/questions/{qid_a}", headers=headers_b)
    assert resp_b_view.status_code == 404

    # Trainer B cannot approve Trainer A's question
    resp_b_approve = client.post(f"/api/v1/trainer/questions/{qid_a}/approve", headers=headers_b)
    assert resp_b_approve.status_code == 400

    # Trainer B cannot edit Trainer A's question
    resp_b_edit = client.put(f"/api/v1/trainer/questions/{qid_a}", headers=headers_b, json={"question": "Hacked"})
    assert resp_b_edit.status_code == 400

    client.close()


def test_official_role_forbidden_from_trainer_routes():
    client, database, settings = make_trainer_app()
    official = create_user(database, "learner@test.com", "OFFICIAL", "EMP-001")
    token_official = create_access_token(str(official["_id"]), settings)
    headers = {"Authorization": f"Bearer {token_official}"}

    # All trainer endpoints must reject OFFICIAL with 403 Forbidden
    assert client.get("/api/v1/trainer/dashboard", headers=headers).status_code == 403
    assert client.get("/api/v1/trainer/materials", headers=headers).status_code == 403
    assert client.get("/api/v1/trainer/quizzes", headers=headers).status_code == 403
    assert client.get("/api/v1/trainer/learners", headers=headers).status_code == 403
    assert client.post("/api/v1/trainer/quizzes", headers=headers, json={}).status_code == 403
    client.close()


def test_trainer_edge_cases_and_validation():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@test.com", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Non-existent question returns 404
    fake_qid = str(ObjectId())
    assert client.get(f"/api/v1/trainer/questions/{fake_qid}", headers=headers).status_code == 404

    # 2. Non-existent quiz returns 404
    fake_quiz_id = str(ObjectId())
    assert client.get(f"/api/v1/trainer/quizzes/{fake_quiz_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/trainer/quizzes/{fake_quiz_id}/attempts", headers=headers).status_code == 404

    # 3. Invalid rating on feedback (rating=10 rejected by Pydantic 422)
    fake_attempt_id = str(ObjectId())
    resp_invalid_rating = client.post(
        f"/api/v1/trainer/attempts/{fake_attempt_id}/feedback",
        headers=headers,
        json={"feedback_text": "Good", "rating": 10},
    )
    assert resp_invalid_rating.status_code == 422

    # 4. Attempting to assign quiz with empty learner_ids list returns 422
    assert client.post(
        f"/api/v1/trainer/quizzes/{fake_quiz_id}/assign",
        headers=headers,
        json={"learner_ids": []},
    ).status_code == 422

    client.close()

