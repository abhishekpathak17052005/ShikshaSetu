#!/usr/bin/env python3
"""
Deep MongoDB verification after Phase 3 seeding.

Checks:
  1. Collection counts (competencies, learning_resources, mappings)
  2. Provider distribution (iGOT=63, NSSTA=85)
  3. The 5 NULL course_id records (provider=NSSTA, resource_type=TRAINING_PROGRAMME)
  4. Duplicate resource_id check
  5. Orphan mapping check (mappings with no matching resource/competency)

Run: ..\.venv\Scripts\python.exe verify_seed.py
"""

import sys
from app.core.config import get_settings
from app.core.database import initialize_database


def main():
    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

    print("=" * 70)
    print("PHASE 3 SEED VERIFICATION")
    print("=" * 70)

    errors = []

    # ------------------------------------------------------------------
    # 1. Collection counts
    # ------------------------------------------------------------------
    print("\n[1] COLLECTION COUNTS")
    print("-" * 50)
    c_count  = database.competencies.count_documents({})
    lr_count = database.learning_resources.count_documents({})
    m_count  = database.learning_resource_mappings.count_documents({})

    print(f"  competencies               : {c_count:>5}  (expected 42)")
    print(f"  learning_resources         : {lr_count:>5}  (expected 148)")
    print(f"  learning_resource_mappings : {m_count:>5}  (expected 114)")

    if c_count  != 42:  errors.append(f"competencies: got {c_count}, expected 42")
    if lr_count != 148: errors.append(f"learning_resources: got {lr_count}, expected 148")
    if m_count  != 114: errors.append(f"mappings: got {m_count}, expected 114")

    # ------------------------------------------------------------------
    # 2. Provider distribution
    # ------------------------------------------------------------------
    print("\n[2] PROVIDER DISTRIBUTION")
    print("-" * 50)
    igot_count  = database.learning_resources.count_documents({"provider": "IGOT"})
    nssta_count = database.learning_resources.count_documents({"provider": "NSSTA"})

    print(f"  iGOT  (provider=IGOT)  : {igot_count:>5}  (expected 63)")
    print(f"  NSSTA (provider=NSSTA) : {nssta_count:>5}  (expected 85)")
    print(f"  Total                  : {igot_count + nssta_count:>5}  (expected 148)")

    if igot_count  != 63: errors.append(f"iGOT count: got {igot_count}, expected 63")
    if nssta_count != 85: errors.append(f"NSSTA count: got {nssta_count}, expected 85")

    # ------------------------------------------------------------------
    # 3. The 5 NULL course_id records
    #    These came from igot_courses_enriched.csv with NULL course_id.
    #    They have resource_id prefix NSSTA-PROTO- and no course_id field.
    # ------------------------------------------------------------------
    print("\n[3] NULL course_id RECORDS (5 NSSTA/MoSPI Annexure records)")
    print("-" * 50)
    null_records = list(
        database.learning_resources.find({"resource_id": {"$regex": "^NSSTA-PROTO-"}})
    )
    print(f"  Records with NSSTA-PROTO- prefix : {len(null_records)}  (expected 5)")

    for rec in null_records:
        pid = rec.get("provider_specific", {})
        stored_id = pid.get("course_id")
        print(f"    resource_id={rec['resource_id']}")
        print(f"      title          : {rec['title']}")
        print(f"      provider       : {rec['provider']}")
        print(f"      resource_type  : {rec['resource_type']}")
        print(f"      course_id(stored): {stored_id}  <- must be None")
        ok = (
            rec["provider"] == "NSSTA"
            and rec["resource_type"] == "TRAINING_PROGRAMME"
            and stored_id is None
        )
        print(f"      classification : {'[PASS]' if ok else '[FAIL]'}")
        if not ok:
            errors.append(f"NULL record {rec['resource_id']} classification wrong")

    if len(null_records) != 5:
        errors.append(f"NULL course_id records: got {len(null_records)}, expected 5")

    # ------------------------------------------------------------------
    # 4. Duplicate resource_id check
    # ------------------------------------------------------------------
    print("\n[4] DUPLICATE resource_id CHECK")
    print("-" * 50)
    pipeline = [
        {"$group": {"_id": "$resource_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    duplicates = list(database.learning_resources.aggregate(pipeline))
    if duplicates:
        print(f"  [FAIL] {len(duplicates)} duplicate resource_id(s) found:")
        for d in duplicates:
            print(f"    {d['_id']} (count={d['count']})")
        errors.append(f"{len(duplicates)} duplicate resource_ids")
    else:
        print("  [PASS] No duplicate resource_ids")

    # ------------------------------------------------------------------
    # 5. Orphan mapping check
    #    Every mapping's resource_id must exist in learning_resources,
    #    and competency_id must exist in competencies.
    # ------------------------------------------------------------------
    print("\n[5] ORPHAN MAPPING CHECK")
    print("-" * 50)

    # Build sets of valid ObjectIds
    valid_resource_oids = set(
        str(doc["_id"]) for doc in database.learning_resources.find({}, {"_id": 1})
    )
    valid_competency_oids = set(
        str(doc["_id"]) for doc in database.competencies.find({}, {"_id": 1})
    )

    orphan_resource  = 0
    orphan_competency = 0
    for mapping in database.learning_resource_mappings.find():
        if str(mapping.get("resource_id")) not in valid_resource_oids:
            orphan_resource += 1
        if str(mapping.get("competency_id")) not in valid_competency_oids:
            orphan_competency += 1

    if orphan_resource == 0 and orphan_competency == 0:
        print("  [PASS] No orphan mappings")
    else:
        print(f"  [FAIL] {orphan_resource} mappings with missing resource")
        print(f"  [FAIL] {orphan_competency} mappings with missing competency")
        errors.append("Orphan mappings found")

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    if errors:
        print("[RESULT] FAIL - Issues found:")
        for e in errors:
            print(f"  - {e}")
        client.close()
        sys.exit(1)
    else:
        print("[RESULT] PASS - All verification checks passed.")

    client.close()


if __name__ == "__main__":
    main()
