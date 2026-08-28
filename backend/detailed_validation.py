#!/usr/bin/env python3
"""Detailed pre-seed validation - checks data integrity and mapping references"""

import csv
import sys
from pathlib import Path
from collections import defaultdict

def load_csv_as_dict(filename, key_column=None):
    """Load CSV and optionally return as dict indexed by key_column"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if key_column and data:
        result = {}
        for row in data:
            key = row.get(key_column, "").strip()
            if key:
                result[key] = row
        return result, data
    
    return None, data

def main():
    print("\n" + "="*70)
    print("DETAILED PRE-SEED VALIDATION")
    print("="*70)
    
    all_pass = True
    
    # Load all data
    print("\n📖 LOADING CSV DATA...")
    print("-" * 70)
    
    # iGOT courses
    igot_by_id, igot_all = load_csv_as_dict("igot_courses_enriched.csv", "course_id")
    print(f"✓ Loaded iGOT courses: {len(igot_all)} records")
    if igot_by_id:
        print(f"  With valid IDs: {len(igot_by_id)}")
        print(f"  Missing IDs: {len(igot_all) - len(igot_by_id)}")
    
    # NSSTA programmes
    nssta_by_id, nssta_all = load_csv_as_dict("nssta_training_programmes.csv", "programme_id")
    print(f"✓ Loaded NSSTA programmes: {len(nssta_all)} records")
    if nssta_by_id:
        print(f"  With valid IDs: {len(nssta_by_id)}")
    
    # Competencies
    comp_by_id, comp_all = load_csv_as_dict("competency_taxonomy.csv", "competency_id")
    print(f"✓ Loaded competencies: {len(comp_all)} records")
    if comp_by_id:
        print(f"  With valid IDs: {len(comp_by_id)}")
    
    # Mappings
    _, igot_maps = load_csv_as_dict("course_competency_mapping.csv")
    print(f"✓ Loaded iGOT mappings: {len(igot_maps)} records")
    
    _, nssta_maps = load_csv_as_dict("nssta_competency_mapping.csv")
    print(f"✓ Loaded NSSTA mappings: {len(nssta_maps)} records")
    
    # VALIDATION SECTION
    print("\n" + "="*70)
    print("VALIDATION CHECKS")
    print("="*70)
    
    # Check 1: Valid resource IDs in courses
    print("\n1. VALID RESOURCE IDs")
    print("-" * 70)
    
    null_igot = len(igot_all) - len(igot_by_id)
    if null_igot == 0:
        print("✅ PASS  igot_courses_enriched.csv - All IDs valid")
    else:
        print(f"❌ FAIL  igot_courses_enriched.csv - {null_igot} records missing course_id")
        all_pass = False
        # Show examples
        for i, row in enumerate(igot_all):
            if not row.get("course_id", "").strip():
                print(f"       Row {i+1}: {row.get('course_title', 'NO TITLE')}")
                if i >= 2:
                    print(f"       ... and {null_igot - 3} more")
                    break
    
    nssta_null = len(nssta_all) - len(nssta_by_id)
    if nssta_null == 0:
        print("✅ PASS  nssta_training_programmes.csv - All IDs valid")
    else:
        print(f"❌ FAIL  nssta_training_programmes.csv - {nssta_null} records missing programme_id")
        all_pass = False
    
    comp_null = len(comp_all) - len(comp_by_id)
    if comp_null == 0:
        print("✅ PASS  competency_taxonomy.csv - All IDs valid")
    else:
        print(f"❌ FAIL  competency_taxonomy.csv - {comp_null} records missing competency_id")
        all_pass = False
    
    # Check 2: Mapping integrity - iGOT
    print("\n2. MAPPING INTEGRITY - iGOT")
    print("-" * 70)
    
    missing_courses = []
    missing_competencies = []
    
    for i, mapping in enumerate(igot_maps):
        course_id = mapping.get("course_id", "").strip()
        comp_id = mapping.get("competency_id", "").strip()
        
        if course_id not in igot_by_id:
            missing_courses.append((i+1, course_id))
        if comp_id not in comp_by_id:
            missing_competencies.append((i+1, comp_id))
    
    if missing_courses:
        print(f"❌ FAIL  iGOT mappings - {len(missing_courses)} reference non-existent courses:")
        for row, cid in missing_courses[:3]:
            print(f"       Row {row}: course_id '{cid}'")
        if len(missing_courses) > 3:
            print(f"       ... and {len(missing_courses) - 3} more")
        all_pass = False
    else:
        print(f"✅ PASS  iGOT mappings - All course references valid ({len(igot_maps)} mappings)")
    
    if missing_competencies:
        print(f"❌ FAIL  iGOT mappings - {len(missing_competencies)} reference non-existent competencies:")
        for row, cid in missing_competencies[:3]:
            print(f"       Row {row}: competency_id '{cid}'")
        if len(missing_competencies) > 3:
            print(f"       ... and {len(missing_competencies) - 3} more")
        all_pass = False
    else:
        print(f"✅ PASS  iGOT mappings - All competency references valid")
    
    # Check 3: Mapping integrity - NSSTA
    print("\n3. MAPPING INTEGRITY - NSSTA")
    print("-" * 70)
    
    missing_progs = []
    missing_comp_nssta = []
    
    for i, mapping in enumerate(nssta_maps):
        prog_id = mapping.get("programme_id", "").strip()
        comp_id = mapping.get("competency_id", "").strip()
        
        if prog_id not in nssta_by_id:
            missing_progs.append((i+1, prog_id))
        if comp_id not in comp_by_id:
            missing_comp_nssta.append((i+1, comp_id))
    
    if missing_progs:
        print(f"❌ FAIL  NSSTA mappings - {len(missing_progs)} reference non-existent programmes:")
        for row, pid in missing_progs[:3]:
            print(f"       Row {row}: programme_id '{pid}'")
        all_pass = False
    else:
        print(f"✅ PASS  NSSTA mappings - All programme references valid ({len(nssta_maps)} mappings)")
    
    if missing_comp_nssta:
        print(f"❌ FAIL  NSSTA mappings - {len(missing_comp_nssta)} reference non-existent competencies:")
        for row, cid in missing_comp_nssta[:3]:
            print(f"       Row {row}: competency_id '{cid}'")
        all_pass = False
    else:
        print(f"✅ PASS  NSSTA mappings - All competency references valid")
    
    # Check 4: Expected counts
    print("\n4. EXPECTED COUNTS")
    print("-" * 70)
    
    expected = {
        "iGOT courses": (len(igot_by_id), 68),
        "NSSTA programmes": (len(nssta_by_id), 80),
        "Competencies": (len(comp_by_id), 42),
        "iGOT mappings": (len(igot_maps), 68),
        "NSSTA mappings": (len(nssta_maps), 46),
    }
    
    for name, (actual, exp) in expected.items():
        status = "✅ PASS" if actual == exp else "❌ FAIL"
        print(f"{status}  {name}: {actual}/{exp}")
        if actual != exp:
            all_pass = False
    
    # Check 5: Coverage
    print("\n5. MAPPING COVERAGE")
    print("-" * 70)
    
    mapped_courses = set()
    for mapping in igot_maps:
        course_id = mapping.get("course_id", "").strip()
        if course_id in igot_by_id:
            mapped_courses.add(course_id)
    
    unmapped_courses = set(igot_by_id.keys()) - mapped_courses
    print(f"iGOT courses: {len(mapped_courses)}/{len(igot_by_id)} have competency mappings")
    if unmapped_courses:
        print(f"  ⚠️  {len(unmapped_courses)} courses without mappings (this is OK - not all need mapping)")
    
    mapped_progs = set()
    for mapping in nssta_maps:
        prog_id = mapping.get("programme_id", "").strip()
        if prog_id in nssta_by_id:
            mapped_progs.add(prog_id)
    
    unmapped_progs = set(nssta_by_id.keys()) - mapped_progs
    print(f"NSSTA programmes: {len(mapped_progs)}/{len(nssta_by_id)} have competency mappings")
    if unmapped_progs:
        print(f"  ⚠️  {len(unmapped_progs)} programmes without mappings (expected ~40)")
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION RESULT")
    print("="*70)
    
    if all_pass:
        print("\n✅ ALL CRITICAL CHECKS PASSED")
        print("\nReady for seeding:")
        print(f"  • 68 valid iGOT courses")
        print(f"  • 80 valid NSSTA programmes")
        print(f"  • 42 valid competencies")
        print(f"  • 68 valid iGOT mappings")
        print(f"  • 46 valid NSSTA mappings")
        return 0
    else:
        print("\n❌ CRITICAL CHECKS FAILED")
        print("❌ DO NOT SEED - FIX ISSUES FIRST")
        return 1

if __name__ == "__main__":
    sys.exit(main())
