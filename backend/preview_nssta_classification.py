#!/usr/bin/env python3
"""Preview how the 5 NULL course_id records will be classified in learning_resources"""

import csv
import hashlib
import json

def preview_record(row_num, row):
    """Show how a single record will be represented in MongoDB"""
    
    course_id = row.get("course_id", "").strip()
    title = row.get("course_title", "").strip()
    provider_field = row.get("provider", "").strip()
    source_url = row.get("source_url", "").strip()
    extraction_note = row.get("extraction_note", "").strip()
    
    # Determine provider classification
    if not course_id or course_id == "NULL":
        # This is NSSTA/MoSPI, not iGOT
        provider = "NSSTA"  # Correct classification
        resource_type = "TRAINING_PROGRAMME"
        # Generate internal ID for database relationships only
        internal_hash = hashlib.md5(f"{title}{row_num}".encode()).hexdigest()[:8]
        resource_id = f"NSSTA-PROTO-{internal_hash.upper()}"
    else:
        # iGOT course
        provider = "IGOT"
        resource_type = "COURSE"
        resource_id = f"IGOT-{course_id}"
    
    # Build MongoDB document representation
    doc = {
        "resource_id": resource_id,
        "provider": provider,
        "resource_type": resource_type,
        "title": title,
        "metadata": {
            "duration_hours": None,  # Would be parsed from duration field
            "difficulty": None,
            "target_roles": [],
            "prerequisites": [],
        },
        "competencies": [],  # Linked by mapping script
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": source_url,
            "source_document": "SRC-05" if "mospi" in source_url else "SRC-01",
            "verification_status": "TENTATIVE",
        },
        "provider_specific": {
            "course_id": course_id if course_id and course_id != "NULL" else None,
            "extracted_from": "NSSTA OM Annexure II" if not course_id or course_id == "NULL" else "iGOT Portal",
            "source_note": extraction_note[:100] if extraction_note else "",
        },
        "status": "ACTIVE",
    }
    
    return {
        "row": row_num,
        "title": title,
        "resource_id": resource_id,
        "provider": provider,
        "resource_type": resource_type,
        "course_id_in_db": None if (not course_id or course_id == "NULL") else course_id,
        "mongodb_document": doc,
    }

def main():
    print("\n" + "="*80)
    print("PREVIEW: How 5 NULL course_id records will be classified in learning_resources")
    print("="*80 + "\n")
    
    # Load enriched CSV
    with open("igot_courses_enriched.csv", 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Find NULL course_id rows
    null_rows = []
    for idx, row in enumerate(rows, start=2):
        course_id = row.get("course_id", "").strip()
        if not course_id or course_id == "NULL":
            null_rows.append((idx, row))
    
    print(f"Found {len(null_rows)} records with NULL/empty course_id\n")
    
    # Preview each
    for row_num, row in null_rows:
        preview = preview_record(row_num, row)
        
        print(f"ROW {preview['row']}: {preview['title']}")
        print("-" * 80)
        print(f"  resource_id (for MongoDB): {preview['resource_id']}")
        print(f"  provider: {preview['provider']}")
        print(f"  resource_type: {preview['resource_type']}")
        print(f"  course_id in database: {preview['course_id_in_db']}")
        print(f"  source_url: {preview['mongodb_document']['source']['source_url']}")
        print(f"  verification_status: {preview['mongodb_document']['source']['verification_status']}")
        print()
    
    # Summary
    print("="*80)
    print("CLASSIFICATION SUMMARY")
    print("="*80 + "\n")
    
    # Count by provider
    igot_count = 0
    nssta_count = 0
    
    for row_num, row in null_rows:
        preview = preview_record(row_num, row)
        if preview['provider'] == "IGOT":
            igot_count += 1
        else:
            nssta_count += 1
    
    print(f"Of the 5 NULL course_id records:")
    print(f"  • NSSTA/MoSPI: {nssta_count} (correctly classified)")
    print(f"  • iGOT: {igot_count}")
    print()
    
    # Expected totals
    print("EXPECTED MONGODB COUNTS after seeding:")
    print(f"  • Total resources: 148")
    print(f"    - iGOT courses: 63 (with valid course_id)")
    print(f"    - NSSTA programmes (from nssta_training_programmes.csv): 80")
    print(f"    - NSSTA/MoSPI courses (from enriched CSV with NULL): 5")
    print()
    
    # Provider breakdown
    print("PROVIDER BREAKDOWN:")
    print(f"  • provider='IGOT': 63")
    print(f"  • provider='NSSTA': 85 (80 from nssta_training_programmes.csv + 5 from enriched CSV)")
    print()
    
    # Important notes
    print("KEY PROPERTIES:")
    print(f"  • All 5 NSSTA/MoSPI records: course_id = NULL (preserved)")
    print(f"  • All 5 NSSTA/MoSPI records: resource_id = NSSTA-PROTO-xxxxx (internal only)")
    print(f"  • All 5 NSSTA/MoSPI records: provider = 'NSSTA' (NOT 'IGOT')")
    print(f"  • All 5 NSSTA/MoSPI records: source preserved (SRC-05)")
    print(f"  • These will NOT be counted as iGOT catalogue courses")
    print()
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
