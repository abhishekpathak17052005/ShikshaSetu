#!/usr/bin/env python3
"""
POSTMAN VERIFICATION - CONTROLLED HTTP TESTING
Real API calls. No unit tests. No code inspection.
Report: TEST# | METHOD+URL | AUTH | REQ_BODY | HTTP_STATUS | RESPONSE | PASS/FAIL | REASON
"""

import requests
import json
from datetime import datetime

BASE = "http://127.0.0.1:8001/api/v1"
RESULTS = []

def test(num, method, path, auth=False, body=None, expected_status=None, description=""):
    """Execute HTTP test and record result."""
    url = f"{BASE}{path}"
    headers = {}
    
    if auth:
        headers["Authorization"] = f"Bearer {GLOBAL_TOKEN}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            resp = requests.post(url, json=body, headers=headers, timeout=5)
        elif method == "PUT":
            resp = requests.put(url, json=body, headers=headers, timeout=5)
        else:
            resp = None
        
        if resp is None:
            status = "ERROR"
            resp_data = "No response"
            result = "FAIL"
        else:
            status = resp.status_code
            try:
                resp_data = resp.json()
            except:
                resp_data = resp.text[:100]
            
            result = "PASS" if (expected_status is None or status == expected_status) else "FAIL"
        
        # Record
        entry = {
            "num": num,
            "desc": description,
            "method": method,
            "url": url,
            "auth": "JWT" if auth else "None",
            "status": status,
            "result": result,
            "response": resp_data if isinstance(resp_data, dict) else str(resp_data)[:200]
        }
        
        RESULTS.append(entry)
        
        # Print
        print(f"\n{'='*100}")
        print(f"TEST {num}: {description}")
        print(f"{'='*100}")
        print(f"METHOD:   {method} {path}")
        print(f"AUTH:     {'JWT Bearer' if auth else 'None'}")
        if body:
            print(f"BODY:     {json.dumps(body, indent=2)[:200]}")
        print(f"EXPECTED: {expected_status if expected_status else 'Any'}")
        print(f"ACTUAL:   {status}")
        print(f"RESULT:   {result}")
        if isinstance(resp_data, dict):
            print(f"RESPONSE: {json.dumps(resp_data, indent=2)[:500]}")
        else:
            print(f"RESPONSE: {resp_data}")
        
        return resp_data if resp else None
        
    except Exception as e:
        print(f"\nTEST {num}: {description}")
        print(f"ERROR: {str(e)}")
        RESULTS.append({
            "num": num,
            "desc": description,
            "result": "FAIL",
            "error": str(e)
        })
        return None

# Global vars for test data
GLOBAL_TOKEN = None
GLOBAL_USER_ID = None
GLOBAL_EMAIL = f"postman_test_{datetime.now().timestamp()}@example.com"
GLOBAL_PASSWORD = "PostmanTest123!"
GLOBAL_ROLE_ID = None
GLOBAL_MATERIAL_ID = None
GLOBAL_QUIZ_ID = None
GLOBAL_COMPETENCY_CODE = "TECH_PYTHON"

print("\n" + "="*100)
print("WORKFLOW 1: REGISTRATION → LOGIN → COMPETENCIES → ASSESSMENT → GAPS → RECOMMENDATIONS")
print("="*100)

# TEST 1: Get Role (prerequisite)
print("\n[PREREQUISITE] Getting active role...")
resp = requests.get(f"{BASE}/roles", timeout=5)
if resp.status_code == 200:
    roles = resp.json()
    if roles:
        GLOBAL_ROLE_ID = roles[0].get("id")
        print(f"Found role: {GLOBAL_ROLE_ID}")
    else:
        print("ERROR: No roles in database")
        exit(1)

# TEST 1: Register
test(
    1,
    "POST",
    "/auth/register",
    auth=False,
    body={
        "email": GLOBAL_EMAIL,
        "password": GLOBAL_PASSWORD,
        "full_name": "Postman Test Employee",
        "role_id": GLOBAL_ROLE_ID,
        "designation": "Data Analyst",
        "department": "Analytics",
        "employee_id": f"POSTMAN_{int(datetime.now().timestamp())}"
    },
    expected_status=201,
    description="Register new employee"
)

