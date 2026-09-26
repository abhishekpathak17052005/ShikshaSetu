"""
Critical P0 Regression Tests for Question Review: Edit and Reject End-to-End.

Covers:
- Edit question end-to-end (stem, options, correct_answer, bloom, difficulty)
- Same question ID preserved
- Provenance preserved (source_document_id, source_chunks, created_at)
- Reject question end-to-end (status: REJECTED, review_notes stored)
- Database persistence and refresh verification
- Cross-trainer isolation & RBAC authorization
- Admin authorization to review questions across trainers
- Schema validation (empty stem, option count != 4, duplicates)
- Graceful handling of legacy questions with None bloom_level or missing fields
"""

from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.auth.security import create_access_token
from app.trainer.models import QuestionReviewStatus, TrainerQuestion
from tests.test_trainer import make_trainer_app, create_user, create_material


def test_edit_question_end_to_end_persists_same_id():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@shikshasetu.gov.in", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Cybersecurity_Guide.pdf")
    q_doc = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="SEC_CSRF",
        question="What is CSRF?",
        options=["Cross-Site Request Forgery", "Client Side Request Filter", "Cascading Style Reference File", "None of these"],
        correct_answer="A",
        explanation="CSRF stands for Cross-Site Request Forgery",
        difficulty="MEDIUM",
        bloom_level="UNDERSTAND",
        source_document_id=str(mat["_id"]),
        source_chunks=["chunk_001", "chunk_002"],
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_doc)
    original_qid = str(q_doc["_id"])
    original_created_at = q_doc["created_at"]

    # Perform Edit
    edit_payload = {
        "question": "Which mechanism helps prevent Cross-Site Request Forgery (CSRF) attacks?",
        "options": [
            "Anti-CSRF synchronizer tokens and SameSite cookie attribute",
            "Disabling HTTPS encryption",
            "Storing credentials in URL query strings",
            "Increasing session timeout to unlimited"
        ],
        "correct_answer": "A",
        "explanation": "CSRF tokens and SameSite cookies prevent unauthorized cross-site requests.",
        "bloom_level": "APPLY",
        "difficulty": "HARD",
        "competency_code": "SEC_CSRF_ADVANCED"
    }

    resp = client.put(f"/api/v1/trainer/questions/{original_qid}", headers=headers, json=edit_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # 1. Verify response properties
    assert data["id"] == original_qid
    assert data["question"] == edit_payload["question"]
    assert data["options"] == edit_payload["options"]
    assert data["correct_answer"] == "A"
    assert data["explanation"] == edit_payload["explanation"]
    assert data["bloom_level"] == "APPLY"
    assert data["difficulty"] == "HARD"
    assert data["competency_code"] == "SEC_CSRF_ADVANCED"
    assert data["status"] == "EDITED"
    assert data["source_document_id"] == str(mat["_id"])
    assert data["source_chunks"] == ["chunk_001", "chunk_002"]

    # 2. Verify direct database record
    db_record = database.trainer_questions.find_one({"_id": ObjectId(original_qid)})
    assert db_record is not None
    assert str(db_record["_id"]) == original_qid
    assert db_record["question"] == edit_payload["question"]
    assert db_record["options"] == edit_payload["options"]
    assert db_record["status"] == "EDITED"
    assert db_record["bloom_level"] == "APPLY"
    assert db_record["difficulty"] == "HARD"
    # Provenance preserved
    assert db_record["source_document_id"] == str(mat["_id"])
    assert db_record["source_chunks"] == ["chunk_001", "chunk_002"]
    assert db_record["created_at"] == original_created_at

    # 3. Simulate page refresh by fetching question list
    refresh_resp = client.get("/api/v1/trainer/questions", headers=headers)
    assert refresh_resp.status_code == 200
    refreshed_list = refresh_resp.json()
    matched = [q for q in refreshed_list if q["id"] == original_qid]
    assert len(matched) == 1
    assert matched[0]["question"] == edit_payload["question"]
    assert matched[0]["status"] == "EDITED"

    client.close()


def test_reject_question_end_to_end_persists_same_id():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@shikshasetu.gov.in", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Sample.pdf")
    q_doc = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="STAT_SAMPLING",
        question="Ambiguous question to reject?",
        options=["Opt 1", "Opt 2", "Opt 3", "Opt 4"],
        correct_answer="B",
        explanation="Ambiguous context",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_doc)
    original_qid = str(q_doc["_id"])

    # Perform Reject
    reject_payload = {
        "action": "REJECT",
        "review_notes": "Question is ambiguous and not fully grounded in the provided curriculum chapter."
    }
    resp = client.post(f"/api/v1/trainer/questions/{original_qid}/reject", headers=headers, json=reject_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["id"] == original_qid
    assert data["status"] == "REJECTED"
    assert data["review_notes"] == reject_payload["review_notes"]

    # Verify DB update
    db_record = database.trainer_questions.find_one({"_id": ObjectId(original_qid)})
    assert db_record is not None
    assert str(db_record["_id"]) == original_qid
    assert db_record["status"] == "REJECTED"
    assert db_record["review_notes"] == reject_payload["review_notes"]

    # Verify status remains REJECTED on refresh
    refresh_resp = client.get(f"/api/v1/trainer/questions?status=REJECTED", headers=headers)
    assert refresh_resp.status_code == 200
    matched = [q for q in refresh_resp.json() if q["id"] == original_qid]
    assert len(matched) == 1
    assert matched[0]["status"] == "REJECTED"
    assert matched[0]["review_notes"] == reject_payload["review_notes"]

    client.close()


def test_edit_validation_rejects_corrupted_structure():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@shikshasetu.gov.in", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "Doc.pdf")
    q_doc = TrainerQuestion.create(
        trainer_id=str(trainer["_id"]),
        material_id=str(mat["_id"]),
        competency_code="COMP_TEST",
        question="Initial stem?",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Initial explanation",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_doc)
    qid = str(q_doc["_id"])

    # Empty question stem
    r1 = client.put(f"/api/v1/trainer/questions/{qid}", headers=headers, json={"question": "   "})
    assert r1.status_code in (400, 422)

    # Options count not 4
    r2 = client.put(f"/api/v1/trainer/questions/{qid}", headers=headers, json={"options": ["A", "B"]})
    assert r2.status_code in (400, 422)

    # Options with duplicates
    r3 = client.put(f"/api/v1/trainer/questions/{qid}", headers=headers, json={"options": ["Dup", "Dup", "C", "D"]})
    assert r3.status_code in (400, 422)

    # Invalid correct answer key
    r4 = client.put(f"/api/v1/trainer/questions/{qid}", headers=headers, json={"correct_answer": "Z"})
    assert r4.status_code in (400, 422)

    # Invalid bloom level
    r5 = client.put(f"/api/v1/trainer/questions/{qid}", headers=headers, json={"bloom_level": "INVALID_BLOOM"})
    assert r5.status_code in (400, 422)

    client.close()


def test_trainer_authorization_and_cross_tenant_isolation():
    client, database, settings = make_trainer_app()
    trainer_a = create_user(database, "trainerA@test.com", "TRAINER", "TRN-A")
    trainer_b = create_user(database, "trainerB@test.com", "TRAINER", "TRN-B")
    admin = create_user(database, "admin@shikshasetu.gov.in", "ADMIN", "ADM-001")

    token_a = create_access_token(str(trainer_a["_id"]), settings)
    token_b = create_access_token(str(trainer_b["_id"]), settings)
    token_admin = create_access_token(str(admin["_id"]), settings)

    mat = create_material(database, str(trainer_a["_id"]), "DocA.pdf")
    q_doc = TrainerQuestion.create(
        trainer_id=str(trainer_a["_id"]),
        material_id=str(mat["_id"]),
        competency_code="COMP_A",
        question="Question owned by Trainer A",
        options=["A", "B", "C", "D"],
        correct_answer="A",
        explanation="Trainer A explanation",
        status=QuestionReviewStatus.GENERATED,
    )
    database.trainer_questions.insert_one(q_doc)
    qid = str(q_doc["_id"])

    # Trainer B attempts to edit Trainer A's question -> Forbidden/Not found
    resp_b_edit = client.put(
        f"/api/v1/trainer/questions/{qid}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"question": "Hacked by Trainer B"}
    )
    assert resp_b_edit.status_code in (400, 403, 404)

    # Trainer B attempts to reject Trainer A's question -> Forbidden/Not found
    resp_b_reject = client.post(
        f"/api/v1/trainer/questions/{qid}/reject",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"action": "REJECT", "review_notes": "Rejected by Trainer B"}
    )
    assert resp_b_reject.status_code in (400, 403, 404)

    # Admin CAN edit Trainer A's question
    resp_admin_edit = client.put(
        f"/api/v1/trainer/questions/{qid}",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"question": "Admin verified and polished stem"}
    )
    assert resp_admin_edit.status_code == 200
    assert resp_admin_edit.json()["question"] == "Admin verified and polished stem"

    # Admin CAN reject Trainer A's question
    resp_admin_reject = client.post(
        f"/api/v1/trainer/questions/{qid}/reject",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={"action": "REJECT", "review_notes": "Admin rejection"}
    )
    assert resp_admin_reject.status_code == 200
    assert resp_admin_reject.json()["status"] == "REJECTED"

    client.close()


