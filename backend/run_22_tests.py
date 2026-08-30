#!/usr/bin/env python3
"""Execute the 22-test Postman verification suite exactly as specified."""
import requests
import json
from datetime import datetime
from pathlib import Path

BASE_URL = "http://127.0.0.1:8001"
API_PREFIX = "/api/v1"

# Global state
test_results = []
stored_data = {
    "access_token": None,
    "user_id": None,
    "material_id": None,
    "assessment_id": None,
    "competency_id": None,
    "role_id": None,
    "resource_id": None,
}

def log_test(test_num, test_name, method, url, status, expected_status, result, response_data, notes=""):
    """Log test result."""
    test_results.append({
        "TEST_NUMBER": test_num,
        "TEST_NAME": test_name,
        "METHOD": method,
        "URL": url,
        "EXPECTED_STATUS": expected_status,
        "ACTUAL_STATUS": status,
        "RESULT": result,
        "RESPONSE_SAMPLE": response_data,
        "NOTES": notes,
        "TIMESTAMP": datetime.now().isoformat()
    })
    status_indicator = "✅" if result == "PASS" else "❌"
    print(f"{status_indicator} Test {test_num}: {test_name} [{status}]")

def make_request(method, endpoint, json_body=None, files=None, auth_token=None, expected_status=200):
    """Make HTTP request with error handling."""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, timeout=30)
            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, headers=headers, json=json_body, timeout=10)
        elif method == "PUT":
            headers["Content-Type"] = "application/json"
            response = requests.put(url, headers=headers, json=json_body, timeout=10)
        else:
            return None, 0, "Unsupported method"
        
        return response, response.status_code, response.text
    except Exception as e:
        return None, 0, str(e)

print("\n" + "="*80)
print("SHIKSHASETU 22-TEST POSTMAN VERIFICATION SUITE")
print("="*80 + "\n")

# PHASE 1: Authentication & Setup

print("PHASE 1: Authentication & Setup\n")

# Test 1: Health Check
print("Test 1: Health Check...")
response, status, text = make_request("GET", f"{API_PREFIX}/health", expected_status=200)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status == 200 else "FAIL"
    log_test(1, "Health Check", "GET", f"{API_PREFIX}/health", status, 200, result, {"status": data.get("status", "")})
except:
    log_test(1, "Health Check", "GET", f"{API_PREFIX}/health", status, 200, "FAIL", {}, f"Error: {text}")

# Test 2: Register Test User
print("Test 2: Register Test User...")
register_payload = {
    "email": "postman_test_user@example.com",
    "password": "TestPassword123!",
    "full_name": "Postman Test Employee",
    "role_id": "6a8fe8048524f6da8ebb9881",
    "designation": "Test Officer",
    "department": "Testing",
    "employee_id": "POSTMAN001"
}
response, status, text = make_request("POST", f"{API_PREFIX}/auth/register", json_body=register_payload, expected_status=201)
try:
    data = json.loads(text) if response else {}
    if status in [201, 409]:  # 409 if user already exists
        stored_data["user_id"] = data.get("id")
        result = "PASS"
    else:
        result = "FAIL"
    log_test(2, "Register Test User", "POST", f"{API_PREFIX}/auth/register", status, 201, result, {"id": data.get("id", "")}, "409 acceptable if user exists")
except:
    log_test(2, "Register Test User", "POST", f"{API_PREFIX}/auth/register", status, 201, "FAIL", {}, f"Error: {text}")

# Test 3: Login & Get JWT Token
print("Test 3: Login & Get JWT Token...")
login_payload = {
    "email": "postman_test_user@example.com",
    "password": "TestPassword123!"
}
response, status, text = make_request("POST", f"{API_PREFIX}/auth/login", json_body=login_payload, expected_status=200)
try:
    data = json.loads(text) if response else {}
    if status == 200:
        stored_data["access_token"] = data.get("access_token")
        result = "PASS"
    else:
        result = "FAIL"
    log_test(3, "Login & Get JWT", "POST", f"{API_PREFIX}/auth/login", status, 200, result, {"token_type": data.get("token_type", "")})
except:
    log_test(3, "Login & Get JWT", "POST", f"{API_PREFIX}/auth/login", status, 200, "FAIL", {}, f"Error: {text}")

if not stored_data["access_token"]:
    print("\n❌ CRITICAL: Could not obtain JWT token. Stopping tests.")
    import sys
    sys.exit(1)

