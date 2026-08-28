#!/usr/bin/env python3
"""
DIAGNOSIS ONLY - Direct MongoDB inspection
No modifications, no reseeding, no code changes
"""

from pymongo import MongoClient
from app.core.config import get_settings

print("\n" + "="*100)
print("DIAGNOSIS: ROOT CAUSE ANALYSIS")
print("="*100)

settings = get_settings()

print("\n" + "="*100)
print("CHECK 1: MONGODB CONFIGURATION")
print("="*100)

print(f"\nAPI Configuration (from get_settings()):")
print(f"  MongoDB URI:      {settings.mongodb_uri}")
print(f"  Database name:    {settings.mongodb_database}")

print(f"\nNote: .env file has two MONGODB_URI entries.")
print(f"      The second one (line 6) OVERWRITES the first.")
print(f"      Current effective URI: {settings.mongodb_uri}")

# Connect to the API's database
print(f"\nConnecting to: {settings.mongodb_uri}")
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)

try:
    # Force connection test
    client.admin.command('ping')
    print(f"✓ Connection successful")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

database = client[settings.mongodb_database]

print(f"\n" + "="*100)
print("CHECK 2: DIRECT MONGODB COUNTS")
print("="*100)

collections = {
    "competencies": "competencies",
    "roles": "roles",
    "role_requirements": "role_requirements",
    "learning_resources": "learning_resources",
    "learning_resource_mappings": "learning_resource_mappings",
    "users": "users",
}

counts = {}
print(f"\nDatabase: {settings.mongodb_database}")
for label, collection_name in collections.items():
    count = database[collection_name].count_documents({})
    counts[label] = count
    print(f"  {label:30} = {count:5}")

print(f"\nExpected counts (from seed):")
print(f"  competencies                   =    33")
print(f"  roles                          =     1")
print(f"  role_requirements              =     8")
print(f"  learning_resources             =   148")
print(f"  learning_resource_mappings     =    88")

print(f"\n" + "="*100)
print("CHECK 3: COMPETENCIES COLLECTION SAMPLE")
print("="*100)

competencies = database.competencies.find({}).limit(5)
print(f"\nFirst 5 competencies in MongoDB:")
for i, comp in enumerate(competencies, 1):
    print(f"\n  {i}. {comp.get('code'):20} {comp.get('name'):30} status={comp.get('status')}")

print(f"\n" + "="*100)
print("CHECK 4: ROLES & ROLE REQUIREMENTS")
print("="*100)

role = database.roles.find_one({})
if role:
    print(f"\nRole found in MongoDB:")
    print(f"  _id:      {role.get('_id')}")
    print(f"  code:     {role.get('role_code')}")
    print(f"  name:     {role.get('role_name')}")
    print(f"  status:   {role.get('status')}")
    
    req_count = database.role_requirements.count_documents({"role_id": role["_id"]})
    print(f"\n  Role requirements for this role: {req_count}")
    
    reqs = database.role_requirements.find({"role_id": role["_id"]}).limit(5)
    for i, req in enumerate(reqs, 1):
        comp = database.competencies.find_one({"_id": req.get("competency_id")})
        print(f"    {i}. {comp.get('code') if comp else 'UNKNOWN':20} required_level={req.get('required_level')}")
else:
    print(f"\n✗ No roles found in MongoDB")

print(f"\n" + "="*100)
print("CHECK 5: USERS & TEST USER")
print("="*100)

test_user = database.users.find_one({}, sort=[("_id", -1)])
if test_user:
    print(f"\nMost recent user in MongoDB:")
    print(f"  user_id:     {test_user.get('_id')}")
    print(f"  email:       {test_user.get('email')}")
    print(f"  role_id:     {test_user.get('role_id')}")
    print(f"  status:      {test_user.get('status')}")
    print(f"  access_role: {test_user.get('access_role')}")
else:
    print(f"\n✗ No users found in MongoDB")

print(f"\n" + "="*100)
print("CHECK 6: LEARNING RESOURCES BY PROVIDER")
print("="*100)

igot_count = database.learning_resources.count_documents({"provider": "IGOT"})
nssta_count = database.learning_resources.count_documents({"provider": "NSSTA"})
other_count = database.learning_resources.count_documents({"provider": {"$nin": ["IGOT", "NSSTA"]}})

print(f"\nLearning resources by provider:")
print(f"  IGOT:     {igot_count}")
print(f"  NSSTA:    {nssta_count}")
print(f"  Other:    {other_count}")
print(f"  Total:    {igot_count + nssta_count + other_count}")

print(f"\n" + "="*100)
print("CHECK 7: DATABASE SUMMARY")
print("="*100)

if counts.get("competencies", 0) > 0:
    print(f"\n✓ DATABASE HAS DATA:")
    print(f"  - Competencies loaded: {counts.get('competencies')}")
    print(f"  - Resources loaded: {counts.get('learning_resources')}")
    print(f"  - Mappings loaded: {counts.get('learning_resource_mappings')}")
else:
    print(f"\n✗ DATABASE IS EMPTY - SEED DATA NOT PRESENT")

print(f"\n" + "="*100)
print("SUMMARY")
print("="*100)

if counts.get("competencies", 0) == 0:
    print(f"\n❌ ROOT CAUSE: Seed data is NOT in the database.")
    print(f"   The API is querying an EMPTY database.")
    print(f"   Seeding must be re-run.")
else:
    print(f"\n✓ Seed data IS in the database.")
    print(f"  HTTP endpoints should be able to access it.")
    print(f"  Issue is likely in the HTTP route logic, not database.")

client.close()

print(f"\n{'='*100}")
