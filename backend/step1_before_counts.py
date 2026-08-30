#!/usr/bin/env python3
"""STEP 1: Record current counts before seeding"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("STEP 1: PRE-SEED DATABASE STATE")
print("="*100)

collections = {
    "competencies": "competencies",
    "roles": "roles",
    "role_requirements": "role_requirements",
    "learning_resources": "learning_resources",
    "learning_resource_mappings": "learning_resource_mappings",
}

print(f"\nDatabase: {settings.mongodb_database}")
print(f"Host: {settings.mongodb_uri}\n")

before_counts = {}
for label, collection_name in collections.items():
    count = database[collection_name].count_documents({})
    before_counts[label] = count
    print(f"  {label:35} = {count:5}")

# Role requirements for STATISTICAL_OFFICER
role = database.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
if role:
    role_reqs = list(database.role_requirements.find({"role_id": role["_id"]}))
    print(f"\nSTATISTICAL_OFFICER role requirements: {len(role_reqs)}")
    if role_reqs:
        print(f"  Sample (first 5):")
        for i, req in enumerate(role_reqs[:5], 1):
            comp = database.competencies.find_one({"_id": req.get("competency_id")})
            status = "✓" if comp else "✗ ORPHANED"
            print(f"    {i}. competency_id={str(req.get('competency_id'))[:12]}... {status}")

client.close()

print(f"\n{'='*100}\n")
