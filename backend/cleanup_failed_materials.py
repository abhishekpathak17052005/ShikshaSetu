#!/usr/bin/env python
"""Clean up failed and invalid materials from database."""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def main():
    """Delete all failed materials and associated chunks."""
    
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGODB_DATABASE', 'shikshasetu')
    
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        db.command('ping')
        print(f"✅ Connected to {db_name}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Delete failed materials
    print("Deleting FAILED materials...")
    failed = db.learning_materials.delete_many({'status': 'FAILED'})
    print(f"  Deleted: {failed.deleted_count} failed materials")
    
    # Delete materials with 0 chunks (orphaned)
    print("\nDeleting orphaned materials (0 chunks)...")
    orphaned = db.learning_materials.delete_many({'chunk_count': 0, 'status': 'READY'})
    print(f"  Deleted: {orphaned.deleted_count} orphaned materials")
    
    # Delete materials with null filename (corrupted records)
    print("\nDeleting corrupted records...")
    corrupted = db.learning_materials.delete_many({'original_filename': None})
    print(f"  Deleted: {corrupted.deleted_count} corrupted materials")
    
    # Delete orphaned chunks (no associated material)
    print("\nDeleting orphaned chunks...")
    all_chunks = list(db.document_chunks.find({}))
    valid_materials = set(str(m['_id']) for m in db.learning_materials.find({}))
    
    orphan_chunks = [c for c in all_chunks if str(c.get('material_id', '')) not in valid_materials]
    if orphan_chunks:
        db.document_chunks.delete_many({'_id': {'$in': [c['_id'] for c in orphan_chunks]}})
        print(f"  Deleted: {len(orphan_chunks)} orphaned chunks")
    else:
        print("No orphaned chunks found")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    materials_count = db.learning_materials.count_documents({})
    ready_count = db.learning_materials.count_documents({'status': 'READY'})
    processing_count = db.learning_materials.count_documents({'status': 'PROCESSING'})
    failed_count = db.learning_materials.count_documents({'status': 'FAILED'})
    chunks_count = db.document_chunks.count_documents({})
    
    print(f"Materials in DB: {materials_count}")
    print(f"  - READY: {ready_count}")
    print(f"  - PROCESSING: {processing_count}")
    print(f"  - FAILED: {failed_count}")
    print(f"Chunks in DB: {chunks_count}")
    print("\n✅ Cleanup complete!")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
