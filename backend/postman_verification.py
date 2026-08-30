#!/usr/bin/env python3
"""
PHASE 3 POSTMAN VERIFICATION
Real HTTP/API verification against running backend.
No code changes. Verification only.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001/api/v1"
TEST_RESULTS = []

def log_test(test_name, result, actual_response, notes=""):
    """Log test result in Postman format."""
    # Clean result string for Windows console encoding
    result_clean = result.replace("✅", "[PASS]").replace("❌", "[FAIL]").replace("⚠️", "[WARN]").replace("⊘", "[SKIP]")
    
    entry = {
        "TEST": test_name,
        "RESULT": result_clean,
        "ACTUAL_RESPONSE": actual_response,
        "NOTES": notes,
    }
    TEST_RESULTS.append(entry)
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"RESULT: {result_clean}")
    print(f"RESPONSE: {json.dumps(actual_response, indent=2) if isinstance(actual_response, (dict, list)) else actual_response}")
    if notes:
        print(f"NOTES: {notes}")
    print('='*80)

# Global auth token
auth_token = None
test_user_id = None
test_email = f"testuser_{datetime.now().timestamp()}@example.com"
test_password = "TestPassword123!"

# ============================================================================
# STEP 1: HEALTH CHECK
# ============================================================================
print("\n" + "="*80)
print("STEP 1: HEALTH CHECK")
print("="*80)

try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
    log_test(
        "Health Check",
        result,
        response.json() if response.status_code == 200 else response.text,
        "Server responding normally"
    )
except Exception as e:
    log_test("Health Check", f"❌ ERROR: {str(e)}", {}, "Connection failed")
    sys.exit(1)

# ============================================================================
# STEP 2: REGISTER & LOGIN
# ============================================================================
print("\n" + "="*80)
print("STEP 2: REGISTER & LOGIN")
print("="*80)

# First, get a valid role ID
try:
    roles_response = requests.get(f"{BASE_URL}/roles", timeout=5)
    if roles_response.status_code == 200:
        roles = roles_response.json()
        if roles:
            role_id = roles[0].get("id")
            print(f"Found role: {role_id}")
        else:
            log_test("Get Roles", "❌ FAIL", {}, "No roles in database")
            sys.exit(1)
    else:
        log_test("Get Roles", f"❌ FAIL ({roles_response.status_code})", {}, "Cannot fetch roles")
        sys.exit(1)
except Exception as e:
    log_test("Get Roles", f"❌ ERROR", {}, str(e))
    sys.exit(1)

# Register
try:
    register_payload = {
        "email": test_email,
        "password": test_password,
        "full_name": "Test Employee",
        "role_id": role_id,
        "designation": "Engineer",
        "department": "Technology",
        "employee_id": f"EMP{datetime.now().timestamp()}",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=5)
    result = "✅ PASS" if response.status_code == 201 else f"❌ FAIL ({response.status_code})"
    resp_data = response.json() if response.status_code in [201, 422] else response.text
    
    if response.status_code == 201:
        test_user_id = resp_data.get("id")
        print(f"Registered user: {test_user_id}")
    else:
        print(f"Registration response: {resp_data}")
    
    log_test(
        "Register User",
        result,
        resp_data,
        f"Email: {test_email}, Role: {role_id}"
    )
except Exception as e:
    log_test("Register User", f"❌ ERROR", {}, str(e))
    sys.exit(1)

# Login
try:
    login_payload = {
        "email": test_email,
        "password": test_password,
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=5)
    result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
    resp_data = response.json() if response.status_code == 200 else response.text
    
    if response.status_code == 200:
        auth_token = resp_data.get("access_token")
        print(f"Got token: {auth_token[:20]}...")
        if not test_user_id:
            test_user_id = resp_data.get("user", {}).get("id")
    
    log_test(
        "Login User",
        result,
        resp_data,
        "Authenticated for subsequent requests"
    )
except Exception as e:
    log_test("Login User", f"❌ ERROR", {}, str(e))
    sys.exit(1)

if not auth_token:
    log_test("Auth Setup", "❌ FAIL", {}, "Could not obtain auth token")
    sys.exit(1)

headers = {"Authorization": f"Bearer {auth_token}"}

# ============================================================================
# STEP 3: GET COMPETENCIES
# ============================================================================
print("\n" + "="*80)
print("STEP 3: GET COMPETENCIES (Verify 42 exist)")
print("="*80)

try:
    response = requests.get(f"{BASE_URL}/competencies", headers=headers, timeout=5)
    result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
    resp_data = response.json() if response.status_code == 200 else response.text
    
    competencies = resp_data if isinstance(resp_data, list) else []
    count = len(competencies)
    
    # Sample first competency for inspection
    sample = competencies[0] if competencies else None
    
    log_test(
        "Get Competencies",
        result,
        {"count": count, "sample": sample},
        f"Expected: 42, Actual: {count}"
    )
except Exception as e:
    log_test("Get Competencies", f"❌ ERROR", {}, str(e))

# ============================================================================
# STEP 4: GET USER PROFILE
# ============================================================================
print("\n" + "="*80)
print("STEP 4: GET USER PROFILE")
print("="*80)

try:
    response = requests.get(f"{BASE_URL}/users/me", headers=headers, timeout=5)
    result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
    resp_data = response.json() if response.status_code == 200 else response.text
    
    log_test(
        "Get User Profile",
        result,
        resp_data,
        f"Authenticated user: {test_email}"
    )
except Exception as e:
    log_test("Get User Profile", f"❌ ERROR", {}, str(e))

# ============================================================================
# STEP 5: GET SKILL GAPS
# ============================================================================
print("\n" + "="*80)
print("STEP 5: GET SKILL GAPS (Find meaningful gap)")
print("="*80)

skill_gaps = []
try:
    response = requests.get(f"{BASE_URL}/skill-gaps/me", headers=headers, timeout=5)
    result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
    resp_data = response.json() if response.status_code in [200, 422, 404] else response.text
    
    if response.status_code == 200:
        skill_gaps = resp_data.get("gaps", [])
    
    log_test(
        "Get Skill Gaps",
        result,
        resp_data,
        f"Gaps found: {len(skill_gaps) if isinstance(skill_gaps, list) else 'error'}"
    )
except Exception as e:
    log_test("Get Skill Gaps", f"❌ ERROR", {}, str(e))

# ============================================================================
# STEP 6: GET RECOMMENDATIONS (MAIN TEST)
# ============================================================================
print("\n" + "="*80)
print("STEP 6: GET RECOMMENDATIONS (MAIN TEST - Verify real data)")
print("="*80)

recommendations = None
try:
    response = requests.get(f"{BASE_URL}/recommendations/me", headers=headers, timeout=5)
    result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
    resp_data = response.json() if response.status_code in [200, 503] else response.text
    
    if response.status_code == 200:
        recommendations = resp_data
    
    # Detailed inspection
    inspection = {
        "status_code": response.status_code,
        "has_recommendations": bool(resp_data.get("recommendations")) if isinstance(resp_data, dict) else False,
        "count": len(resp_data.get("recommendations", [])) if isinstance(resp_data, dict) else 0,
    }
    
    if isinstance(resp_data, dict) and resp_data.get("recommendations"):
        first_rec = resp_data["recommendations"][0]
        inspection["first_recommendation_sample"] = {
            "competency_code": first_rec.get("competency_code"),
            "resource_id": first_rec.get("resource_id"),
            "title": first_rec.get("title"),
            "provider": first_rec.get("provider"),
            "score": first_rec.get("score"),
            "has_explanation": bool(first_rec.get("explanation")),
        }
    
    log_test(
        "Get Recommendations",
        result,
        inspection,
        "MAIN TEST: Verify real MongoDB data"
    )
except Exception as e:
    log_test("Get Recommendations", f"❌ ERROR", {}, str(e))

# ============================================================================
# STEP 7: GET RESOURCE BY ID (if recommendation exists)
# ============================================================================
print("\n" + "="*80)
print("STEP 7: GET RESOURCE BY ID")
print("="*80)

if recommendations and recommendations.get("recommendations"):
    sample_resource_id = recommendations["recommendations"][0].get("resource_id")
    if sample_resource_id:
        try:
            response = requests.get(
                f"{BASE_URL}/recommendations/resources/{sample_resource_id}",
                headers=headers,
                timeout=5
            )
            result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            resp_data = response.json() if response.status_code in [200, 404] else response.text
            
            log_test(
                f"Get Resource: {sample_resource_id}",
                result,
                resp_data,
                "Verify real MongoDB resource"
            )
        except Exception as e:
            log_test(f"Get Resource: {sample_resource_id}", f"❌ ERROR", {}, str(e))
else:
    log_test("Get Resource By ID", "⊘ SKIP", {}, "No recommendations returned")

# ============================================================================
# STEP 8: GET RESOURCES BY COMPETENCY
# ============================================================================
print("\n" + "="*80)
print("STEP 8: GET RESOURCES BY COMPETENCY")
print("="*80)

if skill_gaps and isinstance(skill_gaps, list) and len(skill_gaps) > 0:
    sample_competency = skill_gaps[0].get("competency_code", "TECH_SQL")
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/competencies/{sample_competency}/resources",
            headers=headers,
            timeout=5
        )
        result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
        resp_data = response.json() if response.status_code in [200, 404] else response.text
        
        log_test(
            f"Get Resources by Competency: {sample_competency}",
            result,
            resp_data if isinstance(resp_data, dict) else {"error": str(resp_data)},
            "Verify competency-resource mappings"
        )
    except Exception as e:
        log_test(f"Get Resources by Competency", f"❌ ERROR", {}, str(e))
else:
    log_test("Get Resources by Competency", "⊘ SKIP", {}, "No skill gaps to test")

# ============================================================================
# STEP 9: VERIFY PROVIDER SEPARATION
# ============================================================================
print("\n" + "="*80)
print("STEP 9: VERIFY PROVIDER SEPARATION")
print("="*80)

# Try to find resources from each provider
for provider in ["IGOT", "NSSTA"]:
    try:
        response = requests.get(
            f"{BASE_URL}/recommendations/resources/unmapped",
            params={"provider": provider, "limit": 1},
            headers=headers,
            timeout=5
        )
        result = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
        resp_data = response.json() if response.status_code == 200 else response.text
        
        if isinstance(resp_data, dict):
            count = resp_data.get("total_resources", 0)
        else:
            count = 0
        
        log_test(
            f"Get Resources: Provider={provider}",
            result,
            {"provider": provider, "count": count, "sample": resp_data.get("resources", [])[:1] if isinstance(resp_data, dict) else resp_data},
            f"Provider separation: {count} {provider} resources"
        )
    except Exception as e:
        log_test(f"Get Resources: {provider}", f"❌ ERROR", {}, str(e))

# ============================================================================
# STEP 10: SECURITY - UNAUTHENTICATED REQUEST
# ============================================================================
print("\n" + "="*80)
print("STEP 10: SECURITY - UNAUTHENTICATED REQUEST")
print("="*80)

try:
    response = requests.get(f"{BASE_URL}/recommendations/me", timeout=5)
    result = "✅ PASS" if response.status_code == 401 else f"❌ FAIL (expected 401, got {response.status_code})"
    resp_data = response.json() if response.status_code in [401, 403] else response.text
    
    log_test(
        "Unauthenticated Recommendation Request",
        result,
        resp_data,
        "Should reject without JWT token"
    )
except Exception as e:
    log_test("Unauthenticated Request", f"❌ ERROR", {}, str(e))

# ============================================================================
# STEP 11: DETERMINISM - Call twice, compare
# ============================================================================
print("\n" + "="*80)
print("STEP 11: DETERMINISM - Call recommendations twice")
print("="*80)

try:
    response1 = requests.get(f"{BASE_URL}/recommendations/me", headers=headers, timeout=5)
    response2 = requests.get(f"{BASE_URL}/recommendations/me", headers=headers, timeout=5)
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        # Compare top recommendations
        recs1 = [r.get("resource_id") for r in data1.get("recommendations", [])[:5]]
        recs2 = [r.get("resource_id") for r in data2.get("recommendations", [])[:5]]
        
        is_deterministic = recs1 == recs2
        result = "✅ PASS" if is_deterministic else "⚠️  DIFFERENT"
        
        log_test(
            "Determinism Check",
            result,
            {
                "call_1_top_5": recs1,
                "call_2_top_5": recs2,
                "identical": is_deterministic,
            },
            "Verify consistent recommendation ordering"
        )
    else:
        log_test("Determinism Check", "❌ FAIL", {}, "Could not fetch recommendations twice")
except Exception as e:
    log_test("Determinism Check", f"❌ ERROR", {}, str(e))

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "="*80)
print("FINAL REPORT - PHASE 3 POSTMAN VERIFICATION")
print("="*80)

print("\n| TEST | RESULT | ACTUAL RESPONSE | NOTES |")
print("|------|--------|-----------------|-------|")

for entry in TEST_RESULTS:
    test = entry["TEST"]
    result = entry["RESULT"]
    response_preview = str(entry["ACTUAL_RESPONSE"])[:50] + "..." if len(str(entry["ACTUAL_RESPONSE"])) > 50 else str(entry["ACTUAL_RESPONSE"])
    notes = entry["NOTES"][:30] + "..." if len(entry["NOTES"]) > 30 else entry["NOTES"]
    
    print(f"| {test} | {result} | {response_preview} | {notes} |")

# Save detailed results
with open("postman_verification_results.json", "w") as f:
    json.dump(TEST_RESULTS, f, indent=2, default=str)

print(f"\n✅ Verification complete. Results saved to postman_verification_results.json")
print(f"\nServer: http://127.0.0.1:8001")
print(f"Test user: {test_email}")
print(f"Total tests: {len(TEST_RESULTS)}")
print(f"Passed: {len([t for t in TEST_RESULTS if '✅' in t['RESULT']])}")
print(f"Failed: {len([t for t in TEST_RESULTS if '❌' in t['RESULT']])}")

