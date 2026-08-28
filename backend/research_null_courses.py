#!/usr/bin/env python3
"""Research script to investigate 5 courses with NULL course_id"""

import csv
from pathlib import Path

def load_csv(filename):
    """Load CSV and return as list of dicts"""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def main():
    print("\n" + "="*80)
    print("RESEARCH: 5 COURSES WITH NULL course_id")
    print("="*80 + "\n")
    
    # Load enriched CSV
    enriched = load_csv("igot_courses_enriched.csv")
    
    # Find rows with NULL course_id
    null_courses = []
    for idx, row in enumerate(enriched, start=2):  # Start at 2 (header is row 1)
        course_id = row.get("course_id", "").strip()
        if not course_id or course_id == "NULL":
            null_courses.append((idx, row))
    
    print(f"Found {len(null_courses)} courses with NULL/empty course_id\n")
    
    # Load seed 56 for reference
    seed_56 = load_csv("igot_courses_seed_56.csv")
    seed_56_titles = {row.get("course_title", ""): row for row in seed_56}
    
    # Load source registry
    try:
        source_registry = load_csv("source_registry.csv")
        source_registry_dict = {row.get("source_id", ""): row for row in source_registry}
    except:
        source_registry_dict = {}
    
    print("\nDETAILED ANALYSIS OF EACH COURSE:\n")
    print("-" * 80)
    
    for row_num, course in null_courses:
        title = course.get("course_title", "").strip()
        course_url = course.get("course_url", "").strip()
        source_url = course.get("source_url", "").strip()
        extraction_note = course.get("extraction_note", "").strip()
        derived_domain = course.get("derived_domain", "").strip()
        is_seed = course.get("is_seed_record", "").strip()
        
        print(f"\nROW {row_num}:")
        print(f"  Title: {title}")
        print(f"  Current course_id: NULL")
        print(f"  course_url: {course_url}")
        print(f"  source_url: {source_url}")
        print(f"  is_seed_record: {is_seed}")
        print(f"  Extraction note: {extraction_note[:100]}")
        print(f"  Derived domain: {derived_domain}")
        
        # Check if in seed 56
        if title in seed_56_titles:
            seed_record = seed_56_titles[title]
            seed_id = seed_record.get("course_id", "")
            print(f"\n  ✓ FOUND IN SEED 56")
            print(f"    Seed course_id: {seed_id}")
        else:
            print(f"\n  ✗ NOT IN SEED 56 - NEW DISCOVERY")
        
        # Analyze extraction note for clues
        if "reconstructed from" in extraction_note.lower():
            print(f"  NOTE: Course ID reconstructed (not verified against live iGOT portal)")
        
        # Extract course ID from URL if present
        if course_url and "portal.igotkarmayogi.gov.in" in course_url:
            if "/do_" in course_url or "/ext_" in course_url:
                # Extract ID from URL pattern /do_xxx or /ext_xxx
                parts = course_url.split("/")
                for part in parts:
                    if part.startswith("do_") or part.startswith("ext_"):
                        print(f"  URL contains potential ID: {part}")
                        break
        
        print("-" * 80)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    
    # Check if any are in seed
    in_seed = sum(1 for _, row in null_courses if row.get("course_title", "") in seed_56_titles)
    not_in_seed = len(null_courses) - in_seed
    
    print(f"\nIn seed_56.csv: {in_seed}")
    print(f"New discoveries: {not_in_seed}")
    
    # Check extraction types
    reconstructed = sum(1 for _, row in null_courses if "reconstructed" in row.get("extraction_note", "").lower())
    print(f"Reconstructed from PDF: {reconstructed}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
