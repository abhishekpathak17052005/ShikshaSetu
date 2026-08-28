#!/usr/bin/env python3
"""Test if current mapping queries work correctly"""

from pymongo import MongoClient
from bson import ObjectId
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("TESTING MAPPING QUERIES")
print("="*100)

# Get a sample mapping
mapping = database.learning_resource_mappings.find_one({})
if not mapping:
    print("No mappings found")
    exit(1)

print(f"\nSample mapping:")
print(f"  _id: {mapping['_id']}")
print(f"  resource_id field: {mapping['resource_id']} (type: {type(mapping['resource_id']).__name__})")
print(f"  competency_code: {mapping['competency_code']}")

# Test if it's an ObjectId or string
resource_id_value = mapping['resource_id']
print(f"\nResource ID value: {resource_id_value}")
print(f"Type: {type(resource_id_value)}")

# Try to find resource by this ID
print(f"\n1. Query by resource_id field (string lookup):")
res_by_id = database.learning_resources.find_one({"resource_id": str(resource_id_value)})
print(f"   Result: {'FOUND' if res_by_id else 'NOT FOUND'}")

print(f"\n2. Query by _id (ObjectId lookup):")
if isinstance(resource_id_value, ObjectId):
    res_by_oid = database.learning_resources.find_one({"_id": resource_id_value})
else:
    try:
        res_by_oid = database.learning_resources.find_one({"_id": ObjectId(str(resource_id_value))})
    except:
        res_by_oid = None
        
print(f"   Result: {'FOUND' if res_by_oid else 'NOT FOUND'}")
if res_by_oid:
    print(f"   Found resource: {res_by_oid['resource_id']} (provider: {res_by_oid['provider']})")

# Test the actual repository query
print(f"\n3. Repository get_resource_by_mongo_id query:")
from app.learning_resources.repository import LearningResourceRepository
repo = LearningResourceRepository(database)
resource = repo.get_resource_by_mongo_id(str(resource_id_value))
print(f"   Result: {'FOUND' if resource else 'NOT FOUND'}")
if resource:
    print(f"   Found resource: {resource['resource_id']} (provider: {resource['provider']})")

client.close()

print(f"\n{'='*100}\n")
