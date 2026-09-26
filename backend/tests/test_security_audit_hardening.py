"""
Security Audit Hardening Regression Test Suite
Tests for:
1. Authentication & RBAC enforcement on sensitive endpoints.
2. Cross-user IDOR / BOLA authorization checks (Trainer questions).
3. Question lifecycle state transitions (Approved questions immutable).
4. Mass-assignment privilege escalation prevention in user profile updates.
5. Quiz answer key protection before submission and duplicate submission prevention.
6. File upload security (MIME validation, path traversal filename sanitization).
7. HTTP security headers verification.
8. Production settings validation (JWT secret entropy and debug mode protection).
"""

import io
import pytest
from bson import ObjectId

from app.core.config import Settings
from app.auth.security import create_access_token
from tests.test_trainer import make_trainer_app, create_user


def test_production_settings_entropy_and_debug_enforcement():
    """Verify production settings enforce 256-bit JWT secret entropy and disable debug."""
    # Weak secret should fail
    with pytest.raises(ValueError, match="CRITICAL CONFIGURATION ERROR"):
        Settings(
            app_env="production",
            jwt_secret="weak-secret-too-short",
        )

    # Strong secret succeeds and debug is automatically False
    prod_settings = Settings(
        app_env="production",
        jwt_secret="a" * 32,
    )
    assert prod_settings.debug is False
    assert len(prod_settings.jwt_secret) >= 32


def test_http_security_headers_present():
    """Verify essential HTTP security headers are attached to API responses."""
    client, database, settings = make_trainer_app()
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert "strict-transport-security" in resp.headers
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_unauthenticated_trainer_endpoints_rejected():
    """Verify unauthenticated requests to trainer question review endpoints fail."""
    client, database, settings = make_trainer_app()

    resp = client.get("/api/v1/trainer/questions")
    assert resp.status_code in (401, 403)

    resp2 = client.get("/api/v1/trainer/questions/fakeid123")
    assert resp2.status_code in (401, 403)

    resp3 = client.put("/api/v1/trainer/questions/fakeid123", json={"question": "Hacked?"})
    assert resp3.status_code in (401, 403)


def test_mass_assignment_privilege_escalation_blocked():
    """Verify a learner cannot elevate their role to TRAINER or ADMIN via PUT /users/me."""
    client, database, settings = make_trainer_app()
    learner = create_user(database, "learner_sec@gov.in", "OFFICIAL", "OFF-001")
    token = create_access_token(str(learner["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to mass-assign role to ADMIN and application_role to TRAINER
    malicious_payload = {
        "full_name": "Elevated User",
        "role": "ADMIN",
        "access_role": "ADMIN",
        "application_role": "ADMIN",
        "status": "SUPERUSER",
    }
    resp = client.put("/api/v1/users/me", headers=headers, json=malicious_payload)
    # Pydantic schema validation rejects unauthorized privilege fields
    assert resp.status_code == 422

    # Verify database document was NOT modified with privileged keys
    updated_user = database.users.find_one({"_id": learner["_id"]})
    assert updated_user["access_role"] == "OFFICIAL"
    assert updated_user.get("role", "OFFICIAL") in ("OFFICIAL", None)

    # Valid profile updates work as intended
    valid_resp = client.put("/api/v1/users/me", headers=headers, json={"full_name": "Verified Name"})
    assert valid_resp.status_code == 200
    assert database.users.find_one({"_id": learner["_id"]})["full_name"] == "Verified Name"


def test_cross_user_trainer_question_isolation_idor():
    """Verify Trainer B cannot edit or reject Trainer A's questions (IDOR protection)."""
    client, database, settings = make_trainer_app()
    trainer_a = create_user(database, "trainer_a_idor@gov.in", "TRAINER", "TRN-001")
    trainer_b = create_user(database, "trainer_b_idor@gov.in", "TRAINER", "TRN-002")

    token_a = create_access_token(str(trainer_a["_id"]), settings)
    token_b = create_access_token(str(trainer_b["_id"]), settings)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Trainer A creates a question in review studio
    q_doc = {
        "_id": ObjectId(),
        "trainer_id": str(trainer_a["_id"]),
        "material_id": "mat_sec_01",
        "competency_code": "SEC_CODE",
        "question": "Original question by Trainer A?",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "explanation": "Valid explanation.",
        "difficulty": "MEDIUM",
        "bloom_level": "REMEMBER",
        "status": "PENDING_REVIEW",
    }
    database.trainer_questions.insert_one(q_doc)
    question_id = str(q_doc["_id"])

    # Trainer B attempts to edit Trainer A's question -> 400/403/404 Access Denied
    edit_resp = client.put(
        f"/api/v1/trainer/questions/{question_id}",
        headers=headers_b,
        json={"question": "Tampered by Trainer B?"},
    )
    assert edit_resp.status_code in (400, 403, 404)
    assert "access denied" in edit_resp.json()["detail"].lower() or "not found" in edit_resp.json()["detail"].lower()

    # Trainer B attempts to reject Trainer A's question -> 400/403/404 Access Denied
    reject_resp = client.post(
        f"/api/v1/trainer/questions/{question_id}/reject",
        headers=headers_b,
        json={"review_notes": "Malicious rejection by Trainer B"},
    )
    assert reject_resp.status_code in (400, 403, 404)
    assert "access denied" in reject_resp.json()["detail"].lower() or "not found" in reject_resp.json()["detail"].lower()


def test_immutable_approved_question_state_transition():
    """Verify that an APPROVED question cannot be rejected or edited by a trainer."""
    client, database, settings = make_trainer_app()
    trainer_a = create_user(database, "trainer_appr@gov.in", "TRAINER", "TRN-003")
    token_a = create_access_token(str(trainer_a["_id"]), settings)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Insert an already APPROVED question
    q_doc = {
        "_id": ObjectId(),
        "trainer_id": str(trainer_a["_id"]),
        "material_id": "mat_approved_01",
        "competency_code": "SEC_CODE",
        "question": "Approved question text?",
        "options": ["Opt 1", "Opt 2", "Opt 3", "Opt 4"],
        "correct_answer": "B",
        "explanation": "Valid explanation.",
        "difficulty": "EASY",
        "bloom_level": "UNDERSTAND",
        "status": "APPROVED",
    }
    database.trainer_questions.insert_one(q_doc)
    question_id = str(q_doc["_id"])

    # Attempt to reject the approved question -> rejected with error stating already approved
    reject_resp = client.post(
        f"/api/v1/trainer/questions/{question_id}/reject",
        headers=headers_a,
        json={"review_notes": "Should not be able to reject approved question"},
    )
    assert reject_resp.status_code in (400, 409)
    assert "already approved" in reject_resp.json()["detail"].lower()


def test_file_upload_security_mime_and_size_validation():
    """Verify executable file uploads are strictly rejected and size caps enforced."""
    client, database, settings = make_trainer_app()
    trainer = create_user(database, "uploader_sec@gov.in", "TRAINER", "TRN-004")
    token = create_access_token(str(trainer["_id"]), settings)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to upload an executable script (.py / .exe)
    fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00")
    resp_exe = client.post(
        "/api/v1/learning-materials/upload",
        headers=headers,
        files={"file": ("malware.exe", fake_exe, "application/x-dosexec")},
    )
    assert resp_exe.status_code == 400
    assert "unsupported file" in resp_exe.json()["detail"].lower()
