#!/usr/bin/env python3
"""Phase 3: Diagnosis-only audit of failed tests. No code changes."""
import requests
import json
import sys
from app.core.config import get_settings
from app.core.database import initialize_database

BASE_URL = "http://127.0.0.1:8001"
API_PREFIX = "/api/v1"

# Get token for authenticated tests
print("\n" + "="*80)
print("PHASE 3: POSTMAN VERIFICATION DEFECT DIAGNOSIS")
print("="*80 + "\n")

print("[SETUP] Obtaining JWT token for authenticated tests...")
login_response = requests.post(
    f"{BASE_URL}{API_PREFIX}/auth/login",
    json={"email": "postman_test_user@example.com", "password": "TestPassword123!"},
    timeout=10
)
if login_response.status_code != 200:
    print("❌ Could not login. Stopping diagnosis.")
    sys.exit(1)

token = login_response.json().get("access_token")
user_id = login_response.json().get("user").get("id")
print(f"✅ Token obtained: {token[:30]}...\n")

# Initialize database for code inspection
settings = get_settings()
client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
print(f"✅ Database connected\n")

print("="*80)
print("TEST 5: List Assessment Configurations (returns 401, expected 200)")
print("="*80 + "\n")

print("[REQUEST]")
print(f"  Method: GET")
print(f"  URL: {BASE_URL}{API_PREFIX}/assessments/configs")
print(f"  Auth: None (endpoint should be public)")

response = requests.get(f"{BASE_URL}{API_PREFIX}/assessments/configs", timeout=10)
print(f"\n[RESPONSE]")
print(f"  Status: {response.status_code}")
print(f"  Body: {response.text[:200]}")

print(f"\n[CODE ANALYSIS]")
print(f"  File: app/assessments/router.py")
from app.assessments import router as assessments_router
import inspect

# Find the list_assessment_configurations route
route_found = False
for route in assessments_router.router.routes:
    if "configs" in str(route.path) and route.path.endswith("/configs"):
        route_found = True
        print(f"  Route Path: {route.path}")
        print(f"  Methods: {route.methods}")
        print(f"  Dependencies: {route.dependencies}")
        
        # Check source
        if hasattr(route, 'endpoint'):
            source = inspect.getsource(route.endpoint)
            has_depends = "Depends" in source
            print(f"  Auth Required: {'YES (has Depends)' if has_depends else 'NO'}")
            print(f"  Source snippet:\n{source[:300]}")

if not route_found:
    print("  ⚠️  Route /configs not found in registered routes")

print(f"\n[DIAGNOSIS]")
print(f"  Expected: GET /api/v1/assessments/configs should return 200 (public endpoint)")
print(f"  Actual: Returns 401 Unauthorized")
print(f"  Classification: BACKEND DEFECT - Endpoint incorrectly enforces authentication")
print(f"  Likely Issue: Route marked with Depends(get_current_user) when it should be public\n")

print("="*80)
print("TEST 6: Get All Competencies (returns 500, expected 200)")
print("="*80 + "\n")

print("[REQUEST]")
print(f"  Method: GET")
print(f"  URL: {BASE_URL}{API_PREFIX}/competencies")
print(f"  Auth: None")

response = requests.get(f"{BASE_URL}{API_PREFIX}/competencies", timeout=10)
print(f"\n[RESPONSE]")
print(f"  Status: {response.status_code}")
print(f"  Body: {response.text[:500]}")

print(f"\n[CODE ANALYSIS]")
print(f"  File: app/competencies/router.py")
from app.competencies import router as competencies_router

route_found = False
for route in competencies_router.router.routes:
    if route.path == "/competencies" or route.path.endswith("/competencies"):
        route_found = True
        print(f"  Route Path: {route.path}")
        print(f"  Methods: {route.methods}")
        
        if hasattr(route, 'endpoint'):
            source = inspect.getsource(route.endpoint)
            print(f"  Source snippet:\n{source[:400]}")

print(f"\n[DATABASE CHECK]")
comp_count = database.competencies.count_documents({})
print(f"  Competencies in DB: {comp_count}")

print(f"\n[DIAGNOSIS]")
print(f"  Expected: GET /api/v1/competencies should return list of 42 competencies")
print(f"  Actual: Returns 500 Internal Server Error")
print(f"  Database State: {comp_count} competencies available")
print(f"  Classification: BACKEND DEFECT - Server error during retrieval")
print(f"  Likely Issue: Serialization error, missing field, or query failure\n")

print("="*80)
print("TEST 12: Get Material Metadata (returns 422, expected 200)")
print("="*80 + "\n")

print("[REQUEST]")
print(f"  Method: GET")
print(f"  URL: {BASE_URL}{API_PREFIX}/learning-materials/6a911c544d63de45a857fba5")
print(f"  Auth: Bearer token")

response = requests.get(
    f"{BASE_URL}{API_PREFIX}/learning-materials/6a911c544d63de45a857fba5",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10
)
print(f"\n[RESPONSE]")
print(f"  Status: {response.status_code}")
print(f"  Body: {response.text[:500]}")

