#!/usr/bin/env python3
"""Final integrity check after fixes"""

from pymongo import MongoClient
from bson import ObjectId
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("FINAL DATA INTEGRITY VERIFICATION")
print("="*100)

# A. Competencies
comp_count = database.competencies.count_documents({})
print(f"\nA. COMPETENCIES")
print(f"   Total: {comp_count}")
print(f"   Expected: 33")
print(f"   Status: {'✓' if comp_count == 33 else '✗'}")

# B. Learning resources
res_count = database.learning_resources.count_documents({})
print(f"\nB. LEARNING RESOURCES")
print(f"   Total: {res_count}")
print(f"   Expected: 148")
print(f"   Status: {'✓' if res_count == 148 else '✗'}")

# C. Resource mappings
map_count = database.learning_resource_mappings.count_documents({})
igot_map = database.learning_resource_mappings.count_documents({"provider": "IGOT"})
nssta_map = database.learning_resource_mappings.count_documents({"provider": "NSSTA"})

print(f"\nC. RESOURCE MAPPINGS")
print(f"   Total: {map_count}")
print(f"   IGOT: {igot_map}")
print(f"   NSSTA: {nssta_map}")
print(f"   Status: {'✓' if map_count == 88 else '✗'}")

# Check orphans
orphan_res = 0
orphan_comp = 0
for mapping in database.learning_resource_mappings.find({}):
    res = database.learning_resources.find_one({"_id": mapping.get("resource_id")})
    if not res:
        orphan_res += 1
    comp = database.competencies.find_one({"code": mapping.get("competency_code")})
    if not comp:
        orphan_comp += 1

print(f"   Orphan resource refs: {orphan_res}")
print(f"   Orphan competency refs: {orphan_comp}")
print(f"   Status: {'✓' if orphan_res == 0 and orphan_comp == 0 else '✗'}")

# D. Role requirements
role = database.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
role_req_count = database.role_requirements.count_documents({"role_id": role["_id"]})

print(f"\nD. ROLE REQUIREMENTS")
print(f"   Total: {role_req_count}")
print(f"   Expected: 8")
print(f"   Status: {'✓' if role_req_count == 8 else '✗'}")

# Check orphans in role_requirements
orphan_role_reqs = 0
for req in database.role_requirements.find({"role_id": role["_id"]}):
    comp = database.competencies.find_one({"_id": req.get("competency_id")})
    if not comp:
        orphan_role_reqs += 1

print(f"   Orphan competency refs: {orphan_role_reqs}")
print(f"   Status: {'✓' if orphan_role_reqs == 0 else '✗'}")

# E. Provider distribution
igot_res = database.learning_resources.count_documents({"provider": "IGOT"})
nssta_res = database.learning_resources.count_documents({"provider": "NSSTA"})

print(f"\nE. PROVIDER DISTRIBUTION")
print(f"   IGOT resources: {igot_res}")
print(f"   NSSTA resources: {nssta_res}")
print(f"   Total: {igot_res + nssta_res}")

# F. NULL course_id records
null_course_id = database.learning_resources.count_documents({
    "provider": "NSSTA",
    "provider_specific.course_id": None
})

print(f"\nF. NULL COURSE_ID RECORDS (NSSTA)")
print(f"   Count: {null_course_id}")
print(f"   Expected: 5")
print(f"   Status: {'✓' if null_course_id == 5 else '✗'}")

# G. Duplicate resource_id check
all_res_ids = list(database.learning_resources.find({}, {"resource_id": 1}))
unique_res_ids = set(r["resource_id"] for r in all_res_ids)
duplicate_count = len(all_res_ids) - len(unique_res_ids)

print(f"\nG. DUPLICATE RESOURCE_ID CHECK")
print(f"   Total resources: {len(all_res_ids)}")
print(f"   Unique resource_ids: {len(unique_res_ids)}")
print(f"   Duplicates: {duplicate_count}")
print(f"   Status: {'✓' if duplicate_count == 0 else '✗'}")

print(f"\n" + "="*100)
print("SUMMARY")
print("="*100)

all_ok = (
    comp_count == 33 and
    res_count == 148 and
    map_count == 88 and
    orphan_res == 0 and
    orphan_comp == 0 and
    role_req_count == 8 and
    orphan_role_reqs == 0 and
    duplicate_count == 0
)

print(f"\nAll integrity checks: {'✓ PASS' if all_ok else '✗ FAIL'}")

client.close()

print(f"\n{'='*100}\n")
