#!/usr/bin/env python3
import requests

# Direct HTTP request to the running server
resp = requests.get('http://localhost:8001/api/v1/assessments/configs')
print(f'Status: {resp.status_code}')
print(f'Response: {resp.json()}')

# Try with debug enabled
import sys
print("\n" + "=" * 60, file=sys.stderr)
print("Checking all routes:", file=sys.stderr)

from app.main import app
for route in app.routes:
    path_str = str(route.path) if hasattr(route, 'path') else ''
    if 'configs' in path_str:
        print(f"Found route: {route}", file=sys.stderr)
        print(f"  Path: {path_str}", file=sys.stderr)
        if hasattr(route, 'endpoint'):
            print(f"  Endpoint: {route.endpoint}", file=sys.stderr)
            print(f"  Endpoint module: {route.endpoint.__module__}", file=sys.stderr)