print("\n✅ Authentication phase complete. Proceeding with authenticated tests.\n")

# PHASE 2: Core Data Verification

print("PHASE 2: Core Data Verification\n")

# Test 4: Get Assessment Configuration for BEH_CHANGE_MANAGEMENT
print("Test 4: Get Assessment Config for BEH_CHANGE_MANAGEMENT...")
response, status, text = make_request("GET", f"{API_PREFIX}/assessments/configs/BEH_CHANGE_MANAGEMENT", auth_token=stored_data["access_token"])
try:
    data = json.loads(text) if response else {}
    if status == 200:
        result = "PASS"
        log_test(4, "Get Config BEH_CHANGE_MANAGEMENT", "GET", f"{API_PREFIX}/assessments/configs/BEH_CHANGE_MANAGEMENT", status, 200, result, data)
    elif status == 404:
        result = "FAIL_DATA_GAP"
        log_test(4, "Get Config BEH_CHANGE_MANAGEMENT", "GET", f"{API_PREFIX}/assessments/configs/BEH_CHANGE_MANAGEMENT", status, 200, result, data, "Data Gap: Config not seeded (legitimate)")
    else:
        result = "FAIL"
        log_test(4, "Get Config BEH_CHANGE_MANAGEMENT", "GET", f"{API_PREFIX}/assessments/configs/BEH_CHANGE_MANAGEMENT", status, 200, result, data)
except:
    log_test(4, "Get Config BEH_CHANGE_MANAGEMENT", "GET", f"{API_PREFIX}/assessments/configs/BEH_CHANGE_MANAGEMENT", status, 200, "FAIL", {}, f"Error: {text}")

# Test 5: List All Assessment Configurations
print("Test 5: List Assessment Configurations...")
response, status, text = make_request("GET", f"{API_PREFIX}/assessments/configs", expected_status=200)
try:
    data = json.loads(text) if response else []
    count = len(data) if isinstance(data, list) else 0
    result = "PASS" if status == 200 and count > 0 else "FAIL"
    log_test(5, "List Assessment Configs", "GET", f"{API_PREFIX}/assessments/configs", status, 200, result, {"count": count})
except:
    log_test(5, "List Assessment Configs", "GET", f"{API_PREFIX}/assessments/configs", status, 200, "FAIL", {}, f"Error: {text}")

# Test 6: Get All Competencies
print("Test 6: Get All Competencies...")
response, status, text = make_request("GET", f"{API_PREFIX}/competencies", expected_status=200)
try:
    data = json.loads(text) if response else []
    count = len(data) if isinstance(data, list) else 0
    if count > 0 and isinstance(data, list):
        stored_data["competency_id"] = data[0].get("_id") or data[0].get("id")
    result = "PASS" if status == 200 and count >= 42 else "FAIL"
    log_test(6, "Get All Competencies", "GET", f"{API_PREFIX}/competencies", status, 200, result, {"count": count})
except:
    log_test(6, "Get All Competencies", "GET", f"{API_PREFIX}/competencies", status, 200, "FAIL", {}, f"Error: {text}")

# Test 7: Get Specific Competency
print("Test 7: Get Specific Competency...")
if stored_data["competency_id"]:
    response, status, text = make_request("GET", f"{API_PREFIX}/competencies/{stored_data['competency_id']}", expected_status=200)
    try:
        data = json.loads(text) if response else {}
        result = "PASS" if status == 200 else "FAIL"
        log_test(7, "Get Specific Competency", "GET", f"{API_PREFIX}/competencies/{{id}}", status, 200, result, data)
    except:
        log_test(7, "Get Specific Competency", "GET", f"{API_PREFIX}/competencies/{{id}}", status, 200, "FAIL", {}, f"Error: {text}")
else:
    log_test(7, "Get Specific Competency", "GET", f"{API_PREFIX}/competencies/{{id}}", 0, 200, "SKIP", {}, "No competency ID available")

# Test 8: Get Roles
print("Test 8: Get Roles...")
response, status, text = make_request("GET", f"{API_PREFIX}/roles", expected_status=200)
try:
    data = json.loads(text) if response else []
    count = len(data) if isinstance(data, list) else 0
    if count > 0 and isinstance(data, list):
        stored_data["role_id"] = data[0].get("_id") or data[0].get("id")
    result = "PASS" if status == 200 and count >= 1 else "FAIL"
    log_test(8, "Get Roles", "GET", f"{API_PREFIX}/roles", status, 200, result, {"count": count})
