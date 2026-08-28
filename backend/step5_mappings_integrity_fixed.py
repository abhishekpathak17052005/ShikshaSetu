#!/usr/bin/env python3
"""STEP 5: Verify resource mappings integrity - FIXED VALIDATION"""

from pymongo import MongoClient
from bson import ObjectId
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("STEP 5: RESOURCE MAPPINGS INTEGRITY (CORRECTED)")
print("="*100)

all_mappings = list(database.learning_resource_mappings.find({}))
print(f"\nTotal mappings: {len(all_mappings)}")

valid_mappings = 0
orphan_resource_mappings = 0
orphan_competency_mappings = 0

print(f"\nValidating all {len(all_mappings)} mappings...")

for mapping in all_mappings:
    resource_id_oid = mapping.get("resource_id")  # This is ObjectId
    competency_code = mapping.get("competency_code")
    
    # Check if resource exists by ObjectId (not by resource_id field)
    resource = database.learning_resources.find_one({"_id": resource_id_oid})
    if not resource:
        orphan_resource_mappings += 1
    
    # Check if competency exists
    competency = database.competencies.find_one({"code": competency_code})
    if not competency:
        orphan_competency_mappings += 1
    
    if resource and competency:
        valid_mappings += 1

print(f"\nResults:")
print(f"  Valid mappings:           {valid_mappings}")
print(f"  Orphan resource refs:     {orphan_resource_mappings}")
print(f"  Orphan competency refs:   {orphan_competency_mappings}")

if orphan_resource_mappings == 0 and orphan_competency_mappings == 0:
    print(f"\n  Status: ✓ ALL MAPPINGS VALID")
else:
    print(f"\n  Status: ✗ HAS ORPHAN REFERENCES")

# Sample check first 5
print(f"\nSample (first 5 mappings):")
for i, mapping in enumerate(all_mappings[:5], 1):
    res_oid = mapping.get("resource_id")
    comp_code = mapping.get("competency_code")
    provider = mapping.get("provider")
    
    resource = database.learning_resources.find_one({"_id": res_oid})
    competency = database.competencies.find_one({"code": comp_code})
    
    res_status = "✓" if resource else "✗"
    comp_status = "✓" if competency else "✗"
    
    res_title = resource["resource_id"][:30] if resource else "MISSING"
    print(f"  {i}. {provider:5} | Resource {res_status} | Competency {comp_status} | {comp_code:20} → {res_title}")

client.close()

print(f"\n{'='*100}\n")
