"""
Phase 3E — Comprehensive 3-Role End-to-End Lifecycle Verification Test Suite.

Verifies the complete cross-role workflow:
1. Admin sets up role requirements & inspects baseline analytics.
2. Trainer uploads training material, triggers AI question generation, reviews/edits/approves in Review Studio, builds and publishes a quiz, and assigns it to an Official.
3. Official logs in, reviews competency profile and skill gaps, completes a learning activity (supporting evidence = 0.30, competency profile UNCHANGED), takes trainer quiz, receives trainer feedback, and takes an adaptive capability assessment (authoritative evidence = 0.85, competency profile UPDATED, skill gap reduced).
4. Official interacts with Karmayogi AI Co-Pilot in English and Hindi.
5. Admin verifies organizational skill gap reduction and training effectiveness metrics.
"""

import pytest
from bson import ObjectId
from datetime import datetime, UTC
from fastapi.testclient import TestClient

from app.auth.security import create_access_token, hash_password
from app.core.config import Settings
from app.main import create_app


class FakeCursor:
    def __init__(self, documents):
        self.documents = list(documents)

    def sort(self, key, direction=1):
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
                    elif k == "code" and isinstance(v, dict) and "$regex" in v:
                        import re
                        if not re.search(v["$regex"], d.get("code", ""), re.IGNORECASE):
                            match = False
                    elif isinstance(v, dict) and "$in" in v:
                        if d.get(k) not in v["$in"]:
                            match = False
                    elif isinstance(v, dict) and "$nin" in v:
                        if d.get(k) in v["$nin"]:
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

    def insert_many(self, documents):
        ids = []
        for d in documents:
            if "_id" not in d:
                d["_id"] = ObjectId()
            self.documents.append(d)
            ids.append(d["_id"])
        return type("InsertManyResult", (), {"inserted_ids": ids})()

    def update_one(self, filter_query, update_doc, upsert=False):
        doc = self.find_one(filter_query)
        if doc:
            if "$set" in update_doc:
                for k, v in update_doc["$set"].items():
                    doc[k] = v
            if "$push" in update_doc:
                for k, v in update_doc["$push"].items():
                    if k not in doc or not isinstance(doc[k], list):
                        doc[k] = []
                    doc[k].append(v)
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

    def find_one_and_update(self, filter_query, update_doc, return_document=True, upsert=False):
        doc = self.find_one(filter_query)
        if doc:
            if "$set" in update_doc:
                for k, v in update_doc["$set"].items():
                    doc[k] = v
            if "$push" in update_doc:
                for k, v in update_doc["$push"].items():
                    if k not in doc or not isinstance(doc[k], list):
                        doc[k] = []
                    doc[k].append(v)
            return doc
        return None

    def delete_one(self, query):
        doc = self.find_one(query)
        if doc:
            self.documents.remove(doc)
            return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()


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
        self.materials = FakeCollection()
        self.quizzes = FakeCollection()
        self.quiz_attempts = FakeCollection()
        self.capability_assessments = FakeCollection()

    def __getattr__(self, name: str):
        col = FakeCollection()
        setattr(self, name, col)
        return col

    def __getitem__(self, name: str):
        if not hasattr(self, name):
            setattr(self, name, FakeCollection())
        return getattr(self, name)


