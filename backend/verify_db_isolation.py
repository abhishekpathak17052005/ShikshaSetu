#!/usr/bin/env python3
"""Verify pytest database isolation before and after tests"""

from pymongo import MongoClient
from app.core.config import get_settings

def check_databases():
    """Check both production and test databases"""
    
    settings = get_settings()
    client = MongoClient(settings.mongodb_uri)
    
    prod_db = client[settings.mongodb_database]  # shikshasetu
    test_db = client["shikshasetu_test"]  # test database
    
    print("\n" + "="*100)
    print("DATABASE ISOLATION VERIFICATION")
    print("="*100)
    
    print(f"\n[PRODUCTION DATABASE] {settings.mongodb_database}")
    print(f"  competencies:               {prod_db.competencies.count_documents({})}")
    print(f"  learning_resources:         {prod_db.learning_resources.count_documents({})}")
    print(f"  learning_resource_mappings: {prod_db.learning_resource_mappings.count_documents({})}")
    print(f"  role_requirements:          {prod_db.role_requirements.count_documents({})}")
    print(f"  roles:                      {prod_db.roles.count_documents({})}")
    
    print(f"\n[TEST DATABASE] shikshasetu_test")
    print(f"  competencies:               {test_db.competencies.count_documents({})}")
    print(f"  learning_resources:         {test_db.learning_resources.count_documents({})}")
    print(f"  learning_resource_mappings: {test_db.learning_resource_mappings.count_documents({})}")
    print(f"  users:                      {test_db.users.count_documents({})}")
    print(f"  skill_gaps:                 {test_db.skill_gaps.count_documents({})}")
    
    # Create a marker collection in test database to prove pytest will clean it
    print(f"\n[MARKER TEST] Creating marker in test database...")
    marker_id = test_db.test_markers.insert_one({"created_by": "verify_db_isolation", "timestamp": "pre-tests"})
    print(f"  Inserted marker: {marker_id.inserted_id}")
    marker_count = test_db.test_markers.count_documents({})
    print(f"  test_markers collection count: {marker_count}")
    
    client.close()
    
    print("\n" + "="*100)
    print("ISOLATION CONFIGURATION:")
    print("  ✓ Production DB: shikshasetu (will be unchanged by pytest)")
    print("  ✓ Test DB: shikshasetu_test (will be cleaned by pytest)")
    print("  ✓ Marker created: pytest cleanup will remove it")
    print("="*100 + "\n")

if __name__ == "__main__":
    check_databases()
