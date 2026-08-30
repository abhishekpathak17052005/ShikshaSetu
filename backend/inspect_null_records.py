#!/usr/bin/env python3
"""
Inspect the 5 NULL course_id records in igot_courses_enriched.csv.

Displays their raw CSV fields AND the normalized classification that
seed_learning_resources.py will assign to them in MongoDB.

Run: ..\.venv\Scripts\python.exe inspect_null_records.py
"""

import csv
import hashlib
from pathlib import Path


CSV_PATH = "igot_courses_enriched.csv"


def compute_resource_id(title: str, row_num: int) -> str:
    """Mirrors the ID generation in seed_learning_resources.py."""
    internal_hash = hashlib.md5(f"{title}{row_num}".encode()).hexdigest()[:8]
    return f"NSSTA-PROTO-{internal_hash.upper()}"


def main():
    path = Path(CSV_PATH)
    if not path.exists():
        print(f"ERROR: {CSV_PATH} not found. Run from the backend directory.")
        return

    null_records = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # row 1 = header
            course_id = row.get("course_id", "").strip()
            if not course_id or course_id == "NULL":
                null_records.append((row_num, row))

    print("=" * 80)
    print(f"NULL course_id RECORDS IN {CSV_PATH}")
    print(f"Count: {len(null_records)}")
    print("=" * 80)

    for idx, (row_num, row) in enumerate(null_records, start=1):
        title        = row.get("course_title", "").strip()
        course_id    = row.get("course_id", "").strip() or "NULL"
        provider_raw = row.get("provider", "").strip() or row.get("author_creator", "").strip() or "(empty)"
        course_type  = row.get("course_type", "").strip() or "(empty)"
        course_url   = row.get("course_url", "").strip() or "(empty)"
        source_url   = row.get("source_url", "").strip() or "(empty)"

        # --- Normalized classification (mirrors seed_learning_resources.py logic) ---
        assigned_resource_id       = compute_resource_id(title, row_num)
        assigned_provider          = "NSSTA"
        assigned_resource_type     = "TRAINING_PROGRAMME"
        assigned_verification      = "TENTATIVE"
        assigned_source_document   = "SRC-05 (NSSTA OM Annexure)"
        assigned_stored_course_id  = None  # NULL preserved

        sep = "-" * 80
        print(f"\nRECORD {idx} (CSV row {row_num})")
        print(sep)
        print("  RAW CSV FIELDS:")
        print(f"    course_title  : {title}")
        print(f"    course_id     : {course_id}")
        print(f"    provider (raw): {provider_raw}")
        print(f"    course_type   : {course_type}")
        print(f"    course_url    : {course_url}")
        print(f"    source_url    : {source_url}")
        print("  NORMALIZED CLASSIFICATION (what the seed will insert):")
        print(f"    resource_id         : {assigned_resource_id}")
        print(f"    provider            : {assigned_provider}")
        print(f"    resource_type       : {assigned_resource_type}")
        print(f"    stored course_id    : {assigned_stored_course_id}  <-- NULL preserved")
        print(f"    verification_status : {assigned_verification}")
        print(f"    source_document     : {assigned_source_document}")

    print("\n" + "=" * 80)
    print("CLASSIFICATION SUMMARY")
    print("=" * 80)
    print(f"  Total NULL course_id records : {len(null_records)}")
    print(f"  All assigned provider        : NSSTA")
    print(f"  All assigned resource_type   : TRAINING_PROGRAMME")
    print(f"  All stored course_id         : None  (NULL preserved - no IDs invented)")
    print(f"  All verification_status      : TENTATIVE")
    print("=" * 80)


if __name__ == "__main__":
    main()
