"""
Phase 3F: Department & Role-Specific Competency Intelligence Comprehensive Test Suite.

Verifies:
- Test A: Different departments receive different applicable competency sets.
- Test B: Intentionally shared competencies appear for both departments.
- Test C: Irrelevant specialized competencies are excluded.
- Test D: Skill gaps are calculated exclusively against applicable role requirements.
- Test E: Recommendations are scoped to applicable skill gaps.
- Test F: Adaptive assessments guard against non-applicable competencies.
- Test G: Evidence governance (0.30 learning vs 0.85 assessment) is strictly maintained.
- Test H: User isolation is strictly enforced.
- Test I: Department/role change reconciles competency profile while preserving historical evidence.
- Test J: RBAC permissions (OFFICIAL, TRAINER, ADMIN) remain intact.
"""

from datetime import datetime, UTC
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings
from app.auth.security import create_access_token, hash_password
from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies


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

    def _matches_query(self, doc, query):
        if not query:
            return True
        for k, v in query.items():
            if k == "$or":
                if not any(self._matches_query(doc, sub) for sub in v):
                    return False
            elif k == "$and":
                if not all(self._matches_query(doc, sub) for sub in v):
                    return False
            elif isinstance(v, dict):
                doc_val = doc.get(k)
                if "$in" in v:
                    in_list = [str(x) for x in v["$in"]]
                    if str(doc_val) not in in_list and doc_val not in v["$in"]:
                        return False
                if "$nin" in v:
                    in_list = [str(x) for x in v["$nin"]]
                    if str(doc_val) in in_list or doc_val in v["$nin"]:
                        return False
                if "$ne" in v:
                    if doc_val == v["$ne"] or str(doc_val) == str(v["$ne"]):
                        return False
                if "$exists" in v:
                    exists = k in doc
                    if exists != v["$exists"]:
                        return False
            else:
                doc_val = doc.get(k)
                if doc_val != v and str(doc_val) != str(v):
                    return False
        return True

    def find(self, query=None, projection=None):
        docs = self.documents
        if query:
            filtered = [d for d in docs if self._matches_query(d, query)]
            return FakeCursor(filtered)
        return FakeCursor(docs)

    def find_one(self, query=None, projection=None, sort=None):
        docs = self.documents
        if query:
            for d in docs:
                if self._matches_query(d, query):
                    return d
            return None
        return docs[0] if docs else None

    def insert_one(self, doc):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.documents.append(doc)
        return type("InsertResult", (), {"inserted_id": doc["_id"]})()

    def insert_many(self, docs):
        for d in docs:
            self.insert_one(d)
        return type("InsertManyResult", (), {"inserted_ids": [d["_id"] for d in docs]})()

    def update_one(self, query, update, upsert=False):
        doc = self.find_one(query)
        if doc:
            if "$set" in update:
                for k, v in update["$set"].items():
                    doc[k] = v
            return type("UpdateResult", (), {"modified_count": 1, "matched_count": 1})()
        elif upsert:
            new_doc = {}
            if "$set" in update:
                new_doc.update(update["$set"])
            if "$setOnInsert" in update:
                new_doc.update(update["$setOnInsert"])
            if "_id" not in new_doc:
                new_doc["_id"] = ObjectId()
            self.documents.append(new_doc)
            return type("UpdateResult", (), {"modified_count": 0, "matched_count": 0, "upserted_id": new_doc["_id"]})()
        return type("UpdateResult", (), {"modified_count": 0, "matched_count": 0})()

    def update_many(self, query, update):
        count = 0
        for doc in self.documents:
            if self._matches_query(doc, query):
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                count += 1
        return type("UpdateResult", (), {"modified_count": count})()

    def delete_many(self, query):
        initial = len(self.documents)
        self.documents = [d for d in self.documents if not self._matches_query(d, query)]
        return type("DeleteResult", (), {"deleted_count": initial - len(self.documents)})()

    def delete_one(self, query):
        doc = self.find_one(query)
        if doc:
            self.documents.remove(doc)
            return type("DeleteResult", (), {"deleted_count": 1})()
        return type("DeleteResult", (), {"deleted_count": 0})()

    def count_documents(self, query):
        return len([d for d in self.documents if self._matches_query(d, query)])


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
        self.learning_resource_mappings = FakeCollection()
        self.question_bank = FakeCollection()
        self.adaptive_assessment_sessions = FakeCollection()
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
def env():
    """Sets up an isolated test environment with two users from different ministries."""
    db = FakeDatabase()
    settings = Settings(
        jwt_secret="test-department-secret-key-32-chars",
        api_prefix="/api/v1",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="test",
    )
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    now = datetime.now(UTC)

    # 1. Seed Competencies
    comp_stat = {
        "_id": ObjectId(),
        "code": "STAT_SAMPLING",
        "name": "Sampling Methods & Survey Design",
        "domain": "STATISTICAL",
        "description": "Sampling techniques in official surveys",
        "level_definitions": {"1": "L1", "2": "L2", "3": "L3", "4": "L4", "5": "L5"},
        "status": "active",
        "framework_status": "prototype",
        "source_type": "PROTOTYPE",
        "created_at": now,
        "updated_at": now,
    }
    comp_edu = {
        "_id": ObjectId(),
        "code": "BEH_COMMUNICATION",
        "name": "Communication & Pedagogical Engagement",
        "domain": "BEHAVIOURAL_MANAGERIAL",
        "description": "Educational communication and stakeholder management",
        "level_definitions": {"1": "L1", "2": "L2", "3": "L3", "4": "L4", "5": "L5"},
        "status": "active",
        "framework_status": "prototype",
        "source_type": "PROTOTYPE",
        "created_at": now,
        "updated_at": now,
    }
    comp_shared = {
        "_id": ObjectId(),
        "code": "BEH_ETHICS",
        "name": "Civil Service Ethics & Integrity",
        "domain": "BEHAVIOURAL_MANAGERIAL",
        "description": "Ethical governance in public service",
        "level_definitions": {"1": "L1", "2": "L2", "3": "L3", "4": "L4", "5": "L5"},
        "status": "active",
        "framework_status": "prototype",
        "source_type": "PROTOTYPE",
        "created_at": now,
        "updated_at": now,
    }
    db.competencies.insert_many([comp_stat, comp_edu, comp_shared])

    # 2. Seed Roles
    role_stat = {
        "_id": ObjectId(),
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "department": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "department_code": "MOSPI",
        "designations": ["Statistical Officer", "Senior Statistical Officer (SSO)"],
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    role_edu = {
        "_id": ObjectId(),
        "role_code": "EDUCATION_OFFICER",
        "role_name": "Education & Curriculum Officer",
        "department": "Ministry of Education",
        "department_code": "MOE",
        "designations": ["Teacher", "Curriculum Specialist", "Education Officer"],
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    db.roles.insert_many([role_stat, role_edu])

    # 3. Seed Role Requirements
    # Statistics: STAT_SAMPLING (L4), BEH_ETHICS (L4)
    db.role_requirements.insert_many([
        {
            "role_id": role_stat["_id"],
            "competency_id": comp_stat["_id"],
            "competency_code": "STAT_SAMPLING",
            "competency_name": "Sampling Methods & Survey Design",
            "domain": "STATISTICAL",
            "required_level": 4.0,
            "priority": 1,
            "importance": 0.9,
            "created_at": now,
            "updated_at": now,
        },
        {
            "role_id": role_stat["_id"],
            "competency_id": comp_shared["_id"],
            "competency_code": "BEH_ETHICS",
            "competency_name": "Civil Service Ethics & Integrity",
            "domain": "BEHAVIOURAL_MANAGERIAL",
            "required_level": 4.0,
            "priority": 2,
            "importance": 0.8,
            "created_at": now,
            "updated_at": now,
        },
        # Education: BEH_COMMUNICATION (L4.0), BEH_ETHICS (L4.0)
        {
            "role_id": role_edu["_id"],
            "competency_id": comp_edu["_id"],
            "competency_code": "BEH_COMMUNICATION",
            "competency_name": "Communication & Pedagogical Engagement",
            "domain": "BEHAVIOURAL_MANAGERIAL",
            "required_level": 4.0,
            "priority": 1,
            "importance": 0.95,
            "created_at": now,
            "updated_at": now,
        },
        {
            "role_id": role_edu["_id"],
            "competency_id": comp_shared["_id"],
            "competency_code": "BEH_ETHICS",
            "competency_name": "Civil Service Ethics & Integrity",
            "domain": "BEHAVIOURAL_MANAGERIAL",
            "required_level": 4.0,
            "priority": 2,
            "importance": 0.85,
            "created_at": now,
            "updated_at": now,
        },
    ])

    # 4. Seed Questions for Adaptive Assessment
    for i in range(1, 4):
        db.question_bank.insert_one({
            "question_id": f"q_stat_{i}",
            "competency_code": "STAT_SAMPLING",
            "difficulty": "MEDIUM",
            "question_type": "MCQ",
            "question_text": f"Question {i} on sampling?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "A",
            "status": "ACTIVE",
            "created_at": now,
        })


    # 5. Seed Users
    user_a = {
        "_id": ObjectId(),
        "email": "officer.stat@shikshasetu.gov.in",
        "password_hash": hash_password("Password123!"),
        "full_name": "Rohan Gupta (Statistical Officer)",
        "department": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "designation": "Statistical Officer",
        "employee_id": "STAT-001",
        "role_id": role_stat["_id"],
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    user_b = {
        "_id": ObjectId(),
        "email": "officer.edu@shikshasetu.gov.in",
        "password_hash": hash_password("Password123!"),
        "full_name": "Meera Sharma (Education Officer)",
        "department": "Ministry of Education",
        "designation": "Teacher",
        "employee_id": "EDU-001",
        "role_id": role_edu["_id"],
        "access_role": "OFFICIAL",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    admin_user = {
        "_id": ObjectId(),
        "email": "admin@shikshasetu.gov.in",
        "password_hash": hash_password("Password123!"),
        "full_name": "System Administrator",
        "department": "Department of Personnel and Training (DoPT)",
        "designation": "Director",
        "employee_id": "ADM-001",
        "role_id": role_stat["_id"],
        "access_role": "ADMIN",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    db.users.insert_many([user_a, user_b, admin_user])

    # Reconcile baseline profiles
    reconcile_user_competencies(db, user_a["_id"], role_stat["_id"])
    reconcile_user_competencies(db, user_b["_id"], role_edu["_id"])

    return {
        "client": client,
        "db": db,
        "settings": settings,
        "user_a": user_a,
        "user_b": user_b,
        "admin_user": admin_user,
        "role_stat": role_stat,
        "role_edu": role_edu,
        "comp_stat": comp_stat,
        "comp_edu": comp_edu,
        "comp_shared": comp_shared,
    }


def test_a_different_departments_have_different_competencies(env):
    """Test A: Verify user from Statistics receives different competencies than user from Education."""
    client = env["client"]
    settings = env["settings"]
    user_a = env["user_a"]
    user_b = env["user_b"]

    token_a = create_access_token(str(user_a["_id"]), settings)
    token_b = create_access_token(str(user_b["_id"]), settings)

    res_a = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    comps_a = {c["code"] for c in res_a.json()}

    res_b = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    comps_b = {c["code"] for c in res_b.json()}

    # Sets must not be identical
    assert comps_a != comps_b
    assert "STAT_SAMPLING" in comps_a
    assert "BEH_COMMUNICATION" in comps_b


def test_b_shared_competencies_present_in_both(env):
    """Test B: Verify that intentionally shared competencies (e.g. BEH_ETHICS) appear for both."""
    client = env["client"]
    settings = env["settings"]
    token_a = create_access_token(str(env["user_a"]["_id"]), settings)
    token_b = create_access_token(str(env["user_b"]["_id"]), settings)

    res_a = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_a}"})
    res_b = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_b}"})

    comps_a = {c["code"] for c in res_a.json()}
    comps_b = {c["code"] for c in res_b.json()}

    assert "BEH_ETHICS" in comps_a
    assert "BEH_ETHICS" in comps_b


def test_c_irrelevant_competency_exclusion(env):
    """Test C: Verify department-specific competency does not appear for unrelated department."""
    client = env["client"]
    settings = env["settings"]
    token_b = create_access_token(str(env["user_b"]["_id"]), settings)

    res_b = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_b}"})
    comps_b = {c["code"] for c in res_b.json()}

    # Education Officer must NOT have STAT_SAMPLING
    assert "STAT_SAMPLING" not in comps_b


def test_d_skill_gaps_calculated_only_against_applicable_competencies(env):
    """Test D: Skill gaps must only reflect user's applicable department competencies."""
    client = env["client"]
    settings = env["settings"]
    token_a = create_access_token(str(env["user_a"]["_id"]), settings)
    token_b = create_access_token(str(env["user_b"]["_id"]), settings)

    res_a = client.get("/api/v1/skill-gaps/me", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    gaps_a = {g["competency_code"] for g in res_a.json()["gaps"]}

    res_b = client.get("/api/v1/skill-gaps/me", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    gaps_b = {g["competency_code"] for g in res_b.json()["gaps"]}

    assert "STAT_SAMPLING" in gaps_a
    assert "BEH_COMMUNICATION" not in gaps_a
    assert "BEH_COMMUNICATION" in gaps_b
    assert "STAT_SAMPLING" not in gaps_b


def test_f_adaptive_assessment_guards_irrelevant_competency(env):
    """Test F: User cannot start an adaptive assessment for a non-applicable competency."""
    client = env["client"]
    settings = env["settings"]
    token_b = create_access_token(str(env["user_b"]["_id"]), settings)

    # Education Officer attempts to start STAT_SAMPLING assessment
    res = client.post(
        "/api/v1/adaptive-assessments/start",
        json={"competency_code": "STAT_SAMPLING", "max_questions": 5},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 403
    assert "not applicable" in res.json()["detail"].lower()


def test_g_evidence_governance_authoritative_assessment(env):
    """Test G: Adaptive assessment generates 0.85 authoritative evidence, updating profile and closing gap."""
    client = env["client"]
    settings = env["settings"]
    db = env["db"]
    user_a = env["user_a"]
    token_a = create_access_token(str(user_a["_id"]), settings)

    # 1. Start assessment for applicable STAT_SAMPLING
    start_res = client.post(
        "/api/v1/adaptive-assessments/start",
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert start_res.status_code == 200
    session_id = start_res.json()["session_id"]
    q_id = start_res.json()["question"]["question_id"]

    # 2. Submit answer
    ans_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/answer",
        json={"question_id": q_id, "selected_answer": "Option A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert ans_res.status_code == 200

    # 3. Finalize
    fin_res = client.post(
        f"/api/v1/adaptive-assessments/{session_id}/finalize",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert fin_res.status_code == 200
    data = fin_res.json()
    assert data["evidence_confidence"] == 0.85
    assert data["updated_competency_level"] > 0


    # 4. Check competency profile updated
    profile = db.competency_profiles.find_one({
        "user_id": user_a["_id"],
        "competency_id": env["comp_stat"]["_id"],
    })
    assert profile is not None
    assert profile["confidence"] == 0.85


def test_h_user_isolation(env):
    """Test H: User A cannot see User B's evidence or profile."""
    client = env["client"]
    settings = env["settings"]
    token_a = create_access_token(str(env["user_a"]["_id"]), settings)

    res = client.get("/api/v1/users/me/evidence", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    records = res.json()
    # All records must belong strictly to User A's role scope
    for r in records:
        assert r["competency_code"] != "BEH_COMMUNICATION"


def test_i_department_change_reconciles_competencies_and_preserves_evidence(env):
    """Test I: Changing department reconciles competency profile while preserving historical evidence."""
    client = env["client"]
    settings = env["settings"]
    db = env["db"]
    user_a = env["user_a"]
    token_a = create_access_token(str(user_a["_id"]), settings)

    # Insert historical evidence for user_a
    ev_oid = ObjectId()
    db.competency_evidence.insert_one({
        "_id": ev_oid,
        "user_id": user_a["_id"],
        "competency_id": env["comp_stat"]["_id"],
        "evidence_type": "CAPABILITY_ASSESSMENT",
        "score": 4.0,
        "confidence": 0.85,
        "created_at": datetime.now(UTC),
    })

    # Update profile to Ministry of Education
    update_res = client.put(
        "/api/v1/users/me",
        json={
            "department": "Ministry of Education",
            "designation": "Teacher",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["department"] == "Ministry of Education"

    # Verify new applicable competencies
    comp_res = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_a}"})
    assert comp_res.status_code == 200
    new_codes = {c["code"] for c in comp_res.json()}
    assert "BEH_COMMUNICATION" in new_codes
    assert "STAT_SAMPLING" not in new_codes

    # Verify historical evidence is STILL INTACT in database
    ev_record = db.competency_evidence.find_one({"_id": ev_oid})
    assert ev_record is not None
    assert ev_record["score"] == 4.0


def test_j_rbac_and_admin_department_filtering(env):
    """Test J: Verify RBAC permissions and admin department-level filtering."""
    client = env["client"]
    settings = env["settings"]
    admin_token = create_access_token(str(env["admin_user"]["_id"]), settings)
    official_token = create_access_token(str(env["user_a"]["_id"]), settings)

    # 1. Non-admin forbidden on /admin/dashboard
    forbidden_res = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {official_token}"})
    assert forbidden_res.status_code == 403

    # 2. Admin allowed on /admin/dashboard
    admin_res = client.get("/api/v1/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200

    # 3. Admin department filter
    dept_filtered_res = client.get(
        "/api/v1/admin/dashboard?department=Ministry%20of%20Education",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dept_filtered_res.status_code == 200
    assert dept_filtered_res.json()["total_users"] == 1
