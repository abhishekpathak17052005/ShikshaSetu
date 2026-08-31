"""Upgrade test user to TRAINER role so upload endpoint works."""
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DATABASE')]

result = db.users.update_one(
    {"email": "ragtester@example.com"},
    {"$set": {"access_role": "TRAINER"}}
)

if result.matched_count == 0:
    print("❌ User not found - creating one...")

    # Get any role_id
    role = db.roles.find_one()
    role_id = str(role["_id"]) if role else None
    if not role_id:
        print("❌ No roles in database")
        exit(1)

    from datetime import datetime
    db.users.insert_one({
        "email": "ragtester@example.com",
        "password_hash": "$2b$12$EXAMPLEHASHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "full_name": "RAG Tester",
        "role_id": role_id,
        "designation": "Tester",
        "department": "Test",
        "employee_id": "RAG001",
        "access_role": "TRAINER",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })
    print("Created new user - but password_hash is invalid, register via API instead.")
else:
    print(f"✅ Updated {result.modified_count} user(s) to TRAINER role")

# Verify
user = db.users.find_one({"email": "ragtester@example.com"})
if user:
    print(f"   email: {user['email']}")
    print(f"   access_role: {user.get('access_role')}")
    print(f"   status: {user.get('status')}")
