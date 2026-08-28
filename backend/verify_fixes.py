#!/usr/bin/env python3
"""Verify both fixes work"""

import requests
import json

print("="*100)
print("VERIFYING FIXES")
print("="*100)

base = "http://127.0.0.1:8001/api/v1"

# Get auth
print("\n[SETUP] Obtaining authentication token...")
resp_roles = requests.get(f"{base}/roles")
role_id = resp_roles.json()[0].get("id")

resp_reg = requests.post(f"{base}/auth/register", json={
    "email": f"verify_fixes@test.com",
    "password": "VerifyFixes123!",
    "full_name": "Verify Fixes",
    "role_id": role_id,
    "designation": "Test",
    "department": "Test",
    "employee_id": "VERIFY_FIXES"
})

resp_login = requests.post(f"{base}/auth/login", json={
    "email": f"verify_fixes@test.com",
    "password": "VerifyFixes123!"
})

token = resp_login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print(f"Token: {token[:30]}...")

# TEST 4 FIX VERIFICATION
print("\n" + "="*100)
print("TEST 4: Assessment Configuration (FIX 1)")
print("="*100)

# Check if BEH_CHANGE_MANAGEMENT is in seeded configs
print("\nGET /api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT")
resp = requests.get(f"{base}/assessments/configs/BEH_CHANGE_MANAGEMENT", headers=headers)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    print("✅ TEST 4 FIX VERIFIED - Configuration found")
    config = resp.json()
    print(f"   Competency: {config.get('competency_code')}")
    print(f"   Questions: {config.get('number_of_questions')}")
else:
    print(f"❌ TEST 4 STILL BLOCKED - {resp.json()}")

# TEST 11 FIX VERIFICATION
print("\n" + "="*100)
print("TEST 11: Material Upload (FIX 2)")
print("="*100)

print("\nPOST /api/v1/learning-materials/upload (with file only)")

with open("verify_test.txt", "w") as f:
    f.write("Verification test content")

with open("verify_test.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    resp = requests.post(
        f"{base}/learning-materials/upload",
        files=files,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")

if resp.status_code in [200, 201]:
    print("✅ TEST 11 FIX VERIFIED - Upload accepted")
    result = resp.json()
    print(f"   Material ID: {result.get('material_id')}")
    print(f"   Status: {result.get('status')}")
elif resp.status_code == 422:
    detail = resp.json().get('detail', [{}])[0]
    if detail.get('loc') == ['body', 'scope']:
        print(f"❌ TEST 11 STILL BLOCKED - scope parameter still required")
    else:
        print(f"❌ TEST 11 - Different validation error: {detail}")
else:
    print(f"❌ Unexpected status: {resp.status_code}")
    print(f"   Response: {resp.json()}")

import os
os.remove("verify_test.txt")

print("\n" + "="*100)
print("VERIFICATION COMPLETE")
print("="*100)
