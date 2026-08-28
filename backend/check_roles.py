#!/usr/bin/env python
"""Check existing roles in database."""

from app.core.database import initialize_database
from app.core.config import Settings

settings = Settings()
client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)

try:
    roles = list(db.roles.find({}, {'_id': 1, 'name': 1, 'status': 1}))
    print(f"Roles in database: {len(roles)}")
    for role in roles[:10]:
        print(f"  - ID: {role.get('_id')} | Name: {role.get('name')} | Status: {role.get('status')}")
    
    if len(roles) == 0:
        print("\nNo roles found! Need to create one for testing.")
        print("\nCreating a test role...")
        
        from bson import ObjectId
        test_role_id = ObjectId()
        db.roles.insert_one({
            "_id": test_role_id,
            "name": "Test Statistical Officer",
            "description": "Test role for E2E testing",
            "status": "active",
            "competency_requirements": [
                {
                    "competency_code": "STAT-SAMPLING",
                    "required_level": 3,
                }
            ],
        })
        
        print(f"Created role: {test_role_id}")
        print(f"Use this ID for tests: '{str(test_role_id)}'")

finally:
    client.close()
