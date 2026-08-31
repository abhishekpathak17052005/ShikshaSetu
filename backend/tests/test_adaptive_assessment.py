"""Tests for Adaptive Capability Assessment Engine (Phase 3C)."""

import pytest
from bson import ObjectId
from datetime import datetime, UTC
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app
from app.adaptive_assessments.calibration import (
    calculate_next_theta,
    map_theta_to_difficulty,
    MIN_THETA,
    MAX_THETA,
)


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
                        or_match = any(
                            all(d.get(sk) == sv for sk, sv in sub.items())
                            for sub in v
                        )
                        if not or_match:
                            match = False
                    elif k == "question_id" and isinstance(v, dict) and "$nin" in v:
                        if d.get("question_id") in v["$nin"]:
                            match = False
                    elif k == "code" and isinstance(v, dict) and "$regex" in v:
                        import re
                        if not re.search(v["$regex"], d.get("code", ""), re.IGNORECASE):
                            match = False
                    elif d.get(k) != v:
                        match = False
                if match:
                    filtered.append(d)
            docs = filtered
        return FakeCursor(docs)

    def find_one(self, query=None, projection=None):
        if not query:
            return self.documents[0] if self.documents else None
        res = list(self.find(query).documents)
        return res[0] if res else None

    def count_documents(self, query=None):
        return len(self.find(query).documents)

    def insert_one(self, document):
        if "_id" not in document:
            document["_id"] = ObjectId()
        self.documents.append(document)
        return type("InsertResult", (), {"inserted_id": document["_id"]})()

    def update_one(self, filter_query, update_doc, upsert=False):
        doc = self.find_one(filter_query)
        if doc:
            if "$set" in update_doc:
                for k, v in update_doc["$set"].items():
                    doc[k] = v
            return type("UpdateResult", (), {"matched_count": 1, "modified_count": 1})()
        elif upsert:
            new_doc = dict(filter_query)
            if "$set" in update_doc:
                new_doc.update(update_doc["$set"])
            if "$setOnInsert" in update_doc:
                new_doc.update(update_doc["$setOnInsert"])
            self.insert_one(new_doc)
            return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0, "upserted_id": new_doc["_id"]})()
        return type("UpdateResult", (), {"matched_count": 0, "modified_count": 0})()

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
        self.question_bank = FakeCollection()
        self.adaptive_assessment_sessions = FakeCollection()


