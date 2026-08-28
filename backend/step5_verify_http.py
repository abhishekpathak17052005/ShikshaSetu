#!/usr/bin/env python3
"""STEP 5: Verify HTTP endpoints see the seeded data"""

import requests
import json

BASE = "http://127.0.0.1:8001/api/v1"

print("\n" + "="*100)
print("STEP 5: HTTP ENDPOINT VERIFICATION")
print("="*100)

# Note: These are unauthenticated reads - no auth needed
# Register a user first to test authenticated endpoints
email = "http_verify@example.com"
password = "HttpVerify123!"

# Get role
print(f"\n1. GET /roles")
resp = requests.get(f"{BASE}/roles", timeout=10)
roles = resp.json() if resp.status_code == 200 else []
print(f"   Status: {resp.status_code}")
print(f"   Roles returned: {len(roles)}")
if roles:
    role_id = roles[0]["id"]
    print(f"   First role: {roles[0].get('role_name')} (ID: {role_id[:12]}...)")

# Register test user
print(f"\n2. POST /auth/register")
resp = requests.post(f"{BASE}/auth/register", json={
    "email": email,
    "password": password,
    "full_name": "HTTP Verify User",
    "role_id": role_id,
    "designation": "Verifier",
    "department": "QA",
    "employee_id": "HTTP_VERIFY_001"
}, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 201:
    user_data = resp.json()
    user_id = user_data["id"]
    print(f"   User created: {user_data.get('email')}")

# Login
print(f"\n3. POST /auth/login")
resp = requests.post(f"{BASE}/auth/login", json={
    "email": email,
    "password": password
}, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    login_data = resp.json()
    token = login_data.get("access_token")
    print(f"   Token obtained: {token[:30]}...")

headers = {"Authorization": f"Bearer {token}"}

# Test 1: GET /competencies
print(f"\n4. GET /competencies (with auth)")
resp = requests.get(f"{BASE}/competencies", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    comps = resp.json()
    print(f"   Competencies returned: {len(comps)}")
    if comps:
        print(f"   First competency: {comps[0].get('code')} - {comps[0].get('name')}")

# Test 2: GET /skill-gaps/me
print(f"\n5. GET /skill-gaps/me (with auth)")
resp = requests.get(f"{BASE}/skill-gaps/me", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    gaps_data = resp.json()
    gaps = gaps_data.get("gaps", [])
    print(f"   Skill gaps identified: {len(gaps)}")
    if gaps:
        print(f"   Gap example: {gaps[0].get('competency_code')} (priority: {gaps[0].get('priority_score'):.2f})")

# Test 3: GET /recommendations/me
print(f"\n6. GET /recommendations/me (with auth)")
resp = requests.get(f"{BASE}/recommendations/me", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    rec_data = resp.json()
    rec_count = rec_data.get("total_recommendations", 0)
    print(f"   Recommendations generated: {rec_count}")
    if rec_count > 0:
        top_rec = rec_data["recommendations"][0]
        print(f"   Top recommendation:")
        print(f"     Resource: {top_rec['resource']['resource_id']}")
        print(f"     Provider: {top_rec['provider']}")
        print(f"     Score: {top_rec['score']:.3f}")

print(f"\n" + "="*100)
print("✓ HTTP ENDPOINT VERIFICATION COMPLETE")
print("="*100 + "\n")
