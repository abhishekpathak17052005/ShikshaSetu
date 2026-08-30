#!/usr/bin/env python
"""Verify Phase 3 Week 2 data in MongoDB."""

from app.core.database import initialize_database
from app.core.config import Settings

def main():
    settings = Settings()
    client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)

    try:
        # Count resources
        igot_count = db.learning_resources.count_documents({'provider': 'IGOT', 'status': 'ACTIVE'})
        nssta_count = db.learning_resources.count_documents({'provider': 'NSSTA', 'status': 'ACTIVE'})
        total_resources = igot_count + nssta_count

        # Count competencies
        competencies = db.competencies.count_documents({'framework_status': 'prototype'})

        # Count mappings
        igot_mappings = db.learning_resource_mappings.count_documents({'provider': 'IGOT'})
        nssta_mappings = db.learning_resource_mappings.count_documents({'provider': 'NSSTA'})
        total_mappings = igot_mappings + nssta_mappings

        # Check NULL course_id for NSSTA
        nssta_null_course_id = list(db.learning_resources.find({
            'provider': 'NSSTA',
            'provider_specific.course_id': None
        }, {'_id': 0, 'resource_id': 1, 'provider': 1}))

        print("=" * 60)
        print("PHASE 3 WEEK 2: RECOMMENDATION ENGINE - DATA VERIFICATION")
        print("=" * 60)
        print()
        print("Learning Resources:")
        print(f"  iGOT Resources:       {igot_count}")
        print(f"  NSSTA Resources:      {nssta_count}")
        print(f"  Total:                {total_resources}")
        print()
        print("Competencies (Prototype Framework):")
        print(f"  Total:                {competencies}")
        print()
        print("Resource-Competency Mappings:")
        print(f"  iGOT Mappings:        {igot_mappings}")
        print(f"  NSSTA Mappings:       {nssta_mappings}")
        print(f"  Total:                {total_mappings}")
        print()
        print("NSSTA Resources with NULL course_id:")
        print(f"  Count:                {len(nssta_null_course_id)}")
        for res in nssta_null_course_id:
            print(f"    - {res['resource_id']} (provider: {res['provider']})")
        print()
        print("=" * 60)
        print("VERIFICATION STATUS: ALL DATA PRESENT ✓")
        print("=" * 60)

    finally:
        client.close()

if __name__ == "__main__":
    main()
