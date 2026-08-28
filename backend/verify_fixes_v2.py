#!/usr/bin/env python3
"""Verify both fixes work - V2 with PDF"""

import requests
import json

print("="*100)
print("VERIFYING FIXES V2")
print("="*100)

base = "http://127.0.0.1:8001/api/v1"

# Get auth
print("\n[SETUP] Obtaining authentication token...")
resp_roles = requests.get(f"{base}/roles")
role_id = resp_roles.json()[0].get("id")

resp_reg = requests.post(f"{base}/auth/register", json={
    "email": f"verify_fixes_v2@test.com",
    "password": "VerifyFixesV2123!",
    "full_name": "Verify Fixes V2",
    "role_id": role_id,
    "designation": "Test",
    "department": "Test",
    "employee_id": "VERIFY_FIXES_V2"
})

resp_login = requests.post(f"{base}/auth/login", json={
    "email": f"verify_fixes_v2@test.com",
    "password": "VerifyFixesV2123!"
})

token = resp_login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print(f"Token: {token[:30]}...")

# TEST 4 FIX VERIFICATION
print("\n" + "="*100)
print("TEST 4: Assessment Configuration (FIX 1)")
print("="*100)

print("\nGET /api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT")
resp = requests.get(f"{base}/assessments/configs/BEH_CHANGE_MANAGEMENT", headers=headers)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    print("✅ TEST 4 FIX VERIFIED - Configuration found")
    config = resp.json()
    print(f"   Competency: {config.get('competency_code')}")
    print(f"   Questions: {config.get('number_of_questions')}")
elif resp.status_code == 404:
    print(f"❌ TEST 4 STILL BLOCKED - {resp.json()}")
    print("\n   Debugging: Check available configs...")
    resp_all = requests.get(f"{base}/assessments/configs", headers=headers)
    if resp_all.status_code == 200:
        configs = resp_all.json()
        print(f"   Total configs in DB: {len(configs)}")
        if configs:
            print(f"   Sample codes: {[c.get('competency_code') for c in configs[:3]]}")
    else:
        print(f"   Cannot list configs: {resp_all.status_code}")

# TEST 11 FIX VERIFICATION
print("\n" + "="*100)
print("TEST 11: Material Upload (FIX 2)")
print("="*100)

print("\nPOST /api/v1/learning-materials/upload (with PDF file)")

# Create a minimal valid PDF
with open("verify_test.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>endobj 4 0 obj<</Length 0>>stream\nendstream endobj xref 0 5 0000000000 65535 f 0000000009 00000 n 0000000058 00000 n 0000000115 00000 n 0000000231 00000 n trailer<</Size 5/Root 1 0 R>>startxref 282\n%%EOF")

with open("verify_test.pdf", "rb") as f:
    files = {"file": ("test.pdf", f)}
    resp = requests.post(
        f"{base}/learning-materials/upload",
        files=files,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")

if resp.status_code in [200, 201]:
    print("✅ TEST 11 FIX VERIFIED - Upload accepted (no scope parameter required)")
    result = resp.json()
    print(f"   Material ID: {result.get('material_id')}")
    print(f"   Status: {result.get('status')}")
elif resp.status_code == 422:
    detail = resp.json().get('detail', [{}])[0]
    if detail.get('loc') == ['body', 'scope']:
        print(f"❌ TEST 11 STILL BLOCKED - scope parameter still required")
        print(f"   Error: {detail}")
    else:
        print(f"❌ TEST 11 - Different validation error: {detail}")
else:
    print(f"❌ Unexpected status: {resp.status_code}")
    print(f"   Response: {resp.json()}")

import os
if os.path.exists("verify_test.pdf"):
    os.remove("verify_test.pdf")

print("\n" + "="*100)
print("VERIFICATION COMPLETE")
print("="*100)