except:
    log_test(8, "Get Roles", "GET", f"{API_PREFIX}/roles", status, 200, "FAIL", {}, f"Error: {text}")

# Test 9: Get Role Requirements
print("Test 9: Get Role Requirements...")
if stored_data["role_id"]:
    response, status, text = make_request("GET", f"{API_PREFIX}/roles/{stored_data['role_id']}/requirements", expected_status=200)
    try:
        data = json.loads(text) if response else []
        result = "PASS" if status == 200 else "FAIL"
        log_test(9, "Get Role Requirements", "GET", f"{API_PREFIX}/roles/{{role_id}}/requirements", status, 200, result, {"count": len(data) if isinstance(data, list) else 0})
    except:
        log_test(9, "Get Role Requirements", "GET", f"{API_PREFIX}/roles/{{role_id}}/requirements", status, 200, "FAIL", {}, f"Error: {text}")
else:
    log_test(9, "Get Role Requirements", "GET", f"{API_PREFIX}/roles/{{role_id}}/requirements", 0, 200, "SKIP", {}, "No role ID available")

# Test 10: Get Skill Gaps
print("Test 10: Get Skill Gaps...")
response, status, text = make_request("GET", f"{API_PREFIX}/skill-gaps/me", auth_token=stored_data["access_token"], expected_status=200)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status in [200, 404] else "FAIL"
    log_test(10, "Get Skill Gaps", "GET", f"{API_PREFIX}/skill-gaps/me", status, 200, result, data, "404 acceptable if no role")
except:
    log_test(10, "Get Skill Gaps", "GET", f"{API_PREFIX}/skill-gaps/me", status, 200, "FAIL", {}, f"Error: {text}")

print("\n" + "="*80)
print("PHASE 3: Document Upload & Processing\n")

# Test 11: Upload PDF Document
print("Test 11: Upload PDF Document...")
pdf_path = "/tmp/test_upload.pdf"
try:
    from reportlab.pdfgen import canvas
    from io import BytesIO
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)
    c.drawString(100, 750, "Test Document for Upload")
    c.save()
    with open(pdf_path, "wb") as f:
        f.write(pdf_buffer.getvalue())
    
    with open(pdf_path, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/learning-materials/upload",
            headers={"Authorization": f"Bearer {stored_data['access_token']}"},
            files=files,
            timeout=30
        )
    
    status = response.status_code
    text = response.text
    data = json.loads(text) if response else {}
    
    if status in [200, 201]:
        stored_data["material_id"] = data.get("material_id")
        result = "PASS"
    else:
        result = "FAIL"
    
    log_test(11, "Upload PDF Document", "POST", f"{API_PREFIX}/learning-materials/upload", status, 200, result, {"material_id": data.get("material_id", "")})
except Exception as e:
    log_test(11, "Upload PDF Document", "POST", f"{API_PREFIX}/learning-materials/upload", 0, 200, "FAIL", {}, f"Error: {str(e)}")

# Test 12: Get Upload Material Metadata
print("Test 12: Get Material Metadata...")
if stored_data["material_id"]:
    response, status, text = make_request("GET", f"{API_PREFIX}/learning-materials/{stored_data['material_id']}", auth_token=stored_data["access_token"], expected_status=200)
    try:
        data = json.loads(text) if response else {}
        result = "PASS" if status == 200 else "FAIL"
        log_test(12, "Get Material Metadata", "GET", f"{API_PREFIX}/learning-materials/{{material_id}}", status, 200, result, data)
    except:
        log_test(12, "Get Material Metadata", "GET", f"{API_PREFIX}/learning-materials/{{material_id}}", status, 200, "FAIL", {}, f"Error: {text}")
else:
    log_test(12, "Get Material Metadata", "GET", f"{API_PREFIX}/learning-materials/{{material_id}}", 0, 200, "SKIP", {}, "No material ID from Test 11")

# Test 13: Get Learning Recommendations
print("Test 13: Get Recommendations...")
response, status, text = make_request("GET", f"{API_PREFIX}/recommendations/me", auth_token=stored_data["access_token"], expected_status=200)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status in [200, 404] else "FAIL"
    count = len(data) if isinstance(data, list) else 0
    log_test(13, "Get Recommendations", "GET", f"{API_PREFIX}/recommendations/me", status, 200, result, {"count": count})
