#!/usr/bin/env python3
"""Check MongoDB state during test failure"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]

print("MongoDB State Check:")
print(f"  competencies: {db.competencies.count_documents({})}")
print(f"  roles: {db.roles.count_documents({})}")
print(f"  role_requirements: {db.role_requirements.count_documents({})}")
print(f"  learning_resources: {db.learning_resources.count_documents({})}")
print(f"  learning_resource_mappings: {db.learning_resource_mappings.count_documents({})}")

client.close()
