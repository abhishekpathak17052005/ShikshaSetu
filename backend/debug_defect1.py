#!/usr/bin/env python3
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=" * 60)
print("DEBUG: Checking route dependencies")
print("=" * 60)

# Find the /configs route
for route in app.routes:
    if hasattr(route, 'path') and 'configs' in str(route.path):
        print(f"\nRoute: {route.path}")
        print(f"Methods: {route.methods if hasattr(route, 'methods') else 'N/A'}")
        if hasattr(route, 'dependant'):
            print(f"Dependencies: {route.dependant.dependencies if hasattr(route.dependant, 'dependencies') else 'None'}")
        if hasattr(route, 'endpoint'):
            print(f"Endpoint: {route.endpoint.__name__}")

print("\n" + "=" * 60)
print("TEST: Direct request to /configs")
print("=" * 60)

response = client.get("/api/v1/assessments/configs")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
