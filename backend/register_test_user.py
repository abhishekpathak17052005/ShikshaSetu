"""Register a test user for RAG testing with TRAINER role."""

import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"

# Get a TRAINER role
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DATABASE')]

# First try to find TRAINER role
role = db.roles.find_one({"name": "TRAINER"})
if not role:
    # Otherwise find ADMIN role
    role = db.roles.find_one({"name": "ADMIN"})
if not role:
    # Otherwise just use any role
    role = db.roles.find_one()

role_id = str(role['_id']) if role else None

if not role_id:
    print("❌ No roles found in database")
    exit(1)

print(f"Using role: {role['name']} ({role_id})")

# Register
response = requests.post(
    f'{BASE_URL}/auth/register',
    json={
        'email': 'ragtester@example.com',
        'password': 'test-password-123',
        'full_name': 'RAG Tester',
        'role_id': role_id,
        'designation': 'Tester',
        'department': 'Test',
        'employee_id': 'RAG001'
    }
)

if response.status_code in [200, 201]:
    print('✅ User registered/exists')
    print(f"Status: {response.status_code}")
else:
    print(f"❌ Registration failed: {response.status_code}")
    print(f"Response: {response.text}")
