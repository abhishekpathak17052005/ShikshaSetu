#!/usr/bin/env python3
"""Test the upload endpoint to understand the scope parameter"""

import requests
import json

print("="*100)
print("UPLOAD ENDPOINT SCHEMA INSPECTION")
print("="*100)

# First, get auth
print("\n[STEP 1] Obtain authentication token")
resp_roles = requests.get("http://127.0.0.1:8001/api/v1/roles")
role_id = resp_roles.json()[0].get("id")

resp_reg = requests.post("http://127.0.0.1:8001/api/v1/auth/register", json={
    "email": "schema_test@test.com",
    "password": "Test123!",
    "full_name": "Schema Test",
    "role_id": role_id,
    "designation": "Test",
    "department": "Test",
    "employee_id": "SCHEMA_TEST"
})

resp_login = requests.post("http://127.0.0.1:8001/api/v1/auth/login", json={
    "email": "schema_test@test.com",
    "password": "Test123!"
})

token = resp_login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

print(f"Token: {token[:30]}...")

# Test 1: Upload with ONLY file
print("\n[TEST 1] POST with file only (no scope)")
print("-"*100)

with open("test_file.txt", "w") as f:
    f.write("Test content")

with open("test_file.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload",
        files=files,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# Test 2: Upload with file and scope in form data
print("\n[TEST 2] POST with file AND scope in form data")
print("-"*100)

with open("test_file.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    data = {"scope": "general"}
    resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload",
        files=files,
        data=data,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2) if resp.text else 'empty'}")

# Test 3: Check if scope needs to be in JSON body (probably not, but let's try)
print("\n[TEST 3] POST with file (multipart) and scope in JSON body")
print("-"*100)

with open("test_file.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    data = {"scope": "learning_materials"}
    resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload",
        files=files,
        data=data,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2) if resp.text else 'empty'}")

import os
os.remove("test_file.txt")

print("\n" + "="*100)
print("ANALYSIS")
print("="*100)
print("""
The 422 error mentioned 'scope' is required in the 'body'.
This suggests the endpoint may have been updated or the router definition includes
a Pydantic model that requires 'scope' as a form field.

Possibilities:
1. scope is required in multipart form data (alongside file)
2. scope is a query parameter
3. scope was added to a BaseModel but the code still shows old signature
4. This is a mismatch between documentation and implementation

The tests above will help determine which.
""")