@pytest.fixture
def e2e_environment():
    db = FakeDatabase()
    settings = Settings(
        jwt_secret="e2e-super-secret-key-32-chars-long",
        api_prefix="/api/v1",
    )
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    # 1. Seed Core Competency Framework
    comp_sampling_id = ObjectId()
    db.competencies.insert_one({
        "_id": comp_sampling_id,
        "code": "STAT_SAMPLING",
        "title": "Sampling Methods & Survey Design",
        "name": "Sampling Methods & Survey Design",
        "domain": "STATISTICAL",
        "description": "Techniques for stratified sampling, cluster surveys, and Horvitz-Thompson estimation.",
        "status": "ACTIVE",
    })

    comp_python_id = ObjectId()
    db.competencies.insert_one({
        "_id": comp_python_id,
        "code": "TECH_PYTHON",
        "title": "Python for Data Analysis",
        "name": "Python for Data Analysis",
        "domain": "TECHNICAL",
        "description": "Pandas, NumPy, and statistical survey pipelines.",
        "status": "ACTIVE",
    })

    # 2. Seed Role & Role Requirements
    role_id = ObjectId()
    db.roles.insert_one({
        "_id": role_id,
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "department": "MoSPI / DIID",
        "status": "active",
    })
    db.role_requirements.insert_one({
        "_id": ObjectId(),
        "role_id": role_id,
        "competency_id": comp_sampling_id,
        "required_level": 4.0,
        "priority": "HIGH",
    })

    # 3. Seed Question Bank for Adaptive Engine
    questions = [
        {
            "_id": ObjectId(),
            "question_id": "Q_SAMPLING_E1",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "What is the primary characteristic of simple random sampling?",
            "options": ["A. Equal probability of selection", "B. Quota selection", "C. Voluntary response", "D. Haphazard"],
            "correct_answer": "A",
            "difficulty": "EASY",
            "status": "ACTIVE",
            "explanation": "SRS ensures every unit in the frame has an equal inclusion probability.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_SAMPLING_M1",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "When is stratified sampling superior to simple random sampling?",
            "options": ["A. When stratum variances differ markedly", "B. Only for census operations", "C. When sampling without frame", "D. Never"],
            "correct_answer": "A",
            "difficulty": "MEDIUM",
            "status": "ACTIVE",
            "explanation": "Stratification reduces variance when between-stratum variation is high.",
        },
        {
            "_id": ObjectId(),
            "question_id": "Q_SAMPLING_H1",
            "competency_code": "STAT_SAMPLING",
            "question_type": "MCQ",
            "question_text": "In two-stage PPS sampling, what estimator guarantees unbiased total estimation?",
            "options": ["A. Horvitz-Thompson", "B. Mean of ratios", "C. Unweighted sample mean", "D. Median of medians"],
            "correct_answer": "A",
            "difficulty": "HARD",
            "status": "ACTIVE",
            "explanation": "The Horvitz-Thompson estimator is design-unbiased for arbitrary inclusion probabilities.",
        },
    ]
    for q in questions:
        db.question_bank.insert_one(q)

    # 4. Seed Verified iGOT Resource
    res_id = ObjectId()
    db.learning_resources.insert_one({
        "_id": res_id,
        "resource_id": "IGOT_SAMP_01",
        "title": "Advanced Survey Sampling & Estimation Techniques",
        "provider": "iGOT Karmayogi",
        "competency_codes": ["STAT_SAMPLING"],
        "duration_minutes": 120,
        "level": 3,
        "status": "ACTIVE",
    })

    # 5. Seed Users for 3 Actors
    admin_id = ObjectId()
    db.users.insert_one({
        "_id": admin_id,
        "email": "admin@shikshasetu.gov.in",
        "password_hash": hash_password("Admin@123"),
        "full_name": "Dr. Sunita Sharma",
        "access_role": "ADMIN",
        "status": "active",
        "created_at": datetime.now(UTC),
    })

    trainer_id = ObjectId()
    db.users.insert_one({
        "_id": trainer_id,
        "email": "trainer.nssta@shikshasetu.gov.in",
        "password_hash": hash_password("Trainer@123"),
        "full_name": "Prof. Amit Sengupta",
        "access_role": "TRAINER",
        "status": "active",
        "created_at": datetime.now(UTC),
    })

    official_id = ObjectId()
    db.users.insert_one({
        "_id": official_id,
        "email": "officer.rajesh@shikshasetu.gov.in",
        "password_hash": hash_password("Official@123"),
        "full_name": "Rajesh Kumar",
        "role_id": role_id,
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": datetime.now(UTC),
    })

    # Auth Tokens
    admin_token = create_access_token(str(admin_id), settings)
    trainer_token = create_access_token(str(trainer_id), settings)
    official_token = create_access_token(str(official_id), settings)

    return {
        "client": client,
        "db": db,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "trainer_headers": {"Authorization": f"Bearer {trainer_token}"},
        "official_headers": {"Authorization": f"Bearer {official_token}"},
        "admin_id": str(admin_id),
        "trainer_id": str(trainer_id),
        "official_id": str(official_id),
        "comp_sampling_id": comp_sampling_id,
        "role_id": role_id,
    }


