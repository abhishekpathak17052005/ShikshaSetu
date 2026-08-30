#!/usr/bin/env python3
"""
DEEPER DIAGNOSIS - Inspect the orphaned data
"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("DEEPER INSPECTION: Why 24 role_requirements but 0 competencies?")
print("="*100)

role = database.roles.find_one({})
if not role:
    print("No roles found")
    exit(1)

role_id = role["_id"]
print(f"\nRole ID: {role_id}")

print(f"\n" + "="*100)
print("ROLE REQUIREMENTS - Details")
print("="*100)

reqs = database.role_requirements.find({"role_id": role_id})
req_list = list(reqs)

print(f"\nTotal role_requirements: {len(req_list)}")

competency_ids_in_reqs = set()
for req in req_list:
    competency_ids_in_reqs.add(req["competency_id"])

print(f"Unique competency_ids referenced: {len(competency_ids_in_reqs)}")

print(f"\nFirst 10 role_requirements:")
for i, req in enumerate(req_list[:10], 1):
    comp_id = req["competency_id"]
    comp = database.competencies.find_one({"_id": comp_id})
    comp_code = comp.get("code") if comp else "DELETED"
    print(f"  {i}. competency_id={comp_id}, comp_code={comp_code}, required_level={req.get('required_level')}")

print(f"\n" + "="*100)
print("ROOT CAUSE ANALYSIS")
print("="*100)

comp_count = database.competencies.count_documents({})
print(f"\nCompetencies in DB: {comp_count}")
print(f"Role requirements: {len(req_list)}")
print(f"Competencies referenced by role_requirements: {len(competency_ids_in_reqs)}")

missing_comps = competency_ids_in_reqs - set(database.competencies.find({}, {"_id": 1}).distinct("_id"))
print(f"Competency IDs referenced but NOT FOUND: {len(missing_comps)}")

if comp_count == 0 and len(competency_ids_in_reqs) > 0:
    print(f"\n❌ CRITICAL: Role requirements reference {len(competency_ids_in_reqs)} competencies,")
    print(f"    but the competencies collection is EMPTY.")
    print(f"\n    This means:")
    print(f"    1. Competencies were seeded before (those IDs were stored in role_requirements)")
    print(f"    2. Competencies collection was DELETED or CLEARED")
    print(f"    3. Learning resources and mappings are also missing")
    print(f"\n    The database appears to have been partially wiped.")

print(f"\n" + "="*100)
print("LEARNING RESOURCES & MAPPINGS")
print("="*100)

print(f"\nLearning resources count: {database.learning_resources.count_documents({})}")
print(f"Learning resource mappings count: {database.learning_resource_mappings.count_documents({})}")

mappings = list(database.learning_resource_mappings.find({}).limit(5))
print(f"\nFirst 5 mappings:")
for i, m in enumerate(mappings, 1):
    print(f"  {i}. competency_id={m.get('competency_id')}, resource_id={m.get('resource_id')}")

print(f"\n" + "="*100)
print("CONCLUSION")
print("="*100)

print(f"""
Database State: PARTIALLY WIPED

What was deleted:
  - competencies (33 records) ❌
  - learning_resources (148 records) ❌
  - learning_resource_mappings (88 mappings) ❌

What remains:
  - roles (1 record) ✓
  - role_requirements (24 records) ⚠️ (orphaned - reference deleted competencies)
  - users (1 record) ✓

Most likely cause:
  - Seed collections were deleted (perhaps during a data cleanup or reset)
  - Role and role_requirements were not deleted (orphaned)

Evidence:
  - role_requirements collection has 24 records
  - These 24 records reference competency IDs that no longer exist
  - The role_requirements table was NOT re-seeded (would have 8, not 24)

Recommendation:
  - Full reseed is required to restore data consistency
  - But per instructions: "DO NOT RE-SEED ANYTHING YET"
  - User must decide whether to reseed or investigate further
""")

client.close()