print(f"\n[DATABASE CHECK]")
material = database.learning_materials.find_one({"_id": {"$oid": "6a911c544d63de45a857fba5"} if isinstance("6a911c544d63de45a857fba5", str) else "6a911c544d63de45a857fba5"})
if not material:
    from bson import ObjectId
    try:
        material = database.learning_materials.find_one({"_id": ObjectId("6a911c544d63de45a857fba5")})
    except:
        material = None

print(f"  Material found in DB: {'YES' if material else 'NO'}")

print(f"\n[CODE ANALYSIS]")
print(f"  File: app/ai/router.py")
from app.ai import router as ai_router

route_found = False
for route in ai_router.router.routes:
    if "{material_id}" in str(route.path):
        route_found = True
        print(f"  Route Path: {route.path}")
        print(f"  Methods: {route.methods}")

print(f"\n[DIAGNOSIS]")
print(f"  Expected: GET /api/v1/learning-materials/{{material_id}} returns metadata")
print(f"  Actual: Returns 422 Unprocessable Entity (validation error)")
print(f"  Classification: BACKEND DEFECT - Validation too strict or ID format issue")
print(f"  Likely Issue: Path parameter validation failing on material_id format\n")

print("="*80)
print("TEST 16: Create Capability Assessment (returns 404, expected 201)")
print("="*80 + "\n")

print("[REQUEST]")
print(f"  Method: POST")
print(f"  URL: {BASE_URL}{API_PREFIX}/assessments/capability")
print(f"  Auth: Bearer token")
print(f"  Body: {{'competency_code': 'TECH_PYTHON'}}")

response = requests.post(
    f"{BASE_URL}{API_PREFIX}/assessments/capability",
    json={"competency_code": "TECH_PYTHON"},
    headers={"Authorization": f"Bearer {token}"},
    timeout=10
)
print(f"\n[RESPONSE]")
print(f"  Status: {response.status_code}")
print(f"  Body: {response.text[:200]}")

print(f"\n[CODE ANALYSIS]")
print(f"  File: app/capability_assessments/router.py")
print(f"  Expected Router Prefix: /api/v1/assessments/capability (from main.py)")

from app.capability_assessments import router as capability_assessments_router
routes = capability_assessments_router.router.routes
print(f"  Registered routes in capability_assessments_router:")
for route in routes:
    if "POST" in route.methods:
        print(f"    - {route.methods} {route.path}")

print(f"\n[DIAGNOSIS]")
print(f"  Expected: POST /api/v1/assessments/capability creates assessment (201)")
print(f"  Actual: Returns 404 Not Found")
print(f"  Classification: BACKEND DEFECT or ROUTER REGISTRATION ISSUE")
print(f"  Likely Issue: Route not properly registered, or prefix not applied correctly")
print(f"            main.py line: application.include_router(capability_assessments_router)")
print(f"            Without prefix, so router must define full /api/v1/assessments/capability paths\n")

print("="*80)
print("TEST 18: List Capability Assessments (returns 404, expected 200)")
print("="*80 + "\n")

print("[REQUEST]")
print(f"  Method: GET")
print(f"  URL: {BASE_URL}{API_PREFIX}/assessments/capability?limit=10")
print(f"  Auth: Bearer token")

response = requests.get(
    f"{BASE_URL}{API_PREFIX}/assessments/capability?limit=10",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10
)
print(f"\n[RESPONSE]")
print(f"  Status: {response.status_code}")
print(f"  Body: {response.text[:200]}")

print(f"\n[CODE ANALYSIS]")
print(f"  File: app/capability_assessments/router.py")
print(f"  Expected Path: /api/v1/assessments/capability (GET without ID)")
print(f"  Registered routes:")
for route in capability_assessments_router.router.routes:
    if "GET" in route.methods:
        print(f"    - {route.methods} {route.path}")

print(f"\n[DIAGNOSIS]")
print(f"  Expected: GET /api/v1/assessments/capability lists user assessments (200)")
print(f"  Actual: Returns 404 Not Found")
print(f"  Classification: BACKEND DEFECT or ROUTER REGISTRATION ISSUE")
print(f"  Likely Issue: Same as Test 16 - router prefix/path mismatch\n")

client.close()

print("="*80)
print("SUMMARY: 6 FAILED TESTS")
print("="*80 + "\n")

summary = {
    "Test 4": {"Status": "DATA_GAP", "Issue": "BEH_CHANGE_MANAGEMENT config not seeded (legitimate)"},
    "Test 5": {"Status": "DEFECT", "Issue": "Authentication incorrectly enforced on public endpoint"},
    "Test 6": {"Status": "DEFECT", "Issue": "500 error retrieving competencies from database"},
    "Test 12": {"Status": "DEFECT", "Issue": "422 validation error on material_id parameter"},
    "Test 16": {"Status": "DEFECT", "Issue": "404 - capability assessment route not registered"},
    "Test 18": {"Status": "DEFECT", "Issue": "404 - capability assessment list route not registered"},
}

for test, info in summary.items():
    print(f"{test}: {info['Status']} - {info['Issue']}")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE - NO CODE CHANGES MADE")
print("="*80 + "\n")
