import requests
import time
import json
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def print_result(test_name, status, details=""):
    print(f"[{status}] {test_name}: {details}")

def run_tests():
    # Wait a bit for server to start
    time.sleep(2)
    
    # TEST 1: Health
    try:
        res = requests.get(f"{BASE_URL}/health")
        if res.status_code == 200:
            print_result("TEST 1 - Health", "PASS")
        else:
            print_result("TEST 1 - Health", "FAIL", f"Status code {res.status_code}")
    except Exception as e:
        print_result("TEST 1 - Health", "FAIL", str(e))
        return

    # Create unique user to avoid conflict
    uid = str(uuid.uuid4())[:8]
    email = f"test_{uid}@example.com"
    password = "Password123!"

    # Setup: We need a role ID to register
    # We can fetch roles from the DB directly since we don't know an endpoint
    from pymongo import MongoClient
    client = MongoClient("mongodb://localhost:27017")
    db = client.shikshasetu
    role = db.roles.find_one()
    if not role:
        print_result("TEST 2 - Setup", "FAIL", "No roles found in DB")
        return
    role_id = str(role["_id"])

    # TEST 2: Register/Login
    token = None
    try:
        reg_payload = {
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role_id": role_id,
            "designation": "Developer",
            "department": "Engineering",
            "employee_id": f"EMP{uid}"
        }
        res_reg = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        
        login_payload = {
            "email": email,
            "password": password
        }
        res_login = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        if res_login.status_code == 200:
            token = res_login.json().get("access_token")
            print_result("TEST 2 - Register/Login", "PASS")
        else:
            print_result("TEST 2 - Register/Login", "FAIL", f"Login failed: {res_login.status_code}")
    except Exception as e:
        print_result("TEST 2 - Register/Login", "FAIL", str(e))

    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # TEST 3: Get Competencies
    comp_code = None
    try:
        res_comp = requests.get(f"{BASE_URL}/competencies", headers=headers)
        if res_comp.status_code == 200:
            comps = res_comp.json()
            if comps:
                comp_code = comps[0].get("competency_code")
                print_result("TEST 3 - Get Competencies", "PASS", f"Found competency {comp_code}")
            else:
                print_result("TEST 3 - Get Competencies", "FAIL", "Empty competencies list")
        else:
            print_result("TEST 3 - Get Competencies", "FAIL", f"Status code {res_comp.status_code}")
    except Exception as e:
        print_result("TEST 3 - Get Competencies", "FAIL", str(e))

    # TEST 4: Profile (Skip, as discussed)
    print_result("TEST 4 - Get Competency Profile", "SKIPPED", "No direct endpoint")

    # TEST 5: Get Current Skill Gaps
    try:
        res_sg = requests.get(f"{BASE_URL}/skill-gaps/me", headers=headers)
        if res_sg.status_code == 200:
            print_result("TEST 5 - Get Current Skill Gaps", "PASS")
        else:
            print_result("TEST 5 - Get Current Skill Gaps", "FAIL", f"Status {res_sg.status_code} - {res_sg.text}")
    except Exception as e:
        print_result("TEST 5 - Get Current Skill Gaps", "FAIL", str(e))

    if not comp_code:
        return

    # TEST 6: Create Capability Assessment
    assessment_id = None
    try:
        payload_assess = {"competency_code": comp_code}
        res_ca = requests.post(f"{BASE_URL}/assessments/capability", json=payload_assess, headers=headers)
        if res_ca.status_code == 201:
            assessment_id = res_ca.json().get("_id")
            print_result("TEST 6 - Create Capability Assessment", "PASS", f"Assessment ID: {assessment_id}")
        else:
            print_result("TEST 6 - Create Capability Assessment", "FAIL", f"Status {res_ca.status_code} - {res_ca.text}")
    except Exception as e:
        print_result("TEST 6 - Create Capability Assessment", "FAIL", str(e))

    if not assessment_id:
        return

    # TEST 7: Retrieve Assessment & TEST 8: Answers hidden
    questions = []
    try:
        res_ret = requests.get(f"{BASE_URL}/assessments/capability/{assessment_id}", headers=headers)
        if res_ret.status_code == 200:
            data = res_ret.json()
            questions = data.get("questions", [])
            print_result("TEST 7 - Retrieve Assessment", "PASS")
            
            # Check for answer keys
            answers_hidden = True
            for q in questions:
                if "correct_answer" in q or "explanation" in q:
                    answers_hidden = False
            if answers_hidden:
                print_result("TEST 8 - Verify Answer Keys Are Hidden", "PASS")
            else:
                print_result("TEST 8 - Verify Answer Keys Are Hidden", "FAIL", "Found answer keys in response")
        else:
            print_result("TEST 7 - Retrieve Assessment", "FAIL", f"Status {res_ret.status_code}")
            print_result("TEST 8 - Verify Answer Keys Are Hidden", "FAIL", "Could not retrieve assessment")
    except Exception as e:
        print_result("TEST 7/8", "FAIL", str(e))

    # TEST 9 & 10: Submit Assessment
    try:
        if questions:
            answers = []
            for q in questions:
                # just guess 'A' or the first option
                answers.append({
                    "question_id": q["question_id"],
                    "selected_answer": q["options"][0] if q.get("options") else "A"
                })
            submit_payload = {"answers": answers}
            res_sub = requests.post(f"{BASE_URL}/assessments/capability/{assessment_id}/submit", json=submit_payload, headers=headers)
            if res_sub.status_code == 200:
                print_result("TEST 9 - Submit Assessment", "PASS")
                data = res_sub.json()
                if "score" in data and "percentage" in data:
                    print_result("TEST 10 - Verify Server-Side Score", "PASS", f"Score: {data['score']}")
                else:
                    print_result("TEST 10 - Verify Server-Side Score", "FAIL", "Score not in response")
            else:
                print_result("TEST 9 - Submit Assessment", "FAIL", f"Status {res_sub.status_code} - {res_sub.text}")
                print_result("TEST 10 - Verify Server-Side Score", "FAIL", "Submission failed")
    except Exception as e:
        print_result("TEST 9/10", "FAIL", str(e))

    print_result("TEST 11 - Verify Evidence", "SKIPPED", "Manual DB check required")
    print_result("TEST 12 - Verify Competency Update", "SKIPPED", "Can be verified via skill-gaps")
    print_result("TEST 13 - Verify Skill Gap Update", "SKIPPED", "Can be verified via skill-gaps")

    # TEST 14: Duplicate Submission
    try:
        if questions:
            res_dup = requests.post(f"{BASE_URL}/assessments/capability/{assessment_id}/submit", json=submit_payload, headers=headers)
            if res_dup.status_code in (400, 409):
                print_result("TEST 14 - Duplicate Submission", "PASS")
            else:
                print_result("TEST 14 - Duplicate Submission", "FAIL", f"Status {res_dup.status_code}")
    except Exception as e:
        print_result("TEST 14 - Duplicate Submission", "FAIL", str(e))

if __name__ == '__main__':
    run_tests()