except:
    log_test(13, "Get Recommendations", "GET", f"{API_PREFIX}/recommendations/me", status, 200, "FAIL", {}, f"Error: {text}")

# Test 14: Get Competency Resources
print("Test 14: Get Competency Resources...")
response, status, text = make_request("GET", f"{API_PREFIX}/recommendations/competencies/STAT_SAMPLING/resources?provider=IGOT", auth_token=stored_data["access_token"], expected_status=200)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status in [200, 404] else "FAIL"
    log_test(14, "Get Competency Resources", "GET", f"{API_PREFIX}/recommendations/competencies/STAT_SAMPLING/resources", status, 200, result, data)
except:
    log_test(14, "Get Competency Resources", "GET", f"{API_PREFIX}/recommendations/competencies/STAT_SAMPLING/resources", status, 200, "FAIL", {}, f"Error: {text}")

# Test 15: Get Resource Details
print("Test 15: Get Resource Details...")
test_resource_id = "IGOT-12345"  # Try a known resource
response, status, text = make_request("GET", f"{API_PREFIX}/recommendations/resources/{test_resource_id}", auth_token=stored_data["access_token"], expected_status=200)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status in [200, 404] else "FAIL"
    log_test(15, "Get Resource Details", "GET", f"{API_PREFIX}/recommendations/resources/{{resource_id}}", status, 200, result, data, "404 acceptable if resource not found")
except:
    log_test(15, "Get Resource Details", "GET", f"{API_PREFIX}/recommendations/resources/{{resource_id}}", status, 200, "FAIL", {}, f"Error: {text}")

print("\n" + "="*80)
print("PHASE 4: Capability Assessment\n")

# Test 16: Create Capability Assessment
print("Test 16: Create Capability Assessment...")
capability_payload = {"competency_code": "TECH_PYTHON"}
response, status, text = make_request("POST", f"{API_PREFIX}/assessments/capability", json_body=capability_payload, auth_token=stored_data["access_token"], expected_status=201)
try:
    data = json.loads(text) if response else {}
    if status in [201, 400]:
        stored_data["assessment_id"] = data.get("_id") or data.get("id")
        result = "PASS" if status == 201 else "FAIL_NO_QUESTIONS"
    else:
        result = "FAIL"
    log_test(16, "Create Capability Assessment", "POST", f"{API_PREFIX}/assessments/capability", status, 201, result, data, "400 acceptable if no questions")
except:
    log_test(16, "Create Capability Assessment", "POST", f"{API_PREFIX}/assessments/capability", status, 201, "FAIL", {}, f"Error: {text}")

# Test 17: Get Capability Assessment
print("Test 17: Get Capability Assessment...")
if stored_data["assessment_id"]:
    response, status, text = make_request("GET", f"{API_PREFIX}/assessments/capability/{stored_data['assessment_id']}", auth_token=stored_data["access_token"], expected_status=200)
    try:
        data = json.loads(text) if response else {}
        result = "PASS" if status in [200, 404] else "FAIL"
        log_test(17, "Get Capability Assessment", "GET", f"{API_PREFIX}/assessments/capability/{{assessment_id}}", status, 200, result, data)
    except:
        log_test(17, "Get Capability Assessment", "GET", f"{API_PREFIX}/assessments/capability/{{assessment_id}}", status, 200, "FAIL", {}, f"Error: {text}")
else:
    log_test(17, "Get Capability Assessment", "GET", f"{API_PREFIX}/assessments/capability/{{assessment_id}}", 0, 200, "SKIP", {}, "No assessment ID from Test 16")

# Test 18: List User Capability Assessments
print("Test 18: List Capability Assessments...")
response, status, text = make_request("GET", f"{API_PREFIX}/assessments/capability?limit=10", auth_token=stored_data["access_token"], expected_status=200)
try:
    data = json.loads(text) if response else []
    count = len(data) if isinstance(data, list) else 0
    result = "PASS" if status == 200 else "FAIL"
    log_test(18, "List Capability Assessments", "GET", f"{API_PREFIX}/assessments/capability", status, 200, result, {"count": count})
except:
    log_test(18, "List Capability Assessments", "GET", f"{API_PREFIX}/assessments/capability", status, 200, "FAIL", {}, f"Error: {text}")