# TEST 2: Login
login_resp = test(
    2,
    "POST",
    "/auth/login",
    auth=False,
    body={
        "email": GLOBAL_EMAIL,
        "password": GLOBAL_PASSWORD
    },
    expected_status=200,
    description="Login and get JWT"
)

if login_resp and "access_token" in login_resp:
    GLOBAL_TOKEN = login_resp.get("access_token")
    GLOBAL_USER_ID = login_resp.get("user", {}).get("id")
    print(f"\nToken obtained: {GLOBAL_TOKEN[:30]}...")
    print(f"User ID: {GLOBAL_USER_ID}")
else:
    print("ERROR: Could not obtain token")
    exit(1)

# TEST 3: Get Competencies
comp_resp = test(
    3,
    "GET",
    "/competencies",
    auth=True,
    expected_status=200,
    description="Get competency framework (expect 33)"
)

if comp_resp and isinstance(comp_resp, list):
    print(f"\n✓ Found {len(comp_resp)} competencies")
    # Find TECH_PYTHON for later tests
    for c in comp_resp:
        if c.get("code") == "TECH_PYTHON":
            GLOBAL_COMPETENCY_CODE = "TECH_PYTHON"
            break
else:
    print("ERROR: No competencies returned")

# TEST 4: Get Assessment (to get questions)
print("\n[FETCHING ASSESSMENT QUESTIONS]")
assessment_resp = requests.get(
    f"{BASE}/capability-assessments/competencies/{GLOBAL_COMPETENCY_CODE}",
    headers={"Authorization": f"Bearer {GLOBAL_TOKEN}"},
    timeout=5
)

questions = []
if assessment_resp.status_code == 200:
    assessment_data = assessment_resp.json()
    questions = assessment_data.get("questions", [])
    print(f"Got {len(questions)} questions for {GLOBAL_COMPETENCY_CODE}")

# TEST 5: Submit Assessment (if questions exist)
if questions:
    answers = []
    for q in questions[:3]:  # Answer first 3
        answers.append({
            "question_id": q.get("question_id"),
            "selected_answer": q.get("options", ["A"])[0]  # Pick first option
        })
    
    test(
        5,
        "POST",
        f"/capability-assessments/competencies/{GLOBAL_COMPETENCY_CODE}/submit",
        auth=True,
        body={"answers": answers},
        expected_status=200,
        description="Submit assessment answers"
    )
else:
    print("\nWARNING: No questions fetched, skipping test 5")

# TEST 6: Get User Competency Profile
test(
    6,
    "GET",
    "/users/me",
    auth=True,
    expected_status=200,
    description="Get user profile"
)

# TEST 7: Get Skill Gaps
gaps_resp = test(
    7,
    "GET",
    "/skill-gaps/me",
    auth=True,
    expected_status=200,
    description="Calculate skill gaps"
)

gap_count = 0
if gaps_resp and isinstance(gaps_resp, dict):
    gaps = gaps_resp.get("gaps", [])
    gap_count = len(gaps)
    print(f"\n✓ Found {gap_count} skill gaps")
    if gaps:
        print(f"  Sample gap: {gaps[0].get('competency_code')} (priority: {gaps[0].get('priority_score')})")

# TEST 8: Get Recommendations (MAIN TEST)
rec_resp = test(
    8,
    "GET",
    "/recommendations/me",
    auth=True,
    expected_status=200,
    description="Get personalized learning recommendations"
)

rec_count = 0
top_rec = None
if rec_resp and isinstance(rec_resp, dict):
    recs = rec_resp.get("recommendations", [])
    rec_count = len(recs)
    print(f"\n✓ Got {rec_count} recommendations")
    if recs:
        top_rec = recs[0]
        print(f"\nTOP RECOMMENDATION:")
        print(f"  Resource: {top_rec.get('resource', {}).get('title')[:60]}")
        print(f"  Provider: {top_rec.get('provider')}")
        print(f"  Score: {top_rec.get('score'):.3f}")
        print(f"  Competency: {top_rec.get('competency_code')}")
        
        # Score breakdown
        explanation = top_rec.get('explanation', {})
        score_components = explanation.get('score_breakdown', [])
        print(f"\n  SCORE BREAKDOWN:")
        for comp in score_components:
            print(f"    {comp.get('name'):25} w={comp.get('weight'):.2f} s={comp.get('score'):.2f} v={comp.get('value'):.3f}")

