#!/usr/bin/env python
"""Diagnose user ID mismatch between upload and retrieval."""

import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DATABASE')]

print("=" * 70)
print("DIAGNOSING USER ID MISMATCH")
print("=" * 70)

# Get test user from database
print("\n1️⃣  Finding test user...")
test_user = db.users.find_one({"email": "ragtester@example.com"})
if test_user:
    print(f"   Found user: {test_user['email']}")
    print(f"   User _id type: {type(test_user['_id'])}")
    print(f"   User _id value: {test_user['_id']}")
    user_id = test_user["_id"]
else:
    print("   ❌ No test user found!")
    exit(1)

# Get latest material
print("\n2️⃣  Finding latest material...")
material = db.learning_materials.find_one(sort=[("created_at", -1)])
if material:
    print(f"   Found material: {material['original_filename']}")
    print(f"   Material _id type: {type(material['_id'])}")
    print(f"   Material _id value: {material['_id']}")
    print(f"   Material user_id type: {type(material.get('user_id'))}")
    print(f"   Material user_id value: {material.get('user_id')}")
    material_id = material["_id"]
else:
    print("   ❌ No materials found!")
    exit(1)

# Compare IDs
print("\n3️⃣  Comparing IDs...")
print(f"   User _id == Material user_id? {user_id == material.get('user_id')}")
print(f"   User _id as string: {str(user_id)}")
print(f"   Material user_id as string: {str(material.get('user_id'))}")

# Try the query that the GET endpoint uses
print("\n4️⃣  Testing GET endpoint query...")
query = {
    "_id": material_id,
    "user_id": user_id
}
result = db.learning_materials.find_one(query)
if result:
    print(f"   ✅ Query returned document: {result['original_filename']}")
else:
    print(f"   ❌ Query returned NO document")
    print(f"   Query was: {query}")

# Try without user filter
print("\n5️⃣  Testing without user filter...")
result = db.learning_materials.find_one({"_id": material_id})
if result:
    print(f"   ✅ Found material by ID alone: {result['original_filename']}")
else:
    print(f"   ❌ Material not found even without user filter!")

# Show all materials and their user_ids
print("\n6️⃣  All materials in database:")
materials = list(db.learning_materials.find().sort("created_at", -1).limit(5))
for i, m in enumerate(materials, 1):
    print(f"   {i}. {m['original_filename']}")
    print(f"      _id: {m['_id']}")
    print(f"      user_id: {m.get('user_id')} (type: {type(m.get('user_id')).__name__})")

print("\n" + "=" * 70)