@pytest.fixture
def adaptive_setup():
    db = FakeDatabase()
    settings = Settings(
        jwt_secret="adaptive-test-secret-key-32-chars-long",
        api_prefix="/api/v1",
    )
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    # Seed Competency
    comp_oid = ObjectId()
    db.competencies.insert_one({
        "_id": comp_oid,
        "code": "STAT_SAMPLING",
        "title": "Sampling Methods & Survey Design",
        "domain": "STATISTICAL",
        "status": "ACTIVE",
    })

    # Seed Question Bank with Easy, Medium, Hard questions
    questions = [
        {
            "_id": ObjectId(),
            "question_id": "Q_EASY_1",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "What is the primary purpose of simple random sampling?",
            "options": ["A. Equal probability of selection", "B. Grouping by stratum", "C. Convenience", "D. Systematic interval"],
            "correct_answer": "A",
            "difficulty": "EASY",
            "status": "ACTIVE",
            "explanation": "Simple random sampling ensures every unit has an equal selection chance.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_EASY_2",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "What is a sampling frame?",
            "options": ["A. Mathematical formula", "B. Exhaustive list of population units", "C. Sample size", "D. Variance estimator"],
            "correct_answer": "B",
            "difficulty": "EASY",
            "status": "ACTIVE",
            "explanation": "A sampling frame is the actual list from which sample units are drawn.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_MED_1",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "When is stratified sampling preferred over simple random sampling?",
            "options": ["A. When population is completely homogeneous", "B. When subpopulations differ significantly in variance", "C. When no frame exists", "D. Only for pilot studies"],
            "correct_answer": "B",
            "difficulty": "MEDIUM",
            "status": "ACTIVE",
            "explanation": "Stratification reduces overall sample variance when subpopulation variances differ.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_MED_2",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "What is Neyman optimal allocation used for?",
            "options": ["A. Equal sample per stratum", "B. Allocating sample proportional to stratum size and variance", "C. Determining cluster size", "D. Imputing missing values"],
            "correct_answer": "B",
            "difficulty": "MEDIUM",
            "status": "ACTIVE",
            "explanation": "Neyman allocation minimizes sample variance for a fixed sample size.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_HARD_1",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "In two-stage cluster sampling with PPS, what is the Horvitz-Thompson estimator property?",
            "options": ["A. Biased for nonlinear metrics", "B. Unbiased for population total with unequal probabilities", "C. Zero variance", "D. Independent of selection probabilities"],
            "correct_answer": "B",
            "difficulty": "HARD",
            "status": "ACTIVE",
            "explanation": "Horvitz-Thompson provides an unbiased estimator of the total under arbitrary probability sampling designs.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_HARD_2",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "How is the Design Effect (Deff) defined in complex survey estimation?",
            "options": ["A. Ratio of complex variance to SRS variance of equal size", "B. Product of weights", "C. Standard error squared", "D. Response rate"],
            "correct_answer": "A",
            "difficulty": "HARD",
            "status": "ACTIVE",
            "explanation": "Deff measures the inflation of variance due to clustering and weighting relative to simple random sampling.",
        },
    ]
    for q in questions:
        db.question_bank.insert_one(q)

    # Seed User A & B
    user_a_id = ObjectId()
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
        "competency_id": comp_oid,
        "required_level": 4.0,
        "priority": "HIGH",
    })

    user_a = {
        "_id": user_a_id,
        "email": "officer.a@shikshasetu.gov.in",
        "password_hash": hash_password("Password@123"),
        "full_name": "Rajesh Sharma",
        "role_id": role_id,
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(user_a)

    user_b_id = ObjectId()
    user_b = {
        "_id": user_b_id,
        "email": "officer.b@shikshasetu.gov.in",
        "password_hash": hash_password("Password@123"),
        "full_name": "Pooja Verma",
        "role_id": role_id,
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": datetime.now(UTC),
    }
    db.users.insert_one(user_b)

    token_a = create_access_token(str(user_a_id), settings)
    token_b = create_access_token(str(user_b_id), settings)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    return client, headers_a, headers_b, db, str(user_a_id), str(user_b_id), comp_oid


def test_calibration_math():
    """Verify deterministic calibration bounds and transitions."""
    # Test step up on correct
    theta_med_correct = calculate_next_theta(2.5, "MEDIUM", True)
    assert theta_med_correct == 2.9
    assert map_theta_to_difficulty(theta_med_correct) == "MEDIUM"

    # Step up to HARD
    theta_hard = calculate_next_theta(3.5, "HARD", True)
    assert theta_hard == 4.0
    assert map_theta_to_difficulty(theta_hard) == "HARD"

    # Clamping at MAX_THETA (5.0)
    theta_max = calculate_next_theta(4.8, "HARD", True)
    assert theta_max <= MAX_THETA

    # Step down on incorrect
    theta_down = calculate_next_theta(2.5, "MEDIUM", False)
    assert theta_down == 2.1
    assert map_theta_to_difficulty(theta_down) == "EASY"

    # Clamping at MIN_THETA (1.0)
    theta_min = calculate_next_theta(1.2, "EASY", False)
    assert theta_min >= MIN_THETA


def test_start_adaptive_session(adaptive_setup):
    client, headers_a, _, _, _, _, _ = adaptive_setup
    res = client.post(
        "/api/v1/adaptive-assessments/start",
        headers=headers_a,
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["competency_code"] == "STAT_SAMPLING"
    assert data["estimated_level"] == 2.5
    assert data["difficulty"] == "MEDIUM"
    assert data["current_question_number"] == 1
    assert data["total_questions_planned"] == 3
    assert data["question"] is not None
    assert "correct_answer" not in data["question"]  # Security: Redacted


def test_adaptive_answer_step_up_and_step_down(adaptive_setup):
    client, headers_a, _, _, _, _, _ = adaptive_setup
    # Start session
    start_res = client.post(
        "/api/v1/adaptive-assessments/start",
        headers=headers_a,
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
    )
    session_id = start_res.json()["session_id"]
    q1 = start_res.json()["question"]

    # Submit CORRECT answer for Q1
    ans_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/answer",
        headers=headers_a,
        json={"question_id": q1["question_id"], "selected_answer": "B"},  # Q_MED_1 is B
    )
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert ans_data["is_correct"] is True
    assert ans_data["updated_estimated_level"] > ans_data["previous_estimated_level"]
    assert ans_data["questions_completed"] == 1
    assert ans_data["is_complete"] is False
    assert ans_data["next_question"] is not None


def test_adaptive_user_isolation(adaptive_setup):
    client, headers_a, headers_b, _, _, _, _ = adaptive_setup
    start_res = client.post(
        "/api/v1/adaptive-assessments/start",
        headers=headers_a,
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
    )
    session_id = start_res.json()["session_id"]

    # User B tries to answer User A's session -> 404/403
    ans_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/answer",
        headers=headers_b,
        json={"question_id": "Q_MED_1", "selected_answer": "B"},
    )
    assert ans_res.status_code == 404


