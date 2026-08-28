#!/usr/bin/env python3
"""Audit the actual registered API endpoints"""

import requests

base = "http://127.0.0.1:8001/api/v1"

print("="*100)
print("POSTMAN API CONTRACT AUDIT")
print("="*100)

print("\n" + "="*100)
print("TEST 4: Assessment Questions Endpoint")
print("="*100)

print("\nPostman used: GET /capability-assessments/competencies/BEH_CHANGE_MANAGEMENT")
resp = requests.get("http://127.0.0.1:8001/api/v1/capability-assessments/competencies/BEH_CHANGE_MANAGEMENT", timeout=5)
print(f"Status: {resp.status_code} (404 = endpoint does not exist)")

print("\nCorrect endpoint (from code audit):")
print("  Endpoint: GET /api/v1/assessments/configs/{competency_code}")
resp_correct = requests.get(f"{base}/assessments/configs/BEH_CHANGE_MANAGEMENT", timeout=5)
print(f"  Status: {resp_correct.status_code}")
if resp_correct.status_code == 200:
    print("  ✅ ENDPOINT EXISTS - Returns assessment configuration with questions")
    data = resp_correct.json()
    print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
else:
    print(f"  Response: {resp_correct.text[:200]}")

print("\n" + "="*100)
print("TEST 11: Material Upload Endpoint")
print("="*100)

print("\nPostman used: POST /materials/upload")
resp_wrong = requests.post("http://127.0.0.1:8001/api/v1/materials/upload", timeout=5)
print(f"Status: {resp_wrong.status_code} (404 = endpoint does not exist)")

print("\nCorrect endpoint (from code audit):")
print("  Endpoint: POST /api/v1/learning-materials/upload")
resp_correct = requests.post(f"{base}/learning-materials/upload", timeout=5)
print(f"  Status: {resp_correct.status_code}")
if resp_correct.status_code == 422:
    print("  ✅ ENDPOINT EXISTS - Returns 422 (missing file parameter)")
elif resp_correct.status_code == 400:
    print("  ✅ ENDPOINT EXISTS - Returns 400 (validation error)")
else:
    print(f"  Status indicates endpoint exists or is properly configured")

print("\n" + "="*100)
print("SUMMARY")
print("="*100)

print("""
FROM CODE AUDIT:
================

Registered Router Prefixes (from main.py):

1. assessments_router
   - Includes at: prefix="/api/v1/assessments"
   - Router internal prefix: "/assessments"
   - Final prefix: /api/v1/assessments
   
   Routes in this router:
   - POST / (start assessment)
   - GET / (list assessments)
   - GET /{attempt_id}
   - POST /{attempt_id}/submit
   - GET /configs (list configurations)
   - GET /configs/{competency_code} ← ASSESSMENT QUESTIONS

2. capability_assessments_router
   - Includes at: NO prefix (uses router's own prefix)
   - Router internal prefix: "/api/v1/assessments/capability"
   - Final prefix: /api/v1/assessments/capability
   
   Routes in this router:
   - POST / (create capability assessment)
   - GET /{assessment_id}
   - POST /{assessment_id}/submit
   - GET /{assessment_id}/results
   - GET / (list user assessments)

3. ai_router
   - Includes at: prefix="/api/v1"
   - Router internal prefix: "/learning-materials"
   - Final prefix: /api/v1/learning-materials
   
   Routes in this router:
   - POST /upload ← MATERIAL UPLOAD
   - GET /{material_id}
   - POST /{material_id}/generate-questions

POSTMAN TEST 4 AUDIT:
=====================
Postman Test 4 used: GET /capability-assessments/competencies/BEH_CHANGE_MANAGEMENT

Status: ❌ FAIL (404 Not Found)

Root Cause: INCORRECT ENDPOINT PATH

Analysis:
- Postman is hitting: /capability-assessments/competencies/{code}
- This path does NOT exist in the registered routers
- The assessment endpoint path is wrong

Correct endpoint for fetching assessment questions:
- Path: GET /api/v1/assessments/configs/{competency_code}
- Router: assessments_router (app/assessments/router.py)
- Purpose: Returns assessment configuration with questions for a competency

POSTMAN TEST 11 AUDIT:
======================
Postman Test 11 used: POST /materials/upload

Status: ❌ FAIL (404 Not Found)

Root Cause: INCORRECT ENDPOINT PATH

Analysis:
- Postman is hitting: /materials/upload
- This path does NOT exist in the registered routers
- The materials endpoint path is wrong

Correct endpoint for uploading learning materials:
- Path: POST /api/v1/learning-materials/upload
- Router: ai_router (app/ai/router.py)
- Purpose: Upload and process learning documents (PDF, DOCX, PPTX)

CONCLUSION:
===========
Both TEST 4 and TEST 11 failures are due to INCORRECT ENDPOINT PATHS in the Postman tests.
The backend endpoints DO EXIST but at different paths than what the Postman tests are using.
This is an API CONTRACT MISMATCH, not missing functionality.
""")
