#!/usr/bin/env python
"""Test RAG document upload and error handling."""

import os
import sys
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def test_upload_and_check():
    """Test document upload and check for errors."""
    
    # Create test file
    test_file = Path("test_sample.pdf")
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        print("Creating a minimal test PDF...")
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(test_file))
            c.drawString(100, 750, "This is a test PDF for RAG system.")
            c.drawString(100, 730, "It contains basic text for extraction testing.")
            c.save()
            print(f"✅ Created test PDF: {test_file}")
        except ImportError:
            print("❌ reportlab not installed. Install with: pip install reportlab")
            return 1
    
    # Step 1: Login to get token
    print("\n1️⃣  Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": "ragtester@example.com",
            "password": "test-password-123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return 1
    
    token = login_response.json()["access_token"]
    print(f"✅ Logged in, token: {token[:20]}...")
    
    # Step 2: Upload document
    print("\n2️⃣  Uploading document...")
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(test_file, "rb") as f:
        files = {"file": (test_file.name, f, "application/pdf")}
        upload_response = requests.post(
            f"{BASE_URL}/learning-materials/upload",
            files=files,
            headers=headers
        )
    
    if upload_response.status_code not in [200, 201]:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(upload_response.text)
        return 1
    
    upload_data = upload_response.json()
    material_id = upload_data["material_id"]
    print(f"✅ Uploaded successfully, Material ID: {material_id}")
    
    # Step 3: Poll for processing status
    print("\n3️⃣  Checking processing status...")
    for attempt in range(10):
        time.sleep(1)
        
        status_response = requests.get(
            f"{BASE_URL}/learning-materials/{material_id}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            data = status_response.json()
            status = data.get("status", "UNKNOWN")
            extraction = data.get("extraction_status", "UNKNOWN")
            chunks = data.get("chunk_count", 0)
            embeddings = data.get("embedding_count", 0)
            
            print(f"Attempt {attempt + 1}: Status={status}, Extraction={extraction}, Chunks={chunks}")
            
            if status == "FAILED":
                print(f"\n❌ PROCESSING FAILED")
                print(f"   Error details:")
                
                # Query database for error message
                from pymongo import MongoClient
                from dotenv import load_dotenv
                from bson import ObjectId
                
                load_dotenv()
                uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
                db_name = os.getenv('MONGODB_DATABASE', 'shikshasetu')
                
                client = MongoClient(uri)
                db = client[db_name]
                mat = db.learning_materials.find_one({"_id": ObjectId(material_id)})
                
                if mat:
                    print(f"   Error Message: {mat.get('error_message', 'N/A')}")
                    print(f"   Extraction Status: {mat.get('extraction_status', 'N/A')}")
                
                return 1
            
            elif status == "READY":
                print(f"\n✅ PROCESSING COMPLETE")
                print(f"   Chunks: {chunks}")
                print(f"   Embeddings: {embeddings}")
                
                if chunks == 0:
                    print(f"   ⚠️  WARNING: No chunks were created or indexed!")
                    return 1
                
                return 0
        
        else:
            print(f"❌ Status check failed: {status_response.status_code}")
            return 1
    
    print(f"❌ Processing timeout after 10 seconds")
    return 1

if __name__ == '__main__':
    sys.exit(test_upload_and_check())
