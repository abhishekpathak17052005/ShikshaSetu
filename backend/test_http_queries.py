#!/usr/bin/env python3
"""Test if HTTP endpoints work with current mappings"""

import requests
import json
from pymongo import MongoClient
from bson import ObjectId
from app.core.config import get_settings

BASE = "http://127.0.0.1:8001/api/v1"

# First register and login
settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

# Get a role
role = database.roles.find_one({})
role_id = str(role["_id"])

print("\n" + "="*100)
print("TESTING HTTP ENDPOINTS WITH SEEDED MAPPINGS")
print("="*100)

# Register a test user
email = "test_mapping_verify@example.com"
password = "TestMapping123!"

print(f"\n1. Register user...")
resp = requests.post(f"{BASE}/auth/register", json={
    "email": email,
    "password": password,
    "full_name": "Test Mapping",
    "role_id": role_id,
    "designation": "Tester",
    "department": "QA",
    "employee_id": "TEST_MAP_001"
})
print(f"   Status: {resp.status_code}")
if resp.status_code == 201:
    user_id = resp.json()["id"]
    print(f"   User ID: {user_id}")
else:
    print(f"   Error: {resp.text}")
    exit(1)

# Login
print(f"\n2. Login...")
resp = requests.post(f"{BASE}/auth/login", json={
    "email": email,
    "password": password
})
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    token = resp.json()["access_token"]
    print(f"   Token obtained")
else:
    print(f"   Error: {resp.text}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Test competencies
print(f"\n3. GET /competencies")
resp = requests.get(f"{BASE}/competencies", headers=headers)
print(f"   Status: {resp.status_code}")
comp_count = len(resp.json()) if resp.status_code == 200 else 0
print(f"   Count: {comp_count}")

# Test skill gaps
print(f"\n4. GET /skill-gaps/me")
resp = requests.get(f"{BASE}/skill-gaps/me", headers=headers)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    gaps = resp.json().get("gaps", [])
    print(f"   Gaps: {len(gaps)}")
else:
    print(f"   Error: {resp.json()}")

# Test recommendations
print(f"\n5. GET /recommendations/me")
resp = requests.get(f"{BASE}/recommendations/me", headers=headers)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    rec_count = data.get("total_recommendations", 0)
    print(f"   Recommendations: {rec_count}")
    if rec_count > 0:
        top_rec = data["recommendations"][0]
        print(f"   Top recommendation:")
        print(f"     Resource: {top_rec['resource']['resource_id'][:50]}")
        print(f"     Competency: {top_rec['competency_code']}")
        print(f"     Score: {top_rec['score']:.3f}")
        print(f"   ✓ MAPPINGS WORKING - Resources found and recommendations generated!")
    else:
        print(f"   No recommendations (may be expected if role has no gaps)")
else:
    print(f"   Error: {resp.json()}")

client.close()

print(f"\n{'='*100}\n")
