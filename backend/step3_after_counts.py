#!/usr/bin/env python3
"""STEP 3: Verify counts after seeding"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("STEP 3: POST-SEED DATABASE STATE")
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

after_counts = {}
for label, collection_name in collections.items():
    count = database[collection_name].count_documents({})
    after_counts[label] = count
    print(f"  {label:35} = {count:5}")

print(f"\nLearning resources by provider:")
igot_count = database.learning_resources.count_documents({"provider": "IGOT"})
nssta_count = database.learning_resources.count_documents({"provider": "NSSTA"})
print(f"  IGOT:     {igot_count}")
print(f"  NSSTA:    {nssta_count}")
print(f"  Total:    {igot_count + nssta_count}")

print(f"\nLearning resource mappings by provider:")
igot_map = database.learning_resource_mappings.count_documents({"provider": "IGOT"})
nssta_map = database.learning_resource_mappings.count_documents({"provider": "NSSTA"})
print(f"  IGOT:     {igot_map}")
print(f"  NSSTA:    {nssta_map}")
print(f"  Total:    {igot_map + nssta_map}")

client.close()

print(f"\n{'='*100}\n")
