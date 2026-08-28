#!/usr/bin/env python3
"""Check NULL course_id distribution"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]

# Check NSSTA resources with null course_id
nssta_total = db.learning_resources.count_documents({"provider": "NSSTA"})
nssta_with_null = db.learning_resources.count_documents({"provider": "NSSTA", "provider_specific.course_id": None})
nssta_with_value = db.learning_resources.count_documents({"provider": "NSSTA", "provider_specific.course_id": {"$ne": None}})

print(f"NSSTA Resources:")
print(f"  Total: {nssta_total}")
print(f"  With NULL course_id: {nssta_with_null}")
print(f"  With non-NULL course_id: {nssta_with_value}")

# Check iGOT
igot_total = db.learning_resources.count_documents({"provider": "IGOT"})
igot_with_null = db.learning_resources.count_documents({"provider": "IGOT", "provider_specific.course_id": None})
igot_with_value = db.learning_resources.count_documents({"provider": "IGOT", "provider_specific.course_id": {"$ne": None}})

print(f"\niGOT Resources:")
print(f"  Total: {igot_total}")
print(f"  With NULL course_id: {igot_with_null}")
print(f"  With non-NULL course_id: {igot_with_value}")

client.close()