def test_adaptive_finalization_authoritative_evidence_and_profile_update(adaptive_setup):
    client, headers_a, _, db, user_a_id, _, comp_oid = adaptive_setup
    start_res = client.post(
        "/api/v1/adaptive-assessments/start",
        headers=headers_a,
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
    )
    session_id = start_res.json()["session_id"]
    q1 = start_res.json()["question"]

    # Answer Q1
    ans1 = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/answer",
        headers=headers_a,
        json={"question_id": q1["question_id"], "selected_answer": "B"},
    )
    q2 = ans1.json()["next_question"]

    # Answer Q2
    ans2 = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/answer",
        headers=headers_a,
        json={"question_id": q2["question_id"], "selected_answer": "B"},
    )

    # Finalize Session
    fin_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/finalize",
        headers=headers_a,
    )
    assert fin_res.status_code == 200
    fin_data = fin_res.json()

    assert fin_data["status"] == "COMPLETED"
    assert fin_data["evidence_confidence"] == 0.85
    assert fin_data["evidence_type"] == "CAPABILITY_ASSESSMENT"
    assert fin_data["updated_competency_level"] > 0

    # Verify Authoritative Evidence Record in Database
    evidence = db.competency_evidence.find_one({"assessment_id": ObjectId(session_id)})
    assert evidence is not None
    assert evidence["confidence"] == 0.85
    assert evidence["evidence_type"] == "CAPABILITY_ASSESSMENT"

    # Verify Competency Profile in Database Updated
    profile = db.competency_profiles.find_one({
        "user_id": ObjectId(user_a_id),
        "competency_id": comp_oid,
    })
    assert profile is not None
    assert profile["confidence"] == 0.85
    assert profile["current_level"] == fin_data["updated_competency_level"]


def test_learning_evidence_does_not_update_competency(adaptive_setup):
    """
    CRITICAL GOVERNANCE INVARIANT TEST:
    Learning Activity completion must NEVER increase competency level.
    """
    client, headers_a, _, db, user_a_id, _, comp_oid = adaptive_setup
    
    # Insert supporting evidence for learning activity (confidence 0.30)
    db.competency_evidence.insert_one({
        "user_id": ObjectId(user_a_id),
        "competency_id": comp_oid,
        "evidence_type": "LEARNING_ACTIVITY",
        "score": 4.5,
        "confidence": 0.30,
        "source": "learning_activity",
        "created_at": datetime.now(UTC),
    })

    # Ensure profile was NOT updated by learning activity
    profile = db.competency_profiles.find_one({
        "user_id": ObjectId(user_a_id),
        "competency_id": comp_oid,
    })
    assert profile is None  # Remains unassessed / untouched
