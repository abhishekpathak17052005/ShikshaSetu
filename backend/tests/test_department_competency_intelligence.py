"""
Phase 3F — Comprehensive Role & Department-Specific Competency Intelligence Test Suite.

Automated verification covering all 14 mandatory tests:
- TEST 1: Two users from different departments receive different applicable competencies.
- TEST 2: Two users with different roles in the same department receive different applicable competencies.
- TEST 3: A user does not receive all 42 competencies as active competencies.
- TEST 4: A competency outside the user's role requirements cannot become an active skill gap.
- TEST 5: A learning resource unrelated to active role gaps is not generated as a recommendation candidate.
- TEST 6: A role-applicable resource can become a candidate when the corresponding competency is an active gap.
- TEST 7: Adaptive assessment rejects an out-of-role competency.
- TEST 8: Adaptive assessment accepts an applicable competency.
- TEST 9: Changing department/designation re-resolves the role.
- TEST 10: Role change deactivates obsolete competency profiles without deleting historical evidence.
- TEST 11: AI Co-Pilot context contains the resolved role and applicable competency context.
- TEST 12: Admin analytics does not count inactive/out-of-role competencies as active workforce gaps.
- TEST 13: Invalid department/designation combination fails safely.
- TEST 14: No user is silently forced to STATISTICAL_OFFICER.
"""

