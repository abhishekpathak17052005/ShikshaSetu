#!/usr/bin/env python
"""Diagnostic script to find RAG/LLM processing errors."""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def main():
    """Check for failed document uploads and show errors."""
    
    uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGODB_DATABASE', 'shikshasetu')
    
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client[db_name]
        
        # Test connection
        db.command('ping')
        print(f"✅ Connected to {db_name}\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return 1
    
    # Find failed materials
    print("=" * 70)
    print("FAILED MATERIALS")
    print("=" * 70)
    
    failed = list(db.learning_materials.find({'status': 'FAILED'}))
    
    if not failed:
        print("✅ No failed materials found")
    else:
        print(f"❌ Found {len(failed)} failed material(s):\n")
        for material in failed:
            print(f"📄 File: {material.get('original_filename')}")
            print(f"   Material ID: {material.get('_id')}")
            print(f"   Status: {material.get('status')}")
            print(f"   Extraction Status: {material.get('extraction_status')}")
            print(f"   Error Message: {material.get('error_message')}")
            print(f"   Chunk Count: {material.get('chunk_count', 0)}")
            print(f"   Embedding Count: {material.get('embedding_count', 0)}")
            print()
    
    # Show PROCESSING materials
    print("=" * 70)
    print("PROCESSING MATERIALS")
    print("=" * 70)
    
    processing = list(db.learning_materials.find({'status': 'PROCESSING'}))
    
    if not processing:
        print("✅ No materials currently processing")
    else:
        print(f"⏳ Found {len(processing)} material(s) in progress:")
        for material in processing:
            print(f"  - {material.get('original_filename')} (ID: {material.get('_id')})")
    print()
    
    # Show READY materials
    print("=" * 70)
    print("READY MATERIALS")
    print("=" * 70)
    
    ready = list(db.learning_materials.find({'status': 'READY'}))
    
    if not ready:
        print("⚠️  No ready materials found")
    else:
        print(f"✅ Found {len(ready)} ready material(s):")
        for material in ready:
            print(f"  - {material.get('original_filename')}")
            print(f"    Chunks: {material.get('chunk_count', 0)}, Embeddings: {material.get('embedding_count', 0)}")
    print()
    
    # Check environment
    print("=" * 70)
    print("CONFIGURATION")
    print("=" * 70)
    
    llm_provider = os.getenv('LLM_PROVIDER', 'not set')
    embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'not set')
    api_key = os.getenv('LLM_API_KEY', 'not set')
    
    print(f"LLM Provider: {llm_provider}")
    print(f"Embedding Provider: {embedding_provider}")
    print(f"API Key: {'✅ Set' if api_key != 'not set' else '❌ Not set'}")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
