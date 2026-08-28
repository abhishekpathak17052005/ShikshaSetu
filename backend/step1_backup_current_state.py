#!/usr/bin/env python3
"""STEP 1: Record current production database state before reseeding"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
prod_db = client[settings.mongodb_database]  # shikshasetu (production)

print("\n" + "="*100)
print("STEP 1: PRODUCTION DATABASE BACKUP STATE (BEFORE RESEED)")
print("="*100)

print(f"\nDatabase: {settings.mongodb_database}")
print(f"Connection: {settings.mongodb_uri}\n")

backup_state = {
    "competencies": prod_db.competencies.count_documents({}),
    "roles": prod_db.roles.count_documents({}),
    "role_requirements": prod_db.role_requirements.count_documents({}),
    "learning_resources": prod_db.learning_resources.count_documents({}),
    "learning_resource_mappings": prod_db.learning_resource_mappings.count_documents({}),
}

for collection, count in backup_state.items():
    print(f"  {collection:35} = {count:5}")

print("\n" + "="*100)
print("BACKUP COMPLETE - READY FOR RESEED")
print("="*100 + "\n")

client.close()
