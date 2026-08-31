#!/usr/bin/env python
"""Full E2E test: upload → process → retrieve → generate questions."""

import os
import sys
import time
import requests
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"


def get_db():
    client = MongoClient(os.getenv('MONGODB_URI'))
    return client[os.getenv('MONGODB_DATABASE')]


def ensure_test_pdf():
    test_file = Path("test_sample.pdf")
    if not test_file.exists():
        print("Creating test PDF...")
        try:
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(str(test_file))
            c.drawString(100, 750, "Introduction to Data Analysis")
            c.drawString(100, 720, "")
            c.drawString(100, 700, "Data analysis is the process of inspecting, cleaning, and")
            c.drawString(100, 680, "transforming data to discover useful information, suggest")
            c.drawString(100, 660, "conclusions, and support decision-making.")
            c.drawString(100, 640, "")
            c.drawString(100, 620, "Key concepts:")
            c.drawString(100, 600, "1. Descriptive statistics - summarising data features")
            c.drawString(100, 580, "2. Inferential statistics - drawing conclusions from samples")
            c.drawString(100, 560, "3. Data visualisation - presenting data graphically")
            c.drawString(100, 540, "4. Hypothesis testing - validating assumptions with data")
            c.save()
            print("✅ Created test_sample.pdf")
        except ImportError:
            print("❌ reportlab not installed: pip install reportlab")
            sys.exit(1)
    return test_file


def login():
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "ragtester@example.com",
        "password": "test-password-123"
    })
    if r.status_code != 200:
        print(f"❌ Login failed {r.status_code}: {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    print(f"✅ Logged in")
    return token


def upload(token, test_file):
    headers = {"Authorization": f"Bearer {token}"}
    with open(test_file, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/learning-materials/upload",
            files={"file": (test_file.name, f, "application/pdf")},
            headers=headers
        )
    if r.status_code not in [200, 201]:
        print(f"❌ Upload failed {r.status_code}: {r.text}")
        sys.exit(1)
    material_id = r.json()["material_id"]
    print(f"✅ Uploaded → Material ID: {material_id}")
    return material_id


def poll_status(token, material_id, max_attempts=15):
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(max_attempts):
        time.sleep(2)
        r = requests.get(f"{BASE_URL}/learning-materials/{material_id}", headers=headers)
        if r.status_code != 200:
            print(f"❌ Status check failed {r.status_code}: {r.text}")
            sys.exit(1)
        data = r.json()
        status = data["status"]
        chunks = data.get("chunk_count", 0)
        embeddings = data.get("embedding_count", 0)
        print(f"   [{i+1}] status={status}, chunks={chunks}, embeddings={embeddings}")
        if status == "READY":
            if chunks == 0:
                print("❌ READY but 0 chunks — embedding failed")
                sys.exit(1)
            print(f"✅ Processing complete: {chunks} chunks, {embeddings} embeddings")
            return data
        if status == "FAILED":
            db = get_db()
            mat = db.learning_materials.find_one({"_id": ObjectId(material_id)})
            error = mat.get("error_message", "unknown") if mat else "unknown"
            print(f"❌ Processing FAILED: {error}")
            sys.exit(1)
    print(f"❌ Timeout after {max_attempts} attempts")
    sys.exit(1)


def generate_questions(token, material_id):
    headers = {"Authorization": f"Bearer {token}"}

    # Pick a competency code from the database
    db = get_db()
    comp = db.competencies.find_one()
    comp_code = comp.get("code", "DA.001") if comp else "DA.001"
    print(f"   Using competency: {comp_code}")

    r = requests.post(
        f"{BASE_URL}/learning-materials/{material_id}/generate-questions",
        json={
            "competency_code": comp_code,
            "question_count": 3,
            "difficulty": "intermediate"
        },
        headers=headers
    )
    if r.status_code != 200:
        print(f"❌ Generation failed {r.status_code}: {r.text}")
        sys.exit(1)

    data = r.json()
    questions = data.get("questions", [])
    print(f"✅ Generated {len(questions)} question(s)")
    for i, q in enumerate(questions, 1):
        print(f"\n   Q{i}: {q['question'][:80]}...")
        print(f"       Answer: {q['correct_answer']}")
    return questions


def main():
    print("=" * 60)
    print("RAG FULL E2E TEST")
    print("=" * 60)

    print("\n1️⃣  Preparing test file...")
    test_file = ensure_test_pdf()

    print("\n2️⃣  Logging in...")
    token = login()

    print("\n3️⃣  Uploading document...")
    material_id = upload(token, test_file)

    print("\n4️⃣  Waiting for processing...")
    poll_status(token, material_id)

    print("\n5️⃣  Generating questions...")
    questions = generate_questions(token, material_id)

    print("\n" + "=" * 60)
    print("✅ ALL STEPS PASSED")
    print(f"   Material ID: {material_id}")
    print(f"   Questions generated: {len(questions)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
