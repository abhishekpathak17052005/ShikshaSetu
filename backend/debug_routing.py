#!/usr/bin/env python3
from fastapi import Request
from fastapi.testclient import TestClient
from app.main import app

# Create a test client
client = TestClient(app)

# Monkey-patch to see what's being called
original_app = app

async def debug_middleware(request: Request, call_next):
    print(f"\n>>> Request to: {request.method} {request.url.path}")
    print(f">>> Matched route will be determined by FastAPI routing")
    response = await call_next(request)
    print(f"<<< Response: {response.status_code}")
    return response

# Don't actually add middleware, just make a test request and inspect the route after
print("Making test request to /api/v1/assessments/configs")
response = client.get("/api/v1/assessments/configs")

print(f"\nResponse Status: {response.status_code}")
print(f"Response Body: {response.json()}")

# Now let's trace through the route matching manually
print("\n\nManually checking route matching:")
from starlette.routing import Match, Route

for route in app.routes:
    if hasattr(route, 'path'):
        match, child_scope = route.matches({"type": "http", "method": "GET", "path": "/api/v1/assessments/configs"})
        if match == Match.FULL:
            print(f"MATCHED: {route.path} => {route.endpoint.__name__ if hasattr(route, 'endpoint') else 'N/A'}")
        elif match == Match.PARTIAL:
            print(f"PARTIAL: {route.path}")
