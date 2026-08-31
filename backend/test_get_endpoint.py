#!/usr/bin/env python
"""Test GET material endpoint."""

import requests
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "ragtester@example.com",
        "password": "test-password-123"
    }
)

if response.status_code != 200:
    print(f"❌ Login failed")
    exit(1)

token = response.json()["access_token"]
print(f"✅ Logged in")

# Get a material ID
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DATABASE')]
mat = db.learning_materials.find_one()

if not mat:
    print("❌ No materials in database")
    exit(1)

material_id = str(mat["_id"])
print(f"Testing with Material ID: {material_id}")

# Try to GET it
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    f"{BASE_URL}/learning-materials/{material_id}",
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Response: {response.text}")
else:
    print(f"✅ Success: {response.json()}")
