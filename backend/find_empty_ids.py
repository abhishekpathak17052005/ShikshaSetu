#!/usr/bin/env python3
"""Find rows with empty course_id"""

import csv

with open("igot_courses_enriched.csv", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    print("\nRows with EMPTY or NULL course_id:")
    print("="*70)
    
    empty_count = 0
    for row_num, row in enumerate(reader, start=2):
        course_id = row.get("course_id", "").strip()
        if not course_id or course_id == "NULL":
            empty_count += 1
            title = row.get("course_title", "NO TITLE")[:60]
            print(f"\nRow {row_num}:")
            print(f"  ID: '{course_id}'")
            print(f"  Title: {title}")
    
    print(f"\n\nTotal rows with empty ID: {empty_count}")
