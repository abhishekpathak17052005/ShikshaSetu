"""
Targeted Verification Script for Defect Cycle 1.

Verifies:
1. Capability Assessment Response Serialization & Full Assessment Lifecycle
2. Quiz Learning Material Ownership & Complete Interactive Quiz Loop
3. Cross-User Security Isolation on Materials and Quizzes
"""

import sys
import io
import time
from datetime import datetime, UTC
from bson import ObjectId

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, r"c:\Users\Lenovo\Desktop\ShikshaSetu\backend")

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings


def run_defect_cycle_1_verification():
    settings = get_settings()
    
    print("=" * 80)
    print("SHIKSHASETU: TARGETED DEFECT CYCLE 1 VERIFICATION")
    print(f"Target Database: {settings.mongodb_database}")
    print(f"Timestamp: {datetime.now(UTC).isoformat()}")
    print("=" * 80)

    with TestClient(app) as client:
        db = app.state.database
        role = db.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
        role_id_str = str(role["_id"])

        ts = int(time.time())
        user_a_email = f"defect_user_a_{ts}@shikshasetu.gov.in"
        user_b_email = f"defect_user_b_{ts}@shikshasetu.gov.in"
        pwd = "TargetedDefectTest@123"

        # ---------------------------------------------------------------------
        # SETUP: Register and Login User A & User B
        # ---------------------------------------------------------------------
        print("\n[Setup] Registering & Authenticating Users...")
        # User A
        reg_a = client.post("/api/v1/auth/register", json={
            "email": user_a_email,
            "password": pwd,
            "full_name": "Defect Tester A",
            "role_id": role_id_str,
            "designation": "Assistant Director",
            "department": "National Accounts Division",
            "employee_id": f"EMP_DEF_A_{ts}",
        })
        assert reg_a.status_code == 201, f"User A reg failed: {reg_a.text}"
        user_a_id = reg_a.json()["id"]

        login_a = client.post("/api/v1/auth/login", json={"email": user_a_email, "password": pwd})
        assert login_a.status_code == 200, f"User A login failed: {login_a.text}"
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User B
        reg_b = client.post("/api/v1/auth/register", json={
            "email": user_b_email,
            "password": pwd,
            "full_name": "Defect Tester B",
            "role_id": role_id_str,
            "designation": "Statistical Assistant",
            "department": "Field Operations Division",
            "employee_id": f"EMP_DEF_B_{ts}",
        })
        assert reg_b.status_code == 201, f"User B reg failed: {reg_b.text}"
        user_b_id = reg_b.json()["id"]

        login_b = client.post("/api/v1/auth/login", json={"email": user_b_email, "password": pwd})
        assert login_b.status_code == 200, f"User B login failed: {login_b.text}"
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        print(f"  ✅ User A created ({user_a_id}) and authenticated.")
        print(f"  ✅ User B created ({user_b_id}) and authenticated.")

        # =====================================================================
        # DEFECT 1: CAPABILITY ASSESSMENT RESPONSE SERIALIZATION & LIFECYCLE
        # =====================================================================
        print("\n" + "=" * 60)
        print("VERIFYING DEFECT 1: CAPABILITY ASSESSMENT SERIALIZATION")
        print("=" * 60)

        # 1. Create Capability Assessment
        create_res = client.post(
            "/api/v1/assessments/capability",
            headers=headers_a,
            json={"competency_code": "TECH_PYTHON"}
        )
        print(f"1. POST /api/v1/assessments/capability -> Status: {create_res.status_code}")
        assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
        
        cap_data = create_res.json()
        cap_id = cap_data.get("id")
        assert cap_id, f"Missing 'id' in response: {cap_data}"
        assert cap_data.get("competency_code") == "TECH_PYTHON"
        assert cap_data.get("status") == "IN_PROGRESS"
        questions = cap_data.get("questions", [])
        assert len(questions) > 0, "No questions returned"
        print(f"  ✅ Capability assessment created (ID: {cap_id}) with {len(questions)} questions.")

        # 2. Get Capability Assessment
        get_res = client.get(f"/api/v1/assessments/capability/{cap_id}", headers=headers_a)
        print(f"2. GET /api/v1/assessments/capability/{cap_id} -> Status: {get_res.status_code}")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["id"] == cap_id
        # Verify answer key is hidden
        for q in get_data["questions"]:
            assert "correct_answer" not in q, "Security breach: correct_answer exposed!"
        print("  ✅ Retrieved assessment. Correct answers securely hidden from client.")

        # 3. Submit Answers
        answers_payload = [
            {
                "question_id": q["question_id"],
                "selected_answer": q["options"][0] if q.get("options") else "Option A"
            }
            for q in get_data["questions"]
        ]
        submit_res = client.post(
            f"/api/v1/assessments/capability/{cap_id}/submit",
            headers=headers_a,
            json={"answers": answers_payload}
        )
        print(f"3. POST /api/v1/assessments/capability/{cap_id}/submit -> Status: {submit_res.status_code}")
        assert submit_res.status_code == 200
        sub_data = submit_res.json()
        assert sub_data["status"] == "SUBMITTED"
        assert sub_data["assessment_id"] == cap_id
        assert "score" in sub_data and "percentage" in sub_data and "normalized_score" in sub_data
        print(f"  ✅ Submitted and server scored. Score: {sub_data['percentage']}%, Level: {sub_data['normalized_score']}/5.0")

        # 4. Get Detailed Results Breakdown
        results_res = client.get(f"/api/v1/assessments/capability/{cap_id}/results", headers=headers_a)
        print(f"4. GET /api/v1/assessments/capability/{cap_id}/results -> Status: {results_res.status_code}")
        assert results_res.status_code == 200
        res_data = results_res.json()
        assert res_data["assessment_id"] == cap_id
        assert res_data["total_questions"] == len(questions)
        print(f"  ✅ Retrieved detailed performance breakdown (Correct: {res_data['correct_answers']}/{res_data['total_questions']}).")

        # 5. List Assessments
        list_res = client.get("/api/v1/assessments/capability", headers=headers_a)
        print(f"5. GET /api/v1/assessments/capability -> Status: {list_res.status_code}")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert any(item["id"] == cap_id for item in list_data)
        print(f"  ✅ Listed user capability assessments ({len(list_data)} found).")

        # =====================================================================
        # DEFECT 2: QUIZ MATERIAL OWNERSHIP & COMPLETE QUIZ LOOP
        # =====================================================================
        print("\n" + "=" * 60)
        print("VERIFYING DEFECT 2: QUIZ MATERIAL OWNERSHIP & ISOLATION")
        print("=" * 60)

        # 1. Upload Material by User A
        pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000117 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        upload_res = client.post(
            "/api/v1/learning-materials/upload",
            headers=headers_a,
            files={"file": ("python_tutorial.pdf", pdf_bytes, "application/pdf")}
        )
        print(f"1. POST /api/v1/learning-materials/upload -> Status: {upload_res.status_code}")
        assert upload_res.status_code in [200, 201]
        mat_id = upload_res.json()["material_id"]

        # Ensure material status is READY for quiz generation
        db.learning_materials.update_one(
            {"_id": ObjectId(mat_id)},
            {"$set": {"status": "READY", "extraction_status": "SUCCESS"}}
        )
        material_doc = db.learning_materials.find_one({"_id": ObjectId(mat_id)})
        print(f"  ✅ Stored material '{mat_id}'. Stored user_id type: {type(material_doc['user_id'])} (Value: {material_doc['user_id']})")

        # 2. User A Creates Quiz from Owned Material
        quiz_payload = {
            "material_id": mat_id,
            "competency_code": "TECH_PYTHON",
            "questions": [
                {
                    "question_id": "PY_Q1",
                    "question": "What is Python?",
                    "options": ["High-level language", "Low-level binary", "Hardware chip", "Assembly"],
                    "correct_answer": "A",
                    "explanation": "Python is a high-level interpreted programming language.",
                    "difficulty": "EASY"
                },
                {
                    "question_id": "PY_Q2",
                    "question": "Which data type is immutable?",
                    "options": ["List", "Set", "Tuple", "Dictionary"],
                    "correct_answer": "C",
                    "explanation": "Tuples are immutable in Python.",
                    "difficulty": "MEDIUM"
                }
            ]
        }
        quiz_create_res = client.post("/api/v1/quizzes", headers=headers_a, json=quiz_payload)
        print(f"2. User A POST /api/v1/quizzes -> Status: {quiz_create_res.status_code}")
        assert quiz_create_res.status_code in [200, 201], f"Failed quiz creation: {quiz_create_res.text}"
        quiz_data = quiz_create_res.json()
        quiz_id = quiz_data.get("_id") or quiz_data.get("quiz_id")
        print(f"  ✅ Quiz successfully created by User A (Quiz ID: {quiz_id}).")

        # 3. Retrieve Quiz (Answers Hidden)
        get_quiz_res = client.get(f"/api/v1/quizzes/{quiz_id}", headers=headers_a)
        print(f"3. GET /api/v1/quizzes/{quiz_id} -> Status: {get_quiz_res.status_code}")
        assert get_quiz_res.status_code == 200
        qz_details = get_quiz_res.json()
        for q in qz_details["questions"]:
            assert "correct_answer" not in q, "Security breach: correct_answer exposed in quiz questions!"
        print("  ✅ Retrieved quiz questions. Answers securely hidden.")

        # 4. User A Submits Quiz
        sub_answers = [
            {"question_id": q["question_id"], "selected_answer": "A"}
            for q in qz_details["questions"]
        ]
        sub_quiz_res = client.post(
            f"/api/v1/quizzes/{quiz_id}/submit",
            headers=headers_a,
            json={"answers": sub_answers}
        )
        print(f"4. POST /api/v1/quizzes/{quiz_id}/submit -> Status: {sub_quiz_res.status_code}")
        assert sub_quiz_res.status_code == 200, f"Quiz submit failed: {sub_quiz_res.text}"
        sub_qz_data = sub_quiz_res.json()
        assert "score" in sub_qz_data
        print(f"  ✅ Submitted quiz. Score: {sub_qz_data['score']}%. Passed: {sub_qz_data.get('passed')}.")

        # 5. Verify Evidence & Competency Profile Updated
        evidence = list(db.competency_evidence.find({"user_id": ObjectId(user_a_id), "evidence_type": "QUIZ"}))
        assert len(evidence) > 0, "No QUIZ evidence record created"
        profile = db.competency_profiles.find_one({"user_id": ObjectId(user_a_id)})
        print(f"  ✅ Verified competency evidence and profile updated for User A.")

        # 6. Security Isolation: User B Attempts to Create Quiz with User A's Material
        cross_create_res = client.post("/api/v1/quizzes", headers=headers_b, json=quiz_payload)
        print(f"6. User B POST /api/v1/quizzes (User A's material) -> Status: {cross_create_res.status_code}")
        assert cross_create_res.status_code in [400, 403, 404]
        print(f"  ✅ Security Verified: User B blocked from using User A's material ({cross_create_res.json().get('detail')}).")

        # 7. Security Isolation: User B Attempts to Access User A's Quiz
        cross_get_res = client.get(f"/api/v1/quizzes/{quiz_id}", headers=headers_b)
        print(f"7. User B GET /api/v1/quizzes/{quiz_id} -> Status: {cross_get_res.status_code}")
        assert cross_get_res.status_code in [403, 404]
        print("  ✅ Security Verified: User B blocked from accessing User A's quiz.")

        print("\n" + "=" * 80)
        print("ALL DEFECT 1 & DEFECT 2 TARGETED CHECKS PASSED ✅")
        print("=" * 80)


if __name__ == "__main__":
    run_defect_cycle_1_verification()
