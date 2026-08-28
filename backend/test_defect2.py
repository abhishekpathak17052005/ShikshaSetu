#!/usr/bin/env python3
import requests
import json

API_PREFIX = 'http://localhost:8001/api/v1'

print("=" * 60)
print("DEFECT 2 DIAGNOSIS: Test 6 — GET /competencies")
print("=" * 60)

try:
    print("\n1. Testing GET /competencies:")
    response = requests.get(f'{API_PREFIX}/competencies', timeout=5)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Data count: {len(data) if isinstance(data, list) else 'N/A'}")
        print("\n   RESULT: PASS - Endpoint works")
    elif response.status_code == 500:
        print(f"   Response: {response.text[:800]}")
        print("\n   RESULT: FAIL - Internal Server Error (500)")
    else:
        print(f"   Response: {response.text[:200]}")
        print(f"\n   RESULT: FAIL - Status {response.status_code}")
        
except Exception as e:
    print(f"   Error: {str(e)}")

print("\n" + "=" * 60)