def test_legacy_questions_with_none_fields_dont_crash_response():
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "trainer@shikshasetu.gov.in", "TRAINER", "TRN-001")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    mat = create_material(database, str(trainer["_id"]), "OldDoc.pdf")

    # Manually insert legacy question with None bloom_level, None competency, etc.
    legacy_doc = {
        "_id": ObjectId(),
        "trainer_id": str(trainer["_id"]),
        "material_id": str(mat["_id"]),
        "competency_code": None,
        "question": "What is legacy sampling?",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "B",
        "explanation": None,
        "difficulty": None,
        "bloom_level": None,
        "source_document_id": None,
        "source_chunks": [],
        "grounding_score": None,
        "status": "GENERATED",
        "review_notes": None,
        "created_at": "2026-09-01T00:00:00",
        "updated_at": "2026-09-01T00:00:00",
    }
    database.trainer_questions.insert_one(legacy_doc)
    qid = str(legacy_doc["_id"])

    # 1. Fetching does not raise 500
    r_get = client.get(f"/api/v1/trainer/questions/{qid}", headers=headers)
    assert r_get.status_code == 200
    assert r_get.json()["bloom_level"] == "UNDERSTAND"
    assert r_get.json()["difficulty"] == "MEDIUM"

    # 2. Editing legacy question succeeds and upgrades fields
    r_edit = client.put(
        f"/api/v1/trainer/questions/{qid}",
        headers=headers,
        json={
            "question": "Updated legacy question?",
            "bloom_level": "ANALYZE",
            "difficulty": "HARD",
            "explanation": "Now explained properly"
        }
    )
    assert r_edit.status_code == 200
    assert r_edit.json()["bloom_level"] == "ANALYZE"
    assert r_edit.json()["difficulty"] == "HARD"

    # 3. Rejecting legacy question succeeds
    r_rej = client.post(
        f"/api/v1/trainer/questions/{qid}/reject",
        headers=headers,
        json={"action": "REJECT", "review_notes": "Outdated syllabus"}
    )
    assert r_rej.status_code == 200
    assert r_rej.json()["status"] == "REJECTED"

    client.close()
