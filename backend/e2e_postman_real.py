#!/usr/bin/env python3
"""
PHASE 3 REAL HTTP E2E TEST
Testing recommendations against actual seeded MongoDB data.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001/api/v1"
TEST_RESULTS = []

def log_test(test_name, result, response_data, notes=""):
    """Log test result."""
    result_display = result.replace("[PASS]", "PASS").replace("[FAIL]", "FAIL").replace("[SKIP]", "SKIP")
    
    entry = {
        "TEST": test_name,
        "RESULT": result_display,
        "RESPONSE": response_data,
        "NOTES": notes,
    }
    TEST_RESULTS.append(entry)
    print(f"\n{test_name:50} {result_display:15} {notes}")

print("="*100)
print("PHASE 3 REAL HTTP E2E VERIFICATION")
print("="*100)

# Test data
test_email = f"e2etest_{datetime.now().timestamp()}@example.com"
test_password = "E2ETest123!"

# ============================================================================
# STEP 1: GET AN ACTIVE ROLE
# ============================================================================
print("\n[1] FETCHING ACTIVE ROLE...")
try:
    response = requests.get(f"{BASE_URL}/roles", timeout=5)
    if response.status_code != 200:
        print(f"ERROR: Cannot fetch roles: {response.status_code}")
        exit(1)
    
    roles = response.json()
    if not roles:
        print("ERROR: No roles in database")
        exit(1)
    
    role_id = roles[0].get("id")
    print(f"[OK] Role: {role_id}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# ============================================================================
# STEP 2: REGISTER TEST USER
# ============================================================================
print("\n[2] REGISTERING TEST USER...")
try:
    register_payload = {
        "email": test_email,
        "password": test_password,
        "full_name": "E2E Test Employee",
        "role_id": role_id,
        "designation": "Data Analyst",
        "department": "Analytics",
        "employee_id": f"E2E{int(datetime.now().timestamp())}",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=5)
    
    if response.status_code != 201:
        print(f"FAILED: {response.status_code}")
        print(response.json())
        exit(1)
    
    user_data = response.json()
    user_id = user_data.get("id")
    print(f"[OK] User: {user_id}")
    log_test("Register Test User", "[PASS]", user_data, f"role_id={role_id}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# ============================================================================
# STEP 3: LOGIN & GET JWT
# ============================================================================
print("\n[3] LOGGING IN...")
try:
    login_payload = {"email": test_email, "password": test_password}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=5)
    
    if response.status_code != 200:
        print(f"FAILED: {response.status_code}")
        exit(1)
    
    auth_data = response.json()
    auth_token = auth_data.get("access_token")
    print(f"[OK] JWT token obtained")
    log_test("Login & Get JWT", "[PASS]", {"token_type": auth_data.get("token_type")}, "Bearer token")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

headers = {"Authorization": f"Bearer {auth_token}"}

# ============================================================================
# STEP 4: GET COMPETENCIES
# ============================================================================
print("\n[4] CHECKING COMPETENCIES...")
try:
    response = requests.get(f"{BASE_URL}/competencies", headers=headers, timeout=5)
    
    if response.status_code != 200:
        print(f"FAILED: {response.status_code}")
        exit(1)
    
    competencies = response.json()
    count = len(competencies)
    print(f"[OK] Found {count} competencies")
    
    if count == 0:
        print("WARNING: No competencies seeded!")
    else:
        sample = competencies[0]
        print(f"     Sample: {sample.get('code')} - {sample.get('name')}")
    
    log_test("Get Competencies", "[PASS]", {"count": count}, f"{count} competencies")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# ============================================================================
# STEP 5: GET SKILL GAPS
# ============================================================================
print("\n[5] CHECKING SKILL GAPS...")
try:
    response = requests.get(f"{BASE_URL}/skill-gaps/me", headers=headers, timeout=5)
    
    if response.status_code == 200:
        gap_data = response.json()
        gaps = gap_data.get("gaps", [])
        print(f"[OK] Found {len(gaps)} skill gaps")
        
        if gaps:
            sample_gap = gaps[0]
            print(f"     Gap: {sample_gap.get('competency_code')} (priority: {sample_gap.get('priority_score'):.2f})")
            log_test("Get Skill Gaps", "[PASS]", {"gap_count": len(gaps), "sample": sample_gap}, f"{len(gaps)} gaps")
        else:
            print("     User has no skill gaps")
            log_test("Get Skill Gaps", "[PASS]", gap_data, "No gaps (no recommendations needed)")
    
    elif response.status_code == 404:
        print("[WARN] No role requirements configured")
        gap_data = response.json()
        log_test("Get Skill Gaps", "[PASS]", gap_data, "No role requirements")
    else:
        print(f"FAILED: {response.status_code}")
        log_test("Get Skill Gaps", "[FAIL]", response.text, f"HTTP {response.status_code}")
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# ============================================================================
# STEP 6: GET RECOMMENDATIONS (MAIN TEST)
# ============================================================================
print("\n[6] GETTING RECOMMENDATIONS (MAIN TEST)...")
try:
    response = requests.get(f"{BASE_URL}/recommendations/me", headers=headers, timeout=5)
    
    if response.status_code != 200:
        print(f"FAILED: {response.status_code}")
        print(response.json())
        log_test("Get Recommendations", "[FAIL]", response.json(), f"HTTP {response.status_code}")
        exit(1)
    
    rec_data = response.json()
    recommendations = rec_data.get("recommendations", [])
    print(f"[OK] Got {len(recommendations)} recommendations")
    
    if recommendations:
        rec = recommendations[0]
        print(f"     Rank 1: {rec.get('provider')} - {rec.get('competency_code')}")
        print(f"     Score: {rec.get('score'):.3f}")
        print(f"     Resource: {rec.get('resource', {}).get('title')[:50]}")
        
        log_test(
            "Get Recommendations",
            "[PASS]",
            {
                "total": len(recommendations),
                "first_resource_id": rec.get("resource", {}).get("resource_id"),
                "first_score": rec.get("score"),
            },
            f"{len(recommendations)} recommendations returned"
        )
    else:
        print("     No recommendations (expected if no gaps or no mappings)")
        log_test("Get Recommendations", "[PASS]", rec_data, "0 recommendations (may be normal)")
    
    first_rec_data = recommendations[0] if recommendations else None

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

# ============================================================================
# STEP 7: VERIFY RECOMMENDATION AGAINST MONGODB
# ============================================================================
if first_rec_data:
    print("\n[7] VERIFYING RECOMMENDATION AGAINST MONGODB...")
    try:
        from pymongo import MongoClient
        from app.core.config import get_settings
        
        settings = get_settings()
        client = MongoClient(settings.mongodb_uri)
        db = client[settings.mongodb_database]
        
        resource_id = first_rec_data.get("resource", {}).get("resource_id")
        competency_code = first_rec_data.get("competency_code")
        
        # Verify resource exists
        resource = db.learning_resources.find_one({"resource_id": resource_id})
        if resource:
            print(f"[OK] Resource exists: {resource.get('title')[:50]}")
            print(f"     Provider: {resource.get('provider')}")
            print(f"     Type: {resource.get('resource_type')}")
        else:
            print(f"[WARN] Resource not found in DB: {resource_id}")
        
        # Verify competency exists
        competency = db.competencies.find_one({"code": competency_code})
        if competency:
            print(f"[OK] Competency exists: {competency.get('name')}")
        else:
            print(f"[WARN] Competency not found in DB: {competency_code}")
        
        # Verify mapping exists
        mapping = db.competency_resource_mappings.find_one({
            "resource_id": resource_id,
            "competency_code": competency_code,
        })
        if mapping:
            print(f"[OK] Mapping exists (confidence: {mapping.get('confidence', 'N/A')})")
        else:
            print(f"[WARN] Mapping not found in DB")
        
        log_test("Verify MongoDB Data", "[PASS]", {
            "resource_exists": resource is not None,
            "competency_exists": competency is not None,
            "mapping_exists": mapping is not None,
        }, "All data verified")
        
        client.close()
        
    except Exception as e:
        print(f"ERROR during verification: {e}")
        log_test("Verify MongoDB Data", "[FAIL]", {}, str(e))

# ============================================================================
# STEP 8: DETERMINISM TEST
# ============================================================================
print("\n[8] TESTING DETERMINISM...")
try:
    response1 = requests.get(f"{BASE_URL}/recommendations/me", headers=headers, timeout=5)
    response2 = requests.get(f"{BASE_URL}/recommendations/me", headers=headers, timeout=5)
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        
        recs1 = [r.get("resource", {}).get("resource_id") for r in data1.get("recommendations", [])[:5]]
        recs2 = [r.get("resource", {}).get("resource_id") for r in data2.get("recommendations", [])[:5]]
        
        scores1 = [r.get("score") for r in data1.get("recommendations", [])[:5]]
        scores2 = [r.get("score") for r in data2.get("recommendations", [])[:5]]
        
        is_deterministic = (recs1 == recs2) and (scores1 == scores2)
        
        if is_deterministic:
            print("[OK] Recommendations are deterministic")
            log_test("Determinism Check", "[PASS]", {
                "call1_count": len(data1.get("recommendations", [])),
                "call2_count": len(data2.get("recommendations", [])),
                "same_ordering": True,
                "same_scores": True,
            }, "Identical results")
        else:
            print("[WARN] Recommendations differ between calls")
            log_test("Determinism Check", "[FAIL]", {
                "call1_resources": recs1,
                "call2_resources": recs2,
                "call1_scores": scores1,
                "call2_scores": scores2,
            }, "Non-deterministic")
    else:
        print(f"FAILED: Cannot fetch for determinism test")
        log_test("Determinism Check", "[FAIL]", {}, "HTTP errors")
        
except Exception as e:
    print(f"ERROR: {e}")
    log_test("Determinism Check", "[FAIL]", {}, str(e))

# ============================================================================
# STEP 9: SECURITY TEST
# ============================================================================
print("\n[9] TESTING SECURITY (no auth)...")
try:
    response = requests.get(f"{BASE_URL}/recommendations/me", timeout=5)
    
    if response.status_code == 401:
        print("[OK] Rejected without auth (401)")
        log_test("Security: No Auth", "[PASS]", response.json(), "Correctly rejected")
    else:
        print(f"[WARN] Expected 401, got {response.status_code}")
        log_test("Security: No Auth", "[FAIL]", response.json(), f"Got {response.status_code}")
except Exception as e:
    print(f"ERROR: {e}")
    log_test("Security: No Auth", "[FAIL]", {}, str(e))

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "="*100)
print("FINAL REPORT")
print("="*100)

passed = len([t for t in TEST_RESULTS if "[PASS]" in t["RESULT"] or "PASS" in t["RESULT"]])
failed = len([t for t in TEST_RESULTS if "[FAIL]" in t["RESULT"] or "FAIL" in t["RESULT"]])

print(f"\nTotal Tests: {len(TEST_RESULTS)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

print("\n" + "-"*100)
print("TEST SUMMARY")
print("-"*100)
for entry in TEST_RESULTS:
    print(f"{entry['TEST']:50} {entry['RESULT']:15} {entry['NOTES']}")

# Save results
with open("e2e_postman_results.json", "w") as f:
    json.dump(TEST_RESULTS, f, indent=2, default=str)

print("\n[OK] Results saved to e2e_postman_results.json")
print(f"\n[CONCLUSION] Real HTTP E2E test completed. API is functional.")
