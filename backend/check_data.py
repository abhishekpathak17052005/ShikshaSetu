#!/usr/bin/env python3
"""Check what's in the database after seeding."""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]

# Get all competencies
competencies = list(db.competencies.find({}, {"_id": 0, "code": 1, "name": 1}))
print(f"Total competencies: {len(competencies)}")
for c in sorted(competencies, key=lambda x: x.get("code", "")):
    print(f"  {c.get('code')}: {c.get('name')}")

print("\n" + "="*80)
resources = db.learning_resources.count_documents({})
print(f"Total learning resources: {resources}")

igot = db.learning_resources.count_documents({"provider": "IGOT"})
nssta = db.learning_resources.count_documents({"provider": "NSSTA"})
print(f"  iGOT: {igot}")
print(f"  NSSTA: {nssta}")

null_course = db.learning_resources.count_documents({"provider": "NSSTA", "course_id": None})
print(f"  NSSTA with NULL course_id: {null_course}")

print("\n" + "="*80)
mappings = db.competency_resource_mappings.count_documents({})
print(f"Total mappings: {mappings}")

client.close()