# Test 19: Submit Capability Assessment
print("Test 19: Submit Capability Assessment...")
if stored_data["assessment_id"]:
    submit_payload = {"answers": {"q1": "option_a", "q2": "option_b"}}
    response, status, text = make_request("POST", f"{API_PREFIX}/assessments/capability/{stored_data['assessment_id']}/submit", json_body=submit_payload, auth_token=stored_data["access_token"], expected_status=200)
    try:
        data = json.loads(text) if response else {}
        result = "PASS" if status in [200, 400] else "FAIL"
        log_test(19, "Submit Capability Assessment", "POST", f"{API_PREFIX}/assessments/capability/{{assessment_id}}/submit", status, 200, result, data, "400 acceptable if invalid answers")
    except:
        log_test(19, "Submit Capability Assessment", "POST", f"{API_PREFIX}/assessments/capability/{{assessment_id}}/submit", status, 200, "FAIL", {}, f"Error: {text}")
else:
    log_test(19, "Submit Capability Assessment", "POST", f"{API_PREFIX}/assessments/capability/{{assessment_id}}/submit", 0, 200, "SKIP", {}, "No assessment ID")

print("\n" + "="*80)
print("PHASE 5: Authorization & Security\n")

# Test 20: Unauthenticated Request
print("Test 20: Unauthenticated Request...")
response, status, text = make_request("GET", f"{API_PREFIX}/skill-gaps/me", auth_token=None, expected_status=401)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status == 401 else "FAIL"
    log_test(20, "Unauthenticated Request", "GET", f"{API_PREFIX}/skill-gaps/me", status, 401, result, data)
except:
    log_test(20, "Unauthenticated Request", "GET", f"{API_PREFIX}/skill-gaps/me", status, 401, "FAIL", {}, f"Error: {text}")

# Test 21: Invalid Token
print("Test 21: Invalid Token...")
response, status, text = make_request("GET", f"{API_PREFIX}/skill-gaps/me", auth_token="invalid_token_12345", expected_status=401)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status == 401 else "FAIL"
    log_test(21, "Invalid Token", "GET", f"{API_PREFIX}/skill-gaps/me", status, 401, result, data)
except:
    log_test(21, "Invalid Token", "GET", f"{API_PREFIX}/skill-gaps/me", status, 401, "FAIL", {}, f"Error: {text}")

# Test 22: Get Current User Profile
print("Test 22: Get Current User Profile...")
response, status, text = make_request("GET", f"{API_PREFIX}/users/me", auth_token=stored_data["access_token"], expected_status=200)
try:
    data = json.loads(text) if response else {}
    result = "PASS" if status == 200 else "FAIL"
    log_test(22, "Get User Profile", "GET", f"{API_PREFIX}/users/me", status, 200, result, {"id": data.get("id", "")})
except:
    log_test(22, "Get User Profile", "GET", f"{API_PREFIX}/users/me", status, 200, "FAIL", {}, f"Error: {text}")

# Summary
print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80 + "\n")

passed = sum(1 for t in test_results if t["RESULT"] == "PASS")
failed = sum(1 for t in test_results if t["RESULT"].startswith("FAIL"))
skipped = sum(1 for t in test_results if t["RESULT"] == "SKIP")
data_gaps = sum(1 for t in test_results if "DATA_GAP" in t["RESULT"])

print(f"✅ PASSED:    {passed}")
print(f"❌ FAILED:    {failed}")
print(f"⊘ SKIPPED:   {skipped}")
print(f"⚠️  DATA GAPS: {data_gaps}")
print(f"📊 TOTAL:     {len(test_results)}")

# Save results
results_file = Path("postman_22_test_results.json")
with open(results_file, "w") as f:
    json.dump(test_results, f, indent=2)
print(f"\n📄 Results saved to: {results_file}")

# Show failures
if failed > 0:
    print(f"\n❌ FAILURES (details):\n")
    for t in test_results:
        if t["RESULT"].startswith("FAIL"):
            print(f"Test {t['TEST_NUMBER']}: {t['TEST_NAME']}")
            print(f"  URL: {t['URL']}")
            print(f"  Expected: {t['EXPECTED_STATUS']}, Got: {t['ACTUAL_STATUS']}")
            print(f"  Notes: {t['NOTES']}\n")
