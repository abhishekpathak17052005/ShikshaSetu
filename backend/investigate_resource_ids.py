#!/usr/bin/env python3
"""Investigate resource_id mismatch"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("INVESTIGATING RESOURCE_ID MISMATCH")
print("="*100)

# Check learning_resources collection
resources = list(database.learning_resources.find({}).limit(5))
print(f"\nLearning resources (sample):")
for res in resources:
    print(f"  resource_id (field): {res.get('resource_id')}")
    print(f"    _id: {res.get('_id')}")
    print(f"    provider: {res.get('provider')}")
    print()

# Check learning_resource_mappings collection
mappings = list(database.learning_resource_mappings.find({}).limit(5))
print(f"Learning resource mappings (sample):")
for m in mappings:
    print(f"  resource_id (in mapping): {m.get('resource_id')}")
    print(f"    competency_code: {m.get('competency_code')}")
    print()

# Try to find a matching resource
print(f"Searching for a mapping's resource...")
if mappings:
    first_mapping = mappings[0]
    res_id_in_mapping = first_mapping.get("resource_id")
    print(f"  Mapping references resource_id: {res_id_in_mapping}")
    
    # Try finding by resource_id field
    res_by_id = database.learning_resources.find_one({"resource_id": res_id_in_mapping})
    print(f"  Query db.learning_resources.find_one({{\"resource_id\": \"{res_id_in_mapping}\"}})")
    print(f"  Result: {res_by_id is not None}")
    
    # Try finding by ObjectId
    from bson import ObjectId
    try:
        res_by_oid = database.learning_resources.find_one({"_id": ObjectId(res_id_in_mapping)})
        print(f"  Query db.learning_resources.find_one({{\"_id\": ObjectId(\"{res_id_in_mapping}\")}})")
        print(f"  Result: {res_by_oid is not None}")
    except:
        print(f"  ObjectId conversion failed (not a valid OID)")

client.close()

print(f"\n{'='*100}\n")