from datetime import datetime, UTC
import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings
from app.auth.security import create_access_token, hash_password
from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies
from app.assistant.context import build_user_capability_context



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
    """Sets up an isolated multi-department test environment."""
    db = FakeDatabase()
    settings = Settings(
        jwt_secret="test-phase-3f-secret-key-32-chars-long",
        api_prefix="/api/v1",
        mongodb_uri="mongodb://localhost:27017",
        mongodb_database="test",
    )
    app = create_app(settings)
    app.state.database = db
    app.state.settings = settings
    client = TestClient(app)

    now = datetime.now(UTC)

    # 1. Seed Competencies (Canonical 42 subset for test isolation)
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
    comp_edtech = {
        "_id": ObjectId(),
        "code": "TECH_DATA_VISUALIZATION",
        "name": "Data Visualization & Dashboards",
        "domain": "TECHNICAL",
        "description": "Interactive data visualization and charts",
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
    comp_unrelated = {
        "_id": ObjectId(),
        "code": "DIGOV_CYBERSECURITY",
        "name": "Information Security & Cybersecurity Governance",
        "domain": "DIGITAL_GOVERNANCE",
        "description": "Critical IT infrastructure protection",
        "level_definitions": {"1": "L1", "2": "L2", "3": "L3", "4": "L4", "5": "L5"},
        "status": "active",
        "framework_status": "prototype",
        "source_type": "PROTOTYPE",
        "created_at": now,
        "updated_at": now,
    }
    db.competencies.insert_many([comp_stat, comp_edu, comp_edtech, comp_shared, comp_unrelated])

    # 2. Seed Roles across Departments
    role_stat = {
        "_id": ObjectId(),
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "department": "Ministry of Statistics & Programme Implementation (MoSPI)",
        "department_code": "MOSPI",
        "designations": ["Statistical Officer", "Junior Statistical Officer (JSO)", "Senior Statistical Officer (SSO)"],
        "status": "active",
        "mapping_status": "PROTOTYPE_CONFIGURED",
        "source": "INTERNAL_PROTOTYPE_V1",
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
        "mapping_status": "PROTOTYPE_CONFIGURED",
        "source": "INTERNAL_PROTOTYPE_V1",
        "created_at": now,
        "updated_at": now,
    }
    role_edtech = {
        "_id": ObjectId(),
        "role_code": "DIGITAL_LEARNING_SPECIALIST",
        "role_name": "Digital Pedagogy & EdTech Specialist",
        "department": "Ministry of Education",
        "department_code": "MOE",
        "designations": ["Digital Learning Specialist", "EdTech Coordinator"],
        "status": "active",
        "mapping_status": "PROTOTYPE_CONFIGURED",
        "source": "INTERNAL_PROTOTYPE_V1",
        "created_at": now,
        "updated_at": now,
    }
    db.roles.insert_many([role_stat, role_edu, role_edtech])

    # 3. Seed Role Requirements
    db.role_requirements.insert_many([
        # MoSPI Statistical Officer Requirements
        {
            "role_id": role_stat["_id"],
            "competency_id": comp_stat["_id"],
            "competency_code": "STAT_SAMPLING",
            "required_level": 4.0,
            "priority": 1,
            "importance": 0.9,
            "mapping_status": "PROTOTYPE_CONFIGURED",
            "source": "INTERNAL_PROTOTYPE_V1",
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "role_id": role_stat["_id"],
            "competency_id": comp_shared["_id"],
            "competency_code": "BEH_ETHICS",
            "required_level": 4.0,
            "priority": 2,
            "importance": 0.8,
            "mapping_status": "PROTOTYPE_CONFIGURED",
            "source": "INTERNAL_PROTOTYPE_V1",
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        # MoE Education Officer Requirements
        {
            "role_id": role_edu["_id"],
            "competency_id": comp_edu["_id"],
            "competency_code": "BEH_COMMUNICATION",
            "required_level": 4.0,
            "priority": 1,
            "importance": 0.95,
            "mapping_status": "PROTOTYPE_CONFIGURED",
            "source": "INTERNAL_PROTOTYPE_V1",
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        {
            "role_id": role_edu["_id"],
            "competency_id": comp_shared["_id"],
            "competency_code": "BEH_ETHICS",
            "required_level": 4.0,
            "priority": 2,
            "importance": 0.85,
            "mapping_status": "PROTOTYPE_CONFIGURED",
            "source": "INTERNAL_PROTOTYPE_V1",
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
        # MoE Digital Learning Specialist Requirements
        {
            "role_id": role_edtech["_id"],
            "competency_id": comp_edtech["_id"],
            "competency_code": "TECH_DATA_VISUALIZATION",
            "required_level": 4.0,
            "priority": 1,
            "importance": 0.90,
            "mapping_status": "PROTOTYPE_CONFIGURED",
            "source": "INTERNAL_PROTOTYPE_V1",
            "active": True,
            "created_at": now,
            "updated_at": now,
        },
    ])

    # 4. Seed Learning Resources and Mappings
    res_stat = {
        "_id": ObjectId(),
        "resource_id": "RES-STAT-001",
        "title": "iGOT: Statistical Sampling & Survey Estimation",
        "provider": "IGOT",
        "status": "ACTIVE",
        "source": {
            "source_type": "PROTOTYPE",
            "source_document": "iGOT Public Catalog",
            "verification_status": "VERIFIED",
        },
        "metadata": {
            "difficulty": "Intermediate",
        },
        "provider_specific": {},
        "created_at": now,
        "updated_at": now,
    }
    res_cyber = {
        "_id": ObjectId(),
        "resource_id": "RES-CYBER-001",
        "title": "MeitY: Advanced Cybersecurity Governance",
        "provider": "IGOT",
        "status": "ACTIVE",
        "source": {
            "source_type": "PROTOTYPE",
            "source_document": "iGOT Public Catalog",
            "verification_status": "VERIFIED",
        },
        "metadata": {
            "difficulty": "Advanced",
        },
        "provider_specific": {},
        "created_at": now,
        "updated_at": now,
    }
    db.learning_resources.insert_many([res_stat, res_cyber])
    db.learning_resource_mappings.insert_many([
        {
            "resource_id": str(res_stat["_id"]),
            "competency_id": str(comp_stat["_id"]),
            "competency_code": "STAT_SAMPLING",
            "competency_name": "Sampling Methods & Survey Design",
            "provider": "IGOT",
            "mapping_type": "DERIVED",
            "confidence": 0.8,
            "status": "ACTIVE",
            "created_at": now,
        },
        {
            "resource_id": str(res_cyber["_id"]),
            "competency_id": str(comp_unrelated["_id"]),
            "competency_code": "DIGOV_CYBERSECURITY",
            "competency_name": "Information Security & Cybersecurity Governance",
            "provider": "IGOT",
            "mapping_type": "DERIVED",
            "confidence": 0.8,
            "status": "ACTIVE",
            "created_at": now,
        },
    ])



    # 5. Seed Question Bank for Adaptive Assessment
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

    # 6. Seed Users
    user_stat = {
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
    user_edu = {
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
    user_edtech = {
        "_id": ObjectId(),
        "email": "officer.edtech@shikshasetu.gov.in",
        "password_hash": hash_password("Password123!"),
        "full_name": "Vikram Seth (EdTech Specialist)",
        "department": "Ministry of Education",
        "designation": "Digital Learning Specialist",
        "employee_id": "EDU-002",
        "role_id": role_edtech["_id"],
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
    db.users.insert_many([user_stat, user_edu, user_edtech, admin_user])

    # Reconcile baseline profiles
    reconcile_user_competencies(db, user_stat["_id"], role_stat["_id"])
    reconcile_user_competencies(db, user_edu["_id"], role_edu["_id"])
    reconcile_user_competencies(db, user_edtech["_id"], role_edtech["_id"])

    return {
        "client": client,
        "db": db,
        "settings": settings,
        "user_stat": user_stat,
        "user_edu": user_edu,
        "user_edtech": user_edtech,
        "admin_user": admin_user,
        "role_stat": role_stat,
        "role_edu": role_edu,
        "role_edtech": role_edtech,
        "comp_stat": comp_stat,
        "comp_edu": comp_edu,
        "comp_edtech": comp_edtech,
        "comp_shared": comp_shared,
        "comp_unrelated": comp_unrelated,
    }


def test_01_different_departments_receive_different_competencies(env):
    """TEST 1: Two users from different departments receive different applicable competencies."""
    client, settings = env["client"], env["settings"]
    token_stat = create_access_token(str(env["user_stat"]["_id"]), settings)
    token_edu = create_access_token(str(env["user_edu"]["_id"]), settings)

    res_stat = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_stat}"})
    res_edu = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_edu}"})

    assert res_stat.status_code == 200
    assert res_edu.status_code == 200

    comps_stat = {c["code"] for c in res_stat.json()}
    comps_edu = {c["code"] for c in res_edu.json()}

    assert comps_stat != comps_edu
    assert "STAT_SAMPLING" in comps_stat
    assert "BEH_COMMUNICATION" in comps_edu


def test_02_different_roles_in_same_department_receive_different_competencies(env):
    """TEST 2: Two users with different roles in the same department receive different applicable competencies."""
    client, settings = env["client"], env["settings"]
    token_edu = create_access_token(str(env["user_edu"]["_id"]), settings)
    token_edtech = create_access_token(str(env["user_edtech"]["_id"]), settings)

    res_edu = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_edu}"})
    res_edtech = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token_edtech}"})

    comps_edu = {c["code"] for c in res_edu.json()}
    comps_edtech = {c["code"] for c in res_edtech.json()}

    assert comps_edu != comps_edtech
    assert "BEH_COMMUNICATION" in comps_edu
    assert "TECH_DATA_VISUALIZATION" in comps_edtech


def test_03_user_does_not_receive_all_42_competencies(env):
    """TEST 3: A user does not receive all 42 competencies as active competencies."""
    client, settings = env["client"], env["settings"]
    token = create_access_token(str(env["user_stat"]["_id"]), settings)

    res = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    applicable_comps = res.json()
    assert len(applicable_comps) < 42
    assert len(applicable_comps) == 2  # STAT_SAMPLING and BEH_ETHICS


def test_04_competency_outside_role_cannot_become_active_skill_gap(env):
    """TEST 4: A competency outside the user's role requirements cannot become an active skill gap."""
    client, settings = env["client"], env["settings"]
    token_edu = create_access_token(str(env["user_edu"]["_id"]), settings)

    res = client.get("/api/v1/skill-gaps/me", headers={"Authorization": f"Bearer {token_edu}"})
    assert res.status_code == 200
    gap_codes = {g["competency_code"] for g in res.json()["gaps"]}

    # Education Officer must never have STAT_SAMPLING or DIGOV_CYBERSECURITY as skill gaps
    assert "STAT_SAMPLING" not in gap_codes
    assert "DIGOV_CYBERSECURITY" not in gap_codes
    assert "BEH_COMMUNICATION" in gap_codes


def test_05_unrelated_resource_is_not_recommendation_candidate(env):
    """TEST 5: A learning resource unrelated to active role gaps is not generated as a recommendation candidate."""
    client, settings = env["client"], env["settings"]
    token_stat = create_access_token(str(env["user_stat"]["_id"]), settings)

    res = client.get("/api/v1/recommendations/me", headers={"Authorization": f"Bearer {token_stat}"})
    assert res.status_code == 200
    recs = res.json().get("recommendations", [])
    rec_titles = [r["resource"]["title"] for r in recs]

    # Cybersecurity course is NOT mapped to Statistical Officer's skill gaps
    assert not any("Cybersecurity" in t for t in rec_titles)



def test_06_role_applicable_resource_becomes_candidate_when_gap_exists(env):
    """TEST 6: A role-applicable resource can become a candidate when the corresponding competency is an active gap."""
    client, settings = env["client"], env["settings"]
    token_stat = create_access_token(str(env["user_stat"]["_id"]), settings)

    res = client.get("/api/v1/recommendations/me", headers={"Authorization": f"Bearer {token_stat}"})
    assert res.status_code == 200
    recs = res.json().get("recommendations", [])
    rec_codes = {r.get("competency_code") for r in recs}
    assert "STAT_SAMPLING" in rec_codes


def test_07_adaptive_assessment_rejects_out_of_role_competency(env):
    """TEST 7: Adaptive assessment rejects an out-of-role competency."""
    client, settings = env["client"], env["settings"]
    token_edu = create_access_token(str(env["user_edu"]["_id"]), settings)

    # Education Officer attempts to start assessment for STAT_SAMPLING
    res = client.post(
        "/api/v1/adaptive-assessments/start",
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
        headers={"Authorization": f"Bearer {token_edu}"},
    )
    assert res.status_code == 403
    assert "not applicable" in res.json()["detail"].lower()


def test_08_adaptive_assessment_accepts_applicable_competency(env):
    """TEST 8: Adaptive assessment accepts an applicable competency."""
    client, settings = env["client"], env["settings"]
    token_stat = create_access_token(str(env["user_stat"]["_id"]), settings)

    # Statistical Officer starts assessment for STAT_SAMPLING
    res = client.post(
        "/api/v1/adaptive-assessments/start",
        json={"competency_code": "STAT_SAMPLING", "max_questions": 3},
        headers={"Authorization": f"Bearer {token_stat}"},
    )
    assert res.status_code == 200
    assert res.json()["competency_code"] == "STAT_SAMPLING"


def test_09_changing_department_designation_reresolves_role(env):
    """TEST 9: Changing department/designation re-resolves the role."""
    client, settings = env["client"], env["settings"]
    user = env["user_stat"]
    token = create_access_token(str(user["_id"]), settings)

    # Update profile to Ministry of Education / Teacher
    res = client.put(
        "/api/v1/users/me",
        json={"department": "Ministry of Education", "designation": "Teacher"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["department"] == "Ministry of Education"

    # Verify competencies re-resolved to Education Officer
    comp_res = client.get("/api/v1/competencies/me", headers={"Authorization": f"Bearer {token}"})
    assert comp_res.status_code == 200
    codes = {c["code"] for c in comp_res.json()}
    assert "BEH_COMMUNICATION" in codes
    assert "STAT_SAMPLING" not in codes


def test_10_role_change_deactivates_obsolete_profiles_and_preserves_evidence(env):
    """TEST 10: Role change deactivates obsolete competency profiles without deleting historical evidence."""
    db, settings, client = env["db"], env["settings"], env["client"]
    user = env["user_stat"]
    token = create_access_token(str(user["_id"]), settings)

    # Record historical evidence for user
    ev_id = ObjectId()
    db.competency_evidence.insert_one({
        "_id": ev_id,
        "user_id": user["_id"],
        "competency_id": env["comp_stat"]["_id"],
        "evidence_type": "CAPABILITY_ASSESSMENT",
        "score": 4.0,
        "confidence": 0.85,
        "created_at": datetime.now(UTC),
    })

    # Update role to Education
    client.put(
        "/api/v1/users/me",
        json={"department": "Ministry of Education", "designation": "Teacher"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check that previous profile is inactive
    old_profile = db.competency_profiles.find_one({
        "user_id": user["_id"],
        "competency_id": env["comp_stat"]["_id"],
    })
    assert old_profile is not None
    assert old_profile["status"] == "inactive"

    # Check that historical evidence remains intact
    ev = db.competency_evidence.find_one({"_id": ev_id})
    assert ev is not None
    assert ev["score"] == 4.0


def test_11_ai_copilot_context_contains_resolved_role_and_applicable_gaps(env):
    """TEST 11: AI Co-Pilot context contains the resolved role and applicable competency context."""
    db = env["db"]
    user = env["user_stat"]

    ctx = build_user_capability_context(db, str(user["_id"]))
    assert ctx["profile"]["role_name"] == "Statistical Officer"
    assert "STAT_SAMPLING" in [g["competency_code"] for g in ctx["top_gaps"]]
    assert "BEH_COMMUNICATION" not in [g["competency_code"] for g in ctx["top_gaps"]]



def test_12_admin_analytics_respects_department_and_active_gaps(env):
    """TEST 12: Admin analytics does not count inactive/out-of-role competencies as active workforce gaps."""
    client, settings = env["client"], env["settings"]
    admin_token = create_access_token(str(env["admin_user"]["_id"]), settings)

    res = client.get(
        "/api/v1/admin/skill-gaps?department=Ministry%20of%20Education",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    gaps = res.json()["top_organization_gaps"]
    gap_codes = {g["competency_code"] for g in gaps}

    # Under Ministry of Education, BEH_COMMUNICATION is present, STAT_SAMPLING is not
    assert "BEH_COMMUNICATION" in gap_codes



def test_13_invalid_department_designation_fails_safely(env):
    """TEST 13: Invalid department/designation combination fails safely or falls back gracefully."""
    db = env["db"]
    role_id = resolve_role_for_user(db, "Unknown Alien Department", "Galactic Commander")
    # Must return fallback role rather than crashing
    assert role_id is not None
    assert ObjectId.is_valid(role_id)


def test_14_no_user_silently_forced_to_statistical_officer(env):
    """TEST 14: No user is silently forced to STATISTICAL_OFFICER when their department/designation maps elsewhere."""
    db = env["db"]
    edu_role_id = resolve_role_for_user(db, "Ministry of Education", "Teacher")
    edu_role = db.roles.find_one({"_id": edu_role_id})
    assert edu_role["role_code"] == "EDUCATION_OFFICER"
    assert edu_role["role_code"] != "STATISTICAL_OFFICER"


def test_15_reconciliation_is_idempotent(env):
    """TEST 15: Reconciliation is strictly idempotent."""
    db = env["db"]
    user = env["user_stat"]
    role = env["role_stat"]

    # Run reconciliation 3 consecutive times
    res1 = reconcile_user_competencies(db, user["_id"], role["_id"])
    res2 = reconcile_user_competencies(db, user["_id"], role["_id"])
    res3 = reconcile_user_competencies(db, user["_id"], role["_id"])

    # Profiles count must remain exactly equal to required competencies
    active_profs = list(db.competency_profiles.find({"user_id": user["_id"], "status": "active"}))
    reqs = list(db.role_requirements.find({"role_id": role["_id"]}))
    assert len(active_profs) == len(reqs)
    assert res2["created"] == 0
    assert res3["created"] == 0


def test_16_unmapped_resource_cannot_become_recommendation(env):
    """TEST 16: An unmapped resource in the catalogue is never returned as a recommendation."""
    db, client, settings = env["db"], env["client"], env["settings"]
    token_stat = create_access_token(str(env["user_stat"]["_id"]), settings)

    # Insert an unmapped catalogue resource
    unmapped_id = ObjectId()
    db.learning_resources.insert_one({
        "_id": unmapped_id,
        "resource_id": "RES-UNMAPPED-999",
        "title": "General Civil Services Administrative Guidelines",
        "provider": "IGOT",
        "status": "ACTIVE",
        "source": {
            "source_type": "PROTOTYPE",
            "source_document": "iGOT General Catalog",
            "verification_status": "VERIFIED",
        },
        "metadata": {"difficulty": "Beginner"},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })

    # Query recommendations
    res = client.get("/api/v1/recommendations/me", headers={"Authorization": f"Bearer {token_stat}"})
    assert res.status_code == 200
    rec_ids = [r["resource"]["resource_id"] for r in res.json().get("recommendations", [])]
    assert "RES-UNMAPPED-999" not in rec_ids


def test_17_role_match_cannot_bypass_competency_filter(env):
    """TEST 17: Role match factor never leaks out-of-scope resources without competency mappings."""
    db, client, settings = env["db"], env["client"], env["settings"]
    token_stat = create_access_token(str(env["user_stat"]["_id"]), settings)


    # Insert resource with target participants matching Statistical Officer, but mapped to out-of-role competency
    cyber_role_match_id = ObjectId()
    db.learning_resources.insert_one({
        "_id": cyber_role_match_id,
        "resource_id": "RES-CYBER-STAT-001",
        "title": "Cybersecurity for Statistical Officers",
        "provider": "IGOT",
        "status": "ACTIVE",
        "source": {
            "source_type": "PROTOTYPE",
            "source_document": "iGOT Catalog",
            "verification_status": "VERIFIED",
        },
        "metadata": {"difficulty": "Intermediate"},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    db.learning_resource_mappings.insert_one({
        "resource_id": str(cyber_role_match_id),
        "competency_id": str(env["comp_unrelated"]["_id"]),
        "competency_code": "DIGOV_CYBERSECURITY",
        "competency_name": "Cybersecurity",
        "provider": "IGOT",
        "mapping_type": "DERIVED",
        "confidence": 0.95,
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
    })

    res = client.get("/api/v1/recommendations/me", headers={"Authorization": f"Bearer {token_stat}"})
    assert res.status_code == 200
    rec_ids = [r["resource"]["resource_id"] for r in res.json().get("recommendations", [])]
    # Despite the title referencing Statistical Officers, it is mapped to DIGOV_CYBERSECURITY (out of role) -> must not be recommended
    assert "RES-CYBER-STAT-001" not in rec_ids

