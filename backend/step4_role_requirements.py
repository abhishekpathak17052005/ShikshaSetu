#!/usr/bin/env python3
"""STEP 4: Verify role requirements integrity"""

from pymongo import MongoClient
from app.core.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=2000)
database = client[settings.mongodb_database]

print("\n" + "="*100)
print("STEP 4: ROLE REQUIREMENTS INTEGRITY")
print("="*100)

# Get all roles
roles = list(database.roles.find({}))
print(f"\nTotal roles in database: {len(roles)}\n")

for role in roles:
    role_id = role["_id"]
    role_name = role.get("role_name", role.get("role_code"))
    
    # Get all requirements for this role
    reqs = list(database.role_requirements.find({"role_id": role_id}))
    print(f"Role: {role_name}")
    print(f"  Total requirements: {len(reqs)}")
    
    valid_count = 0
    orphan_count = 0
    
    print(f"\n  Requirements details:")
    for i, req in enumerate(reqs[:10], 1):  # Show first 10
        comp_id = req.get("competency_id")
        comp = database.competencies.find_one({"_id": comp_id})
        
        if comp:
            status = f"✓ VALID: {comp.get('code')}"
            valid_count += 1
        else:
            status = f"✗ ORPHANED: {str(comp_id)[:16]}..."
            orphan_count += 1
        
        print(f"    {i:2}. {status} (required_level={req.get('required_level')})")
    
    # Full count
    for req in reqs[10:]:
        comp = database.competencies.find_one({"_id": req.get("competency_id")})
        if comp:
            valid_count += 1
        else:
            orphan_count += 1
    
    print(f"\n  Summary for {role_name}:")
    print(f"    Valid references:  {valid_count}")
    print(f"    Orphan references: {orphan_count}")
    print(f"    Status: {'✓ OK' if orphan_count == 0 else '✗ HAS ORPHANS'}\n")

client.close()

print(f"{'='*100}\n")
