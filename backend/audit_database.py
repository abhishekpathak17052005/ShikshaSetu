#!/usr/bin/env python3
"""Audit the actual MongoDB data to verify Week 1 seeding."""

import sys
import json
from datetime import datetime
from app.core.config import get_settings
from app.core.database import initialize_database

def audit_database():
    """Inspect actual database state."""
    
    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    
    print("\n" + "="*80)
    print("DATABASE AUDIT: Phase 3 Week 1 Seeding Verification")
    print("="*80 + "\n")
    
    try:
        # 1. Competencies
        print("1️⃣  COMPETENCIES COLLECTION")
        print("-"*80)
        
        comp_coll = database.competencies
        comp_count = comp_coll.count_documents({})
        print(f"Total documents: {comp_count}")
        
        if comp_count > 0:
            sample = comp_coll.find_one()
            print(f"\nSample document structure:")
            print(json.dumps(sample, indent=2, default=str)[:500] + "...")
            
            # Domain breakdown
            domains = comp_coll.aggregate([
                {"$group": {"_id": "$domain", "count": {"$sum": 1}}}
            ])
            print(f"\nBy domain:")
            for doc in domains:
                print(f"  {doc['_id']}: {doc['count']}")
            
            # Framework status
            statuses = comp_coll.aggregate([
                {"$group": {"_id": "$framework_status", "count": {"$sum": 1}}}
            ])
            print(f"\nBy framework_status:")
            for doc in statuses:
                print(f"  {doc['_id']}: {doc['count']}")
        
        # 2. Learning Resources
        print("\n\n2️⃣  LEARNING_RESOURCES COLLECTION")
        print("-"*80)
        
        res_coll = database.learning_resources
        res_count = res_coll.count_documents({})
        print(f"Total documents: {res_count}")
        
        if res_count > 0:
            sample = res_coll.find_one()
            print(f"\nSample document structure:")
            # Show structure only, not full content
            keys = list(sample.keys())
            print(f"Top-level keys: {keys}")
            if "provider_specific" in sample:
                print(f"provider_specific keys: {list(sample['provider_specific'].keys())}")
            if "source" in sample:
                print(f"source keys: {list(sample['source'].keys())}")
            
            # Provider breakdown
            providers = res_coll.aggregate([
                {"$group": {"_id": "$provider", "count": {"$sum": 1}}}
            ])
            print(f"\nBy provider:")
            for doc in providers:
                print(f"  {doc['_id']}: {doc['count']}")
            
            # Resource type breakdown
            types = res_coll.aggregate([
                {"$group": {"_id": "$resource_type", "count": {"$sum": 1}}}
            ])
            print(f"\nBy resource_type:")
            for doc in types:
                print(f"  {doc['_id']}: {doc['count']}")
            
            # Verification status breakdown
            verifs = res_coll.aggregate([
                {"$group": {"_id": "$source.verification_status", "count": {"$sum": 1}}}
            ])
            print(f"\nBy verification_status:")
            for doc in verifs:
                print(f"  {doc['_id']}: {doc['count']}")
            
            # NULL course_id count
            null_count = res_coll.count_documents({"provider_specific.course_id": None})
            print(f"\nWith NULL/None course_id: {null_count}")
            
            # NULL course_id + NSSTA
            nssta_null = res_coll.count_documents({
                "provider": "NSSTA",
                "provider_specific.course_id": None
            })
            print(f"NSSTA with NULL course_id: {nssta_null}")
            
            # Show the NULL course_id records
            null_records = list(res_coll.find({
                "provider": "NSSTA",
                "provider_specific.course_id": None
            }, {"title": 1, "resource_id": 1, "provider": 1, "provider_specific.course_id": 1}))
            
            if null_records:
                print(f"\nNSTA/MoSPI records with NULL course_id:")
                for rec in null_records[:5]:
                    print(f"  - {rec['resource_id']}: {rec['title'][:60]}")
        
        # 3. Learning Resource Mappings
        print("\n\n3️⃣  LEARNING_RESOURCE_MAPPINGS COLLECTION")
        print("-"*80)
        
        map_coll = database.learning_resource_mappings
        map_count = map_coll.count_documents({})
        print(f"Total documents: {map_count}")
        
        if map_count > 0:
            sample = map_coll.find_one()
            print(f"\nSample document keys: {list(sample.keys())}")
            
            # Provider breakdown
            providers = map_coll.aggregate([
                {"$group": {"_id": "$provider", "count": {"$sum": 1}}}
            ])
            print(f"\nMappings by provider:")
            for doc in providers:
                print(f"  {doc['_id']}: {doc['count']}")
        
        # 4. Validate referential integrity
        print("\n\n4️⃣  REFERENTIAL INTEGRITY CHECK")
        print("-"*80)
        
        # Get all resource_id (MongoDB _id) from mappings
        mapped_resource_ids = set()
        for doc in map_coll.find({}, {"resource_id": 1}):
            # resource_id in mappings is the MongoDB _id ObjectId
            if "resource_id" in doc and doc["resource_id"]:
                mapped_resource_ids.add(str(doc["resource_id"]))
        
        print(f"Unique resource MongoDB IDs in mappings: {len(mapped_resource_ids)}")
        
        # Check if they exist in resources by MongoDB _id
        existing_resources = set()
        for obj_id_str in mapped_resource_ids:
            from bson import ObjectId
            try:
                obj_id = ObjectId(obj_id_str)
                if res_coll.find_one({"_id": obj_id}):
                    existing_resources.add(obj_id_str)
            except:
                pass
        
        missing_resources = mapped_resource_ids - existing_resources
        if missing_resources:
            print(f"❌ ORPHANED: Mappings point to non-existent resources:")
            for rid in list(missing_resources)[:5]:
                print(f"  - {rid}")
        else:
            print(f"✅ All mapped resources exist")
        
        # Get all competency_codes from mappings
        mapped_comp_codes = set()
        for doc in map_coll.find({}, {"competency_code": 1}):
            mapped_comp_codes.add(doc["competency_code"])
        
        print(f"\nUnique competency_codes in mappings: {len(mapped_comp_codes)}")
        
        # Check if they exist in competencies
        existing_competencies = set()
        for code in mapped_comp_codes:
            if comp_coll.find_one({"code": code}):
                existing_competencies.add(code)
        
        missing_competencies = mapped_comp_codes - existing_competencies
        if missing_competencies:
            print(f"❌ ORPHANED: Mappings point to non-existent competencies:")
            for code in list(missing_competencies)[:5]:
                print(f"  - {code}")
        else:
            print(f"✅ All mapped competencies exist")
        
        # 5. Mapping distribution
        print("\n\n5️⃣  MAPPING DISTRIBUTION")
        print("-"*80)
        
        # iGOT vs NSSTA
        igot_mappings = map_coll.count_documents({"provider": "IGOT"})
        nssta_mappings = map_coll.count_documents({"provider": "NSSTA"})
        
        print(f"iGOT mappings: {igot_mappings}")
        print(f"NSSTA mappings: {nssta_mappings}")
        
        # Mapping distribution by competency
        comp_dist = map_coll.aggregate([
            {"$group": {"_id": "$competency_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        
        print(f"\nTop 10 competencies by mapping count:")
        for doc in comp_dist:
            print(f"  {doc['_id']}: {doc['count']}")
        
        # 6. Summary
        print("\n\n6️⃣  SUMMARY")
        print("-"*80)
        
        print(f"""
Document Counts:
  Competencies:          {comp_count}
  Learning Resources:    {res_count}
  Resource Mappings:     {map_count}

Provider Breakdown:
  iGOT Resources:        {res_coll.count_documents({'provider': 'IGOT'})}
  NSSTA Resources:       {res_coll.count_documents({'provider': 'NSSTA'})}

Resource Types:
  COURSE:                {res_coll.count_documents({'resource_type': 'COURSE'})}
  TRAINING_PROGRAMME:    {res_coll.count_documents({'resource_type': 'TRAINING_PROGRAMME'})}

Verification Status:
  VERIFIED:              {res_coll.count_documents({'source.verification_status': 'VERIFIED'})}
  TENTATIVE:             {res_coll.count_documents({'source.verification_status': 'TENTATIVE'})}

NULL course_id:
  Total with NULL:       {null_count}
  NSSTA with NULL:       {nssta_null}
  iGOT with NULL:        {res_coll.count_documents({'provider': 'IGOT', 'provider_specific.course_id': None})}

Referential Integrity:
  Orphaned resources:    {len(missing_resources)}
  Orphaned competencies: {len(missing_competencies)}

Mapping Distribution:
  iGOT:                  {igot_mappings}
  NSSTA:                 {nssta_mappings}
        """)
        
        print("="*80)
        print("✅ AUDIT COMPLETE")
        print("="*80 + "\n")
        
    finally:
        client.close()

if __name__ == "__main__":
    try:
        audit_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
