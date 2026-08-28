#!/usr/bin/env python3
"""STEP 3: Verify production database after reseeding"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
prod_db = client[settings.mongodb_database]  # shikshasetu

print("\n" + "="*100)
print("STEP 3: PRODUCTION DATABASE VERIFICATION (AFTER RESEED)")
print("="*100)

# Expected vs Actual counts
expectations = {
    "competencies": 33,
    "learning_resources": 148,
    "learning_resource_mappings": 88,
    "role_requirements": 8,
    "roles": 1,
}

print(f"\nDatabase: {settings.mongodb_database}\n")

all_match = True
for collection, expected in expectations.items():
    actual = prod_db[collection].count_documents({})
    match = "✓" if actual == expected else "✗"
    if actual != expected:
        all_match = False
    print(f"  {collection:35} expected={expected:3} actual={actual:3} {match}")

# Provider distribution
print(f"\nProvider Distribution:")
igot_resources = prod_db.learning_resources.count_documents({"provider": "IGOT"})
nssta_resources = prod_db.learning_resources.count_documents({"provider": "NSSTA"})
print(f"  IGOT resources:  {igot_resources} (expected 63) {'✓' if igot_resources == 63 else '✗'}")
print(f"  NSSTA resources: {nssta_resources} (expected 85) {'✓' if nssta_resources == 85 else '✗'}")

igot_mappings = prod_db.learning_resource_mappings.count_documents({"provider": "IGOT"})
nssta_mappings = prod_db.learning_resource_mappings.count_documents({"provider": "NSSTA"})
print(f"  IGOT mappings:   {igot_mappings} (expected 42) {'✓' if igot_mappings == 42 else '✗'}")
print(f"  NSSTA mappings:  {nssta_mappings} (expected 46) {'✓' if nssta_mappings == 46 else '✗'}")

print(f"\n" + "="*100)
if all_match and igot_resources == 63 and nssta_resources == 85 and igot_mappings == 42 and nssta_mappings == 46:
    print("✓ ALL COUNTS MATCH EXPECTED VALUES")
else:
    print("✗ SOME COUNTS DO NOT MATCH")
print("="*100 + "\n")

client.close()
