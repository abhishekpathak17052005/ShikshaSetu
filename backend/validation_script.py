#!/usr/bin/env python3
"""Pre-seed validation script - checks CSV integrity without touching MongoDB"""

import csv
import sys
from pathlib import Path
from collections import Counter

def validate_csv_exists(filename):
    """Check if CSV file exists"""
    path = Path(filename)
    if path.exists():
        return True, str(path)
    return False, None

def count_csv_rows(filename):
    """Count rows in CSV (excluding header)"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return sum(1 for _ in reader)
    except Exception as e:
        return None

def get_csv_columns(filename):
    """Get column names from CSV"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return reader.fieldnames
    except Exception as e:
        return None

def check_duplicates(filename, key_column):
    """Check for duplicate keys in CSV"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            keys = []
            for row in reader:
                if key_column in row:
                    keys.append(row[key_column])
            
            counts = Counter(keys)
            duplicates = {k: v for k, v in counts.items() if v > 1}
            return duplicates
    except Exception as e:
        return None

def main():
    print("\n" + "="*70)
    print("PRE-SEED VALIDATION: CSV VERIFICATION")
    print("="*70)
    
    # Define canonical files and expectations
    files_to_check = {
        "igot_courses_enriched.csv": {"rows": 68, "key": "course_id"},
        "nssta_training_programmes.csv": {"rows": 80, "key": "programme_id"},
        "competency_taxonomy.csv": {"rows": 42, "key": "competency_id"},
        "course_competency_mapping.csv": {"rows": 68, "key": None},
        "nssta_competency_mapping.csv": {"rows": 46, "key": None},
    }
    
    results = {}
    all_pass = True
    
    # Check 1: File existence
    print("\n1. FILE EXISTENCE")
    print("-" * 70)
    for filename in files_to_check.keys():
        exists, path = validate_csv_exists(filename)
        status = "✅ PASS" if exists else "❌ FAIL"
        print(f"{status}  {filename}")
        if not exists:
            all_pass = False
        results[filename] = {"exists": exists}
    
    # Check 2: Row counts
    print("\n2. ROW COUNTS")
    print("-" * 70)
    for filename, expected_info in files_to_check.items():
        count = count_csv_rows(filename)
        expected = expected_info["rows"]
        
        if count is None:
            print(f"❌ FAIL  {filename} - could not read")
            all_pass = False
        else:
            status = "✅ PASS" if count == expected else "❌ FAIL"
            print(f"{status}  {filename}")
            print(f"         Expected: {expected} | Actual: {count}")
            results[filename]["rows"] = count
            results[filename]["rows_match"] = (count == expected)
            if count != expected:
                all_pass = False
    
    # Check 3: Column verification
    print("\n3. REQUIRED COLUMNS")
    print("-" * 70)
    
    required_columns = {
        "igot_courses_enriched.csv": ["course_id", "course_title", "duration", "difficulty_level"],
        "nssta_training_programmes.csv": ["programme_id", "programme_name", "duration"],
        "competency_taxonomy.csv": ["competency_id", "competency_name", "domain"],
        "course_competency_mapping.csv": ["course_id", "competency_id"],
        "nssta_competency_mapping.csv": ["programme_id", "competency_id"],
    }
    
    for filename, required in required_columns.items():
        cols = get_csv_columns(filename)
        if cols is None:
            print(f"❌ FAIL  {filename} - could not read columns")
            all_pass = False
        else:
            missing = [c for c in required if c not in cols]
            if missing:
                print(f"❌ FAIL  {filename}")
                print(f"         Missing columns: {missing}")
                all_pass = False
            else:
                print(f"✅ PASS  {filename}")
                print(f"         All required columns present")
            results[filename]["columns_valid"] = (len(missing) == 0)
    
    # Check 4: Duplicate keys
    print("\n4. DUPLICATE KEY DETECTION")
    print("-" * 70)
    
    for filename, expected_info in files_to_check.items():
        key_col = expected_info.get("key")
        if not key_col:
            print(f"⊘ SKIP   {filename} - no primary key defined")
            continue
        
        duplicates = check_duplicates(filename, key_col)
        if duplicates is None:
            print(f"❌ FAIL  {filename} - could not check")
            all_pass = False
        elif duplicates:
            print(f"❌ FAIL  {filename}")
            print(f"         Found {len(duplicates)} duplicate keys:")
            for key, count in list(duplicates.items())[:5]:  # Show first 5
                print(f"           {key}: {count} times")
            all_pass = False
        else:
            print(f"✅ PASS  {filename}")
            print(f"         No duplicate keys")
            results[filename]["duplicates"] = 0
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\nExpected Data Counts:")
    print("  • iGOT courses: 68")
    print("  • NSSTA programmes: 80")
    print("  • Competencies: 42")
    print("  • iGOT mappings: 68")
    print("  • NSSTA mappings: 46")
    print("  • TOTAL RESOURCES: 148 (68 + 80)")
    print("  • TOTAL MAPPINGS: 114 (68 + 46)")
    
    print("\nValidation Result:")
    if all_pass:
        print("✅ ALL CSV CHECKS PASSED")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - DO NOT SEED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
