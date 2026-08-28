#!/usr/bin/env python3
"""Test if scope needs to be a dictionary/JSON object"""

import requests
import json

print("="*100)
print("TEST: scope as empty dict or JSON object")
print("="*100)

# Get token
resp_roles = requests.get("http://127.0.0.1:8001/api/v1/roles")
role_id = resp_roles.json()[0].get("id")

requests.post("http://127.0.0.1:8001/api/v1/auth/register", json={
    "email": "dict_test@test.com",
    "password": "Test123!",
    "full_name": "Dict Test",
    "role_id": role_id,
    "designation": "Test",
    "department": "Test",
    "employee_id": "DICT_TEST"
})

resp_login = requests.post("http://127.0.0.1:8001/api/v1/auth/login", json={
    "email": "dict_test@test.com",
    "password": "Test123!"
})

token = resp_login.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Test 1: scope as empty dict {}
print("\n[TEST 1] scope as empty dict {}")
print("-"*100)

with open("test_file.txt", "w") as f:
    f.write("Test content")

with open("test_file.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    data = {"scope": json.dumps({})}  # JSON object as string
    resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload",
        files=files,
        data=data,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")
print(f"Response: {resp.json() if resp.text else 'empty'}")

# Test 2: Try with query parameter instead
print("\n[TEST 2] scope as query parameter")
print("-"*100)

with open("test_file.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload?scope=general",
        files=files,
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")
print(f"Response: {resp.json() if resp.text else 'empty'}")

# Test 3: Try JSON body with file as multipart (this doesn't make sense but let's try)
print("\n[TEST 3] scope as query + file multipart")
print("-"*100)

with open("test_file.txt", "rb") as f:
    files = {"file": ("test.txt", f)}
    resp = requests.post(
        "http://127.0.0.1:8001/api/v1/learning-materials/upload",
        files=files,
        params={"scope": {}},
        headers=headers,
        timeout=10
    )

print(f"Status: {resp.status_code}")
print(f"Response: {resp.json() if resp.text else 'empty'}")

import os
os.remove("test_file.txt")

print("\n" + "="*100)
