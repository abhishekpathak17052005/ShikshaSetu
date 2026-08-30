#!/usr/bin/env python3
import requests
import json

API_PREFIX = 'http://localhost:8001/api/v1'

print("=" * 60)
print("DEFECT 1 DIAGNOSIS: Test 5 — GET /assessments/configs")
print("=" * 60)

# Test 5: GET /assessments/configs (should be public, no auth required)
try:
    print("\n1. Testing WITHOUT authentication:")
    response = requests.get(f'{API_PREFIX}/assessments/configs', timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Data count: {len(data) if isinstance(data, list) else 'N/A'}")
        print("\n   RESULT: PASS - Endpoint is public")
    elif response.status_code == 401:
        print("\n   RESULT: FAIL - Endpoint requires authentication (should be public)")
    else:
        print(f"\n   RESULT: FAIL - Unexpected status code")
        
except Exception as e:
    print(f"   Error: {str(e)}")

print("\n" + "=" * 60)
