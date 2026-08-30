#!/usr/bin/env python3
"""Final verification that both fixes work"""

import requests
import sys

base = "http://127.0.0.1:8001/api/v1"

print("FINAL FIX VERIFICATION")
print("="*80)

# Get auth
resp_roles = requests.get(f"{base}/roles")
role_id = resp_roles.json()[0].get("id")

requests.post(f"{base}/auth/register", json={
    "email": f"final_verify@test.com",
    "password": "FinalVerify123!",
    "full_name": "Final Verify",
    "role_id": role_id,
    "designation": "Test",
    "department": "Test",
    "employee_id": "FINAL_VERIFY"
})

resp_login = requests.post(f"{base}/auth/login", json={
    "email": f"final_verify@test.com",
    "password": "FinalVerify123!"
})

token = resp_login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# TEST 4 FIX: Assessment configuration for competency that HAS a config
print("\nTEST 4 FIX - Assessment Configuration")
print("-"*80)
print("GET /api/v1/assessments/configs/BEH_LEADERSHIP")
resp = requests.get(f"{base}/assessments/configs/BEH_LEADERSHIP", headers=headers)
if resp.status_code == 200:
    print("PASS - Assessment config found")
    print(f"  Status Code: {resp.status_code}")
    print(f"  Competency: {resp.json().get('competency_code')}")
else:
    print(f"FAIL - Status {resp.status_code}: {resp.json()}")
    sys.exit(1)

# TEST 11 FIX: Material upload without scope parameter
print("\nTEST 11 FIX - Material Upload")
print("-"*80)
print("POST /api/v1/learning-materials/upload (file only, no scope)")

with open("final_test.pdf", "wb") as f:
    f.write(b"%PDF-1.4\n%minimal PDF")

with open("final_test.pdf", "rb") as f:
    files = {"file": ("test.pdf", f)}
    resp = requests.post(
        f"{base}/learning-materials/upload",
        files=files,
        headers=headers,
        timeout=10
    )

if resp.status_code in [200, 201]:
    print("PASS - Upload accepted without scope parameter")
    print(f"  Status Code: {resp.status_code}")
    print(f"  Material ID: {resp.json().get('material_id', 'N/A')}")
elif resp.status_code == 422:
    detail = resp.json().get('detail', [{}])[0]
    if detail.get('loc') == ['body', 'scope']:
        print(f"FAIL - scope parameter still required")
        sys.exit(1)
    else:
        print(f"FAIL - Different validation error: {detail}")
        sys.exit(1)
else:
    print(f"FAIL - Status {resp.status_code}: {resp.json()}")
    sys.exit(1)

import os
if os.path.exists("final_test.pdf"):
    os.remove("final_test.pdf")

print("\n" + "="*80)
print("SUCCESS: Both fixes verified")
print("="*80)
