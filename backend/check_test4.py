#!/usr/bin/env python3
"""Check Test 4 endpoint"""

import requests

# Test 4 investigation
print('TEST 4 INVESTIGATION - Assessment Config vs Data')
print('='*80)

# Check the specific endpoint used in Test 4
resp = requests.get('http://127.0.0.1:8001/api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT', timeout=5)
print(f'Endpoint: GET /api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT')
print(f'Status: {resp.status_code}')
print(f'Response: {resp.json()}')
print()

# Check what configs exist
print('Checking available assessment configs:')
resp = requests.get('http://127.0.0.1:8001/api/v1/assessments/configs', timeout=5)
print(f'GET /api/v1/assessments/configs')
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    configs = resp.json()
    print(f'Number of configs: {len(configs)}')
    if configs:
        print(f'\nFirst config:')
        print(f'  Code/ID: {configs[0].get("competency_code") or configs[0].get("code")}')
        print(f'  Keys: {list(configs[0].keys())}')
        print(f'\nAll config codes:')
        for c in configs:
            code = c.get('competency_code') or c.get('code')
            print(f'  - {code}')
