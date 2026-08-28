#!/usr/bin/env python3
"""Clear and reseed mappings."""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]

print("Clearing mappings...")
result = db.competency_resource_mappings.delete_many({})
print(f"Deleted {result.deleted_count} documents")

client.close()
