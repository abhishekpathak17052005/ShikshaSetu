#!/usr/bin/env python3
"""STEP 4: Comprehensive integrity checks"""

from pymongo import MongoClient
from bson import ObjectId
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
prod_db = client[settings.mongodb_database]

print("\n" + "="*100)
print("STEP 4: DATA INTEGRITY CHECKS")
print("="*100)

# Check 1: Zero orphan role_requirements
print(f"\n1. ORPHAN ROLE_REQUIREMENTS CHECK:")
role = prod_db.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
role_id = role["_id"]

orphan_role_reqs = 0
for req in prod_db.role_requirements.find({"role_id": role_id}):
    comp = prod_db.competencies.find_one({"_id": req.get("competency_id")})
    if not comp:
        orphan_role_reqs += 1

print(f"   Orphan role_requirements: {orphan_role_reqs} (expected 0) {'✓' if orphan_role_reqs == 0 else '✗'}")

# Check 2: Zero orphan resource mappings
print(f"\n2. ORPHAN RESOURCE MAPPINGS CHECK:")
orphan_res = 0
orphan_comp = 0

for mapping in prod_db.learning_resource_mappings.find({}):
    res = prod_db.learning_resources.find_one({"_id": mapping.get("resource_id")})
    if not res:
        orphan_res += 1
    
    comp = prod_db.competencies.find_one({"code": mapping.get("competency_code")})
    if not comp:
        orphan_comp += 1

print(f"   Orphan resource refs: {orphan_res} (expected 0) {'✓' if orphan_res == 0 else '✗'}")
print(f"   Orphan competency refs: {orphan_comp} (expected 0) {'✓' if orphan_comp == 0 else '✗'}")

# Check 3: Zero duplicate resource_id
print(f"\n3. DUPLICATE RESOURCE_ID CHECK:")
all_res_ids = list(prod_db.learning_resources.find({}, {"resource_id": 1}))
unique_res_ids = set(r["resource_id"] for r in all_res_ids)
duplicate_count = len(all_res_ids) - len(unique_res_ids)

print(f"   Total resources: {len(all_res_ids)}")
print(f"   Unique resource_ids: {len(unique_res_ids)}")
print(f"   Duplicates: {duplicate_count} (expected 0) {'✓' if duplicate_count == 0 else '✗'}")

# Check 4: Verify NULL course_id records
print(f"\n4. NULL COURSE_ID VERIFICATION:")
null_course_id_nssta = prod_db.learning_resources.count_documents({
    "provider": "NSSTA",
    "resource_type": "TRAINING_PROGRAMME",
    "provider_specific.course_id": None
})

print(f"   NSSTA TRAINING_PROGRAMME with NULL course_id: {null_course_id_nssta}")
print(f"   Status: Found {null_course_id_nssta} records (expected around 85 total NSSTA)")

# Show sample NULL course_id records
null_samples = list(prod_db.learning_resources.find({
    "provider_specific.course_id": None
}, {"resource_id": 1, "title": 1}).limit(5))

print(f"\n   Sample NSSTA records with NULL course_id:")
for i, rec in enumerate(null_samples, 1):
    print(f"     {i}. {rec.get('resource_id')}: {rec.get('title')[:50]}")

print(f"\n" + "="*100)
all_pass = orphan_role_reqs == 0 and orphan_res == 0 and orphan_comp == 0 and duplicate_count == 0
print(f"✓ INTEGRITY CHECKS: {'PASSED' if all_pass else 'FAILED'}")
print("="*100 + "\n")

client.close()
