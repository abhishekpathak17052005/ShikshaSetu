#!/usr/bin/env python
"""Debug registration endpoint."""

from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import get_settings
from app.core.database import initialize_database

settings = get_settings()
client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)

try:
    app = create_app(settings)
    app.state.database = db
    test_client = TestClient(app)

    # Try registration
    register_payload = {
        'email': 'e2e_test@example.com',
        'password': 'TestPassword123!',
        'full_name': 'E2E Test User',
        'designation': 'Statistical Officer',
        'department': 'Testing',
        'employee_id': 'E2E001',
        'role_id': '6a8fe8048524f6da8ebb9881',  # Existing role from database
    }

    print("=" * 70)
    print("REGISTRATION ENDPOINT TEST")
    print("=" * 70)
    print(f"\nPayload:")
    import json
    print(json.dumps(register_payload, indent=2))

    response = test_client.post('/api/v1/auth/register', json=register_payload)
    
    print(f"\nHTTP Status: {response.status_code}")
    print(f"\nResponse:")
    print(response.text)
    
    if response.status_code == 422:
        print("\n" + "=" * 70)
        print("VALIDATION ERROR DETAILS:")
        print("=" * 70)
        try:
            error_data = response.json()
            print(json.dumps(error_data, indent=2))
        except:
            print(response.text)

finally:
    client.close()