# TEST 9: Test Determinism
print("\n" + "="*100)
print("TEST 9: DETERMINISM CHECK")
print("="*100)

rec_resp_2 = test(
    9,
    "GET",
    "/recommendations/me",
    auth=True,
    expected_status=200,
    description="Call recommendations again (identical data)"
)

if rec_resp and rec_resp_2:
    recs_1 = [r.get('resource', {}).get('resource_id') for r in rec_resp.get('recommendations', [])[:5]]
    recs_2 = [r.get('resource', {}).get('resource_id') for r in rec_resp_2.get('recommendations', [])[:5]]
    
    if recs_1 == recs_2:
        print(f"\n✓ DETERMINISTIC: Same top 5 resources")
        RESULTS[-1]["result"] = "PASS"
    else:
        print(f"\n✗ NON-DETERMINISTIC: Resources differ")
        RESULTS[-1]["result"] = "FAIL"

# TEST 10: Provider Verification
print("\n" + "="*100)
print("TEST 10: PROVIDER SEPARATION")
print("="*100)

test(
    10,
    "GET",
    "/recommendations/resources/unmapped?provider=IGOT&limit=1",
    auth=True,
    expected_status=200,
    description="Get iGOT unmapped resources"
)

# TEST 11: Security - Unauthenticated
test(
    11,
    "GET",
    "/recommendations/me",
    auth=False,
    expected_status=401,
    description="Unauthenticated access (should be rejected)"
)

# TEST 12: Security - Invalid Token
print("\n" + "="*100)
print("TEST 12: SECURITY - INVALID TOKEN")
print("="*100)

resp = requests.get(
    f"{BASE}/recommendations/me",
    headers={"Authorization": "Bearer invalid_token_xyz"},
    timeout=5
)
RESULTS.append({
    "num": 12,
    "desc": "Invalid token rejected",
    "method": "GET",
    "url": f"{BASE}/recommendations/me",
    "auth": "Invalid Bearer",
    "status": resp.status_code,
    "result": "PASS" if resp.status_code == 401 else "FAIL"
})
print(f"Status: {resp.status_code} (expected 401)")
print(f"Result: {'PASS' if resp.status_code == 401 else 'FAIL'}")

print("\n" + "="*100)
print("FINAL REPORT")
print("="*100)

passed = len([r for r in RESULTS if r.get("result") == "PASS"])
failed = len([r for r in RESULTS if r.get("result") == "FAIL"])
skipped = len([r for r in RESULTS if r.get("result") == "SKIP"])

print(f"\nTotal Tests:  {len(RESULTS)}")
print(f"Passed:       {passed}")
print(f"Failed:       {failed}")
print(f"Skipped:      {skipped}")

print(f"\n" + "-"*100)
print("TEST RESULTS SUMMARY")
print("-"*100)

for r in RESULTS:
    status_icon = "✓" if r.get("result") == "PASS" else "✗" if r.get("result") == "FAIL" else "⊘"
    print(f"{status_icon} Test {r.get('num'):2} | {r.get('desc'):50} | {r.get('status', 'ERR'):3} | {r.get('result')}")

print(f"\n" + "="*100)
print("WORKFLOW COMPLETION")
print("="*100)

if rec_count > 0 and gap_count > 0:
    print(f"\n✓ COMPLETE: Assessment → Gaps ({gap_count}) → Recommendations ({rec_count}) workflow WORKS")
    if top_rec:
        print(f"\nActual Recommendation Response (Top):")
        print(json.dumps(top_rec, indent=2, default=str)[:1000])
else:
    print(f"\n✗ INCOMPLETE: Gap count={gap_count}, Rec count={rec_count}")

print(f"\n{'='*100}")
print(f"POSTMAN VERIFICATION COMPLETE")
print(f"{'='*100}")
