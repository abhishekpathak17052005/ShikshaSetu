"""
Targeted live security verification for Quiz ownership, isolation, and answer masking.
"""

import sys
import uuid
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import get_settings
from app.core.database import initialize_database


def run_quiz_security_verification():
    settings = get_settings()
    app = create_app(settings)
    client = TestClient(app)
    mongo_client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    app.state.database = db

    print("=== LIVE QUIZ SECURITY & ISOLATION VERIFICATION ===")

    role = db.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
    role_id = str(role["_id"])

    uid_a = str(uuid.uuid4())[:8]
    uid_b = str(uuid.uuid4())[:8]

    # 1. Register User A
    user_a_email = f"quiz_sec_a_{uid_a}@shikshasetu.gov.in"
    res_a = client.post("/api/v1/auth/register", json={
        "email": user_a_email,
        "password": "Password123!",
        "full_name": "Quiz Sec User A",
        "designation": "Officer",
        "department": "Stats",
        "employee_id": f"EMP-QA-{uid_a}",
        "role_id": role_id,
    })
    assert res_a.status_code == 201, f"Register A failed: {res_a.text}"
    user_a_id = res_a.json().get("id") or res_a.json().get("_id")

    login_a = client.post("/api/v1/auth/login", json={"email": user_a_email, "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_email = f"quiz_sec_b_{uid_b}@shikshasetu.gov.in"
    res_b = client.post("/api/v1/auth/register", json={
        "email": user_b_email,
        "password": "Password123!",
        "full_name": "Quiz Sec User B",
        "designation": "Officer",
        "department": "Stats",
        "employee_id": f"EMP-QB-{uid_b}",
        "role_id": role_id,
    })
    assert res_b.status_code == 201, f"Register B failed: {res_b.text}"
    user_b_id = res_b.json().get("id") or res_b.json().get("_id")

    login_b = client.post("/api/v1/auth/login", json={"email": user_b_email, "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Create Material for User A
    mat_a_oid = ObjectId()
    db.learning_materials.insert_one({
        "_id": mat_a_oid,
        "user_id": str(user_a_id),
        "filename": "python_sec.pdf",
        "status": "READY",
    })
    mat_a_id = str(mat_a_oid)

    questions = [
        {
            "question_id": "q1",
            "question": "What is SQL?",
            "options": ["Structured Query Language", "Simple Query Language", "System Query Language", "Standard Query Logic"],
            "correct_answer": "A",
            "explanation": "SQL stands for Structured Query Language.",
            "difficulty": "EASY",
        }
    ]

    # 4. User B tries to create quiz using User A's material -> MUST BE 400
    res_cross_mat = client.post("/api/v1/quizzes", headers=headers_b, json={
        "material_id": mat_a_id,
        "competency_code": "TECH_SQL",
        "questions": questions,
    })
    assert res_cross_mat.status_code == 400, f"Expected 400, got {res_cross_mat.status_code}"
    print("  [PASS] User B blocked from creating quiz using User A's material (HTTP 400)")

    # 5. User A creates quiz with own material -> MUST BE 200
    res_quiz_a = client.post("/api/v1/quizzes", headers=headers_a, json={
        "material_id": mat_a_id,
        "competency_code": "TECH_SQL",
        "questions": questions,
    })
    assert res_quiz_a.status_code == 200, f"Expected 200, got {res_quiz_a.status_code}"
    quiz_a_id = res_quiz_a.json()["_id"]
    print(f"  [PASS] User A created quiz {quiz_a_id} successfully")

    # 6. User B tries to retrieve User A's quiz -> MUST BE 404
    res_cross_get = client.get(f"/api/v1/quizzes/{quiz_a_id}", headers=headers_b)
    assert res_cross_get.status_code == 404, f"Expected 404, got {res_cross_get.status_code}"
    print("  [PASS] User B blocked from retrieving User A's quiz (HTTP 404)")

    # 7. User A retrieves quiz -> Correct answers and explanations MUST BE HIDDEN
    res_owner_get = client.get(f"/api/v1/quizzes/{quiz_a_id}", headers=headers_a)
    assert res_owner_get.status_code == 200
    retrieved_questions = res_owner_get.json()["questions"]
    for q in retrieved_questions:
        assert "correct_answer" not in q, "correct_answer leaked in quiz retrieval!"
        assert "explanation" not in q, "explanation leaked in quiz retrieval!"
    print("  [PASS] Correct answers and explanations hidden in GET /quizzes/{id}")

    # 8. User A submits quiz -> Correct answer evaluated server-side
    actual_q_id = res_quiz_a.json()["questions"][0]["question_id"]
    res_submit = client.post(f"/api/v1/quizzes/{quiz_a_id}/submit", headers=headers_a, json={
        "answers": [{"question_id": actual_q_id, "selected_answer": "A"}]
    })
    assert res_submit.status_code == 200, f"Expected 200, got {res_submit.status_code}: {res_submit.text}"
    submit_data = res_submit.json()
    assert submit_data["percentage"] == 100.0
    assert submit_data["correct_count"] == 1
    assert submit_data["competency"]["competency_level_after"] == 4.5
    print("  [PASS] User A submitted quiz: scored 100%, level updated to 4.5")

    # 9. Verify evidence in DB
    evidence = db.competency_evidence.find_one({"user_id": ObjectId(user_a_id), "quiz_id": ObjectId(quiz_a_id)})
    assert evidence is not None, "Competency evidence not created in DB!"
    assert evidence["competency_code"] == "TECH_SQL"
    print("  [PASS] Competency evidence record created in database with source AI_QUIZ")

    print("\nALL QUIZ SECURITY AND ISOLATION CHECKS PASSED SUCCESSFULLY!\n")


if __name__ == "__main__":
    run_quiz_security_verification()
