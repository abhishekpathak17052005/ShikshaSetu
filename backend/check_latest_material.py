#!/usr/bin/env python
"""Check latest material status and errors."""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DATABASE')]

# Get latest materials
mats = list(db.learning_materials.find().sort('created_at', -1).limit(5))

print("Recent materials:")
for m in mats:
    print(f"\n📄 {m['original_filename']}")
    print(f"   Status: {m['status']}")
    print(f"   Extraction Status: {m.get('extraction_status', 'N/A')}")
    if m.get('error_message'):
        print(f"   Error: {m.get('error_message')}")
    print(f"   Chunks: {m.get('chunk_count', 0)}, Embeddings: {m.get('embedding_count', 0)}")