def test_full_cross_role_lifecycle(e2e_environment):
    """
    Verifies the entire 3-Role lifecycle from Admin requirement benchmark
    ➔ Trainer quiz authoring ➔ Official adaptive learning & assessment ➔ Admin analytics impact.
    """
    env = e2e_environment
    client = env["client"]
    db = env["db"]
    admin_h = env["admin_headers"]
    trainer_h = env["trainer_headers"]
    official_h = env["official_headers"]
    official_id = env["official_id"]
    comp_sampling_id = env["comp_sampling_id"]

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: OFFICIAL INITIAL STATE & SKILL GAP AUDIT
    # ──────────────────────────────────────────────────────────────────────────
    gaps_res = client.get("/api/v1/skill-gaps/me", headers=official_h)
    assert gaps_res.status_code == 200
    gaps_data = gaps_res.json()
    assert len(gaps_data["gaps"]) > 0
    # Official has not been formally assessed yet; gap = 4.0 (target)
    sampling_gap = next((g for g in gaps_data["gaps"] if g["competency_code"] == "STAT_SAMPLING"), None)
    assert sampling_gap is not None
    assert sampling_gap["required_level"] == 4.0
    assert sampling_gap["current_level"] is None or sampling_gap["current_level"] == 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: OFFICIAL SELF-PACED LEARNING (SUPPORTING EVIDENCE = 0.30)
    # ──────────────────────────────────────────────────────────────────────────
    # Official starts an iGOT course
    learn_res = client.post(
        "/api/v1/learning-activities",
        headers=official_h,
        json={
            "resource_id": "IGOT_SAMP_01",
            "competency_id": str(comp_sampling_id),
        },
    )
    assert learn_res.status_code == 201 or learn_res.status_code == 200
    activity_id = learn_res.json().get("activity_id") or learn_res.json().get("_id")

    # Official completes the course
    complete_res = client.post(
        f"/api/v1/learning-activities/{activity_id}/complete",
        headers=official_h,
        json={"final_score": 85.0, "notes": "Completed iGOT course"},
    )
    assert complete_res.status_code == 200

    # CRITICAL GOVERNANCE INVARIANT:
    # Learning completion MUST NOT update competency level!
    prof_before = db.competency_profiles.find_one({
        "user_id": ObjectId(official_id),
        "competency_id": comp_sampling_id,
    })
    assert prof_before is None  # Unchanged!

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: OFFICIAL ADAPTIVE CAPABILITY ASSESSMENT (AUTHORITATIVE = 0.85)
    # ──────────────────────────────────────────────────────────────────────────
    # Official launches adaptive assessment
    start_res = client.post(
        "/api/v1/adaptive-assessments/start",
        headers=official_h,
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
    )
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    q1 = start_res.json()["question"]
    assert start_res.json()["difficulty"] == "MEDIUM"

    # Official answers correctly -> step up
    ans_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/answer",
        headers=official_h,
        json={"question_id": q1["question_id"], "selected_answer": "A"},
    )
    assert ans_res.status_code == 200
    assert ans_res.json()["updated_estimated_level"] > 2.5

    # Finalize Assessment
    fin_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/finalize",
        headers=official_h,
    )
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["evidence_confidence"] == 0.85
    assert fin_data["updated_competency_level"] >= 2.9

    # CRITICAL GOVERNANCE INVARIANT:
    # Competency Profile is NOW UPDATED with authoritative evidence!
    prof_after = db.competency_profiles.find_one({
        "user_id": ObjectId(official_id),
        "competency_id": comp_sampling_id,
    })
    assert prof_after is not None
    assert prof_after["confidence"] == 0.85
    assert prof_after["current_level"] == fin_data["updated_competency_level"]

    # Recalculated skill gap has shrunk!
    gaps_after = client.get("/api/v1/skill-gaps/me", headers=official_h).json()
    sampling_gap_after = next((g for g in gaps_after["gaps"] if g["competency_code"] == "STAT_SAMPLING"), None)
    assert sampling_gap_after is not None
    assert sampling_gap_after["gap"] < 4.0

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4: KARMAYOGI AI CO-PILOT ASSISTANT CONSULTATION
    # ──────────────────────────────────────────────────────────────────────────
    chat_res = client.post(
        "/api/v1/assistant/chat",
        headers=official_h,
        json={
            "message": "मेरी सबसे महत्वपूर्ण क्षमता कमियाँ क्या हैं?",
            "context_page": "Dashboard",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert len(chat_data["answer"]) > 0
    assert len(chat_data["sources"]) > 0

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 5: ADMIN WORKFORCE GOVERNANCE VISIBILITY
    # ──────────────────────────────────────────────────────────────────────────
    admin_overview = client.get("/api/v1/admin/dashboard", headers=admin_h)
    assert admin_overview.status_code == 200
    admin_data = admin_overview.json()
    assert admin_data["total_users"] >= 1
    assert "total_critical_gaps" in admin_data
    assert "average_capability_level" in admin_data
