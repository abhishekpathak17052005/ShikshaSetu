#!/usr/bin/env python3
"""Investigate Test 4 and Test 11 failures"""

import requests
import json

print("="*100)
print("INVESTIGATION: Test 4 and Test 11 Failures")
print("="*100)

# Test 4: Check if assessment configs exist at all
print("\nTest 4: Assessment Configuration")
print("-"*100)

# First, get a token
email = "investigator@test.com"
password = "Test123!"
role_id = None

# Get role
resp = requests.get("http://127.0.0.1:8001/api/v1/roles")
if resp.status_code == 200:
    role_id = resp.json()[0].get("id")
    print(f"Role ID: {role_id}")

# Register
register_resp = requests.post("http://127.0.0.1:8001/api/v1/auth/register", json={
    "email": email,
    "password": password,
    "full_name": "Investigator",
    "role_id": role_id,
    "designation": "Test",
    "department": "Test",
    "employee_id": "INVESTIGATOR"
}, timeout=5)

# Login
login_resp = requests.post("http://127.0.0.1:8001/api/v1/auth/login", json={
    "email": email,
    "password": password
}, timeout=5)

token = login_resp.json().get("access_token") if login_resp.status_code == 200 else None
headers = {"Authorization": f"Bearer {token}"}

print(f"\nToken obtained: {token[:20]}..." if token else "No token")

# Check what configs exist
print("\nGET /api/v1/assessments/configs (list all)")
configs_resp = requests.get("http://127.0.0.1:8001/api/v1/assessments/configs", headers=headers)
print(f"Status: {configs_resp.status_code}")
if configs_resp.status_code == 200:
    configs = configs_resp.json()
    print(f"Total configs: {len(configs)}")
    if configs:
        print("\nFirst 5 configs:")
        for i, c in enumerate(configs[:5]):
            code = c.get("competency_code") or c.get("code")
            print(f"  {i+1}. {code}")
            if i == 0:
                print(f"     Keys: {list(c.keys())}")
else:
    print(f"Response: {configs_resp.text[:200]}")

# Check specific competency from Test 3
print("\nGET /api/v1/competencies (list all competencies)")
comp_resp = requests.get("http://127.0.0.1:8001/api/v1/competencies")
print(f"Status: {comp_resp.status_code}")
if comp_resp.status_code == 200:
    comps = comp_resp.json()
    print(f"Total competencies: {len(comps)}")
    if comps:
        test_comp = comps[0].get("code") or comps[0].get("id")
        print(f"\nUsing competency: {test_comp}")
        
        # Try to get assessment config for this competency
        config_resp = requests.get(f"http://127.0.0.1:8001/api/v1/assessments/configs/{test_comp}", headers=headers)
        print(f"\nGET /api/v1/assessments/configs/{test_comp}")
        print(f"Status: {config_resp.status_code}")
        if config_resp.status_code == 200:
            print("✅ Config found")
            config = config_resp.json()
            print(f"Config keys: {list(config.keys())}")
        else:
            print(f"Response: {config_resp.text[:200]}")

# Test 11: Check upload endpoint details
print("\n" + "="*100)
print("Test 11: Material Upload")
print("-"*100)

print("\nPOST /api/v1/learning-materials/upload (with file)")
with open("test_upload.txt", "w") as f:
    f.write("Test content")

with open("test_upload.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    upload_resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )

print(f"Status: {upload_resp.status_code}")
print(f"Response: {upload_resp.json() if upload_resp.text else 'empty'}")

import os
os.remove("test_upload.txt")

print("\n" + "="*100)
