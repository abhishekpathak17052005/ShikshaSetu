"""
Dedicated Post-Sync Verification Script for ShikshaSetu Database.
"""

import sys
import io

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from bson import ObjectId
from pymongo import MongoClient
from app.core.config import get_settings
from app.core.database import initialize_database, close_database


def verify_database() -> bool:
    settings = get_settings()
    client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    print("=" * 70)
    print(f"DATABASE INTEGRITY VERIFICATION: {db.name}")
    print("=" * 70)

    all_passed = True

    try:
        # 1. Collection Counts
        print("\n--- 1. COLLECTION COUNTS ---")
        expected_counts = {
            "competencies": 42,
            "roles": 1,
            "role_requirements": 8,
            "assessment_configurations": 10,
            "question_bank": 122,
            "learning_resources": 148,
            "learning_resource_mappings": 114,
            "users": 21,
            "competency_profiles": 16,
            "competency_evidence": 72,
        }

        for coll_name, expected in expected_counts.items():
            actual = db[coll_name].count_documents({})
            status = "✅ PASS" if actual == expected else "❌ FAIL"
            if actual != expected:
                all_passed = False
            print(f"  {status} {coll_name:<30}: {actual:>3} (Expected: {expected})")

        # 2. Competencies & Codes
        print("\n--- 2. COMPETENCY CODES & INTEGRITY ---")
        comps = list(db.competencies.find())
        comp_by_id = {c["_id"]: c for c in comps}
        comp_by_code = {c["code"]: c for c in comps}

        # Verify all codes use canonical underscore format
        non_canonical_codes = [c["code"] for c in comps if "-" in c["code"]]
        if not non_canonical_codes:
            print("  ✅ PASS All 42 competencies use canonical underscore format.")
        else:
            print(f"  ❌ FAIL Found non-canonical hyphenated codes: {non_canonical_codes}")
            all_passed = False

        # 3. Role Requirements
        print("\n--- 3. ROLE REQUIREMENTS ---")
        role = db.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
        role_id = role["_id"] if role else None
        reqs = list(db.role_requirements.find({"role_id": role_id}))
        orphaned_req_comps = [r for r in reqs if r.get("competency_id") not in comp_by_id]
        if len(reqs) == 8 and not orphaned_req_comps:
            print("  ✅ PASS 8/8 Role requirements have valid competency ObjectIds.")
            for r in reqs:
                c = comp_by_id[r["competency_id"]]
                print(f"    - {c['code']:<30} | Level: {r['required_level']} | Priority: P{r['priority']} | Weight: {r['importance']}")
        else:
            print(f"  ❌ FAIL Found {len(orphaned_req_comps)} orphaned competency IDs in role_requirements.")
            all_passed = False

        # 4. Assessment Configurations
        print("\n--- 4. ASSESSMENT CONFIGURATIONS ---")
        configs = list(db.assessment_configurations.find())
        unmatched_configs = [ac for ac in configs if ac.get("competency_code") not in comp_by_code]
        if len(configs) == 10 and not unmatched_configs:
            print("  ✅ PASS 10/10 Configurations match active canonical competency codes.")
        else:
            print(f"  ❌ FAIL Found {len(unmatched_configs)} unmatched assessment configs.")
            all_passed = False

        # Verify BEH_CHANGE_MANAGEMENT is unconfigured
        beh_cm_config = db.assessment_configurations.find_one({"competency_code": "BEH_CHANGE_MANAGEMENT"})
        if beh_cm_config is None:
            print("  🔵 DATA GAP VERIFIED: BEH_CHANGE_MANAGEMENT correctly has NO configuration.")
        else:
            print("  ❌ FAIL BEH_CHANGE_MANAGEMENT unexpectedly has a configuration.")
            all_passed = False

        # 5. Question Bank
        print("\n--- 5. QUESTION BANK ---")
        questions = list(db.question_bank.find())
        unmatched_questions = [q for q in questions if q.get("competency_code") not in comp_by_code]
        dup_q_ids = len(questions) - len(set(q.get("question_id") for q in questions))
        if len(questions) == 122 and not unmatched_questions and dup_q_ids == 0:
            print("  ✅ PASS 122/122 Questions map to valid competencies with 0 duplicates.")
        else:
            print(f"  ❌ FAIL Questions check failed. Unmatched: {len(unmatched_questions)}, Duplicate IDs: {dup_q_ids}")
            all_passed = False

        # 6. Learning Resources & Mappings
        print("\n--- 6. LEARNING RESOURCES & MAPPINGS ---")
        resources = list(db.learning_resources.find())
        res_by_id = {r["_id"]: r for r in resources}
        dup_r_ids = len(resources) - len(set(r.get("resource_id") for r in resources))
        mappings = list(db.learning_resource_mappings.find())

        broken_res_fks = [m for m in mappings if m.get("resource_id") not in res_by_id]
        broken_comp_fks = [m for m in mappings if m.get("competency_id") not in comp_by_id]
        broken_comp_codes = [m for m in mappings if m.get("competency_code") not in comp_by_code]

        if dup_r_ids == 0 and not broken_res_fks and not broken_comp_fks and not broken_comp_codes:
            print(f"  ✅ PASS 148 Resources (0 duplicates), 114 Mappings (0 broken FKs, 0 code mismatches).")
        else:
            print(f"  ❌ FAIL Broken resource FKs: {len(broken_res_fks)}, Broken comp FKs: {len(broken_comp_fks)}, Code mismatches: {len(broken_comp_codes)}")
            all_passed = False

        # 7. Competency Profiles
        print("\n--- 7. COMPETENCY PROFILES ---")
        profiles = list(db.competency_profiles.find())
        orphaned_profiles = [p for p in profiles if p.get("competency_id") not in comp_by_id]
        if not orphaned_profiles:
            print(f"  ✅ PASS {len(profiles)}/{len(profiles)} Profiles have 100% valid competency ObjectIds.")
        else:
            print(f"  ❌ FAIL Found {len(orphaned_profiles)} orphaned competency profiles.")
            all_passed = False

        # 8. Competency Evidence
        print("\n--- 8. COMPETENCY EVIDENCE ---")
        evidence = list(db.competency_evidence.find())
        orphaned_evidence = [e for e in evidence if e.get("competency_id") not in comp_by_id]
        if not orphaned_evidence:
            print(f"  ✅ PASS {len(evidence)}/{len(evidence)} Evidence records have 100% valid competency ObjectIds.")
        else:
            print(f"  ❌ FAIL Found {len(orphaned_evidence)} orphaned competency evidence records.")
            all_passed = False

        # 9. Initial Assessment Questions
        print("\n--- 9. MASTER INITIAL ASSESSMENT ---")
        assessment = db.assessments.find_one()
        if assessment:
            questions = assessment.get("questions", [])
            orphaned_q_comps = [q for q in questions if q.get("competency_id") not in comp_by_id]
            if len(questions) == 24 and not orphaned_q_comps:
                print(f"  ✅ PASS 24/24 Assessment questions have valid competency ObjectIds.")
            else:
                print(f"  ❌ FAIL Found {len(orphaned_q_comps)} orphaned question competency IDs.")
                all_passed = False

        print("\n" + "=" * 70)
        final_status = "ALL VERIFICATION CHECKS PASSED ✅" if all_passed else "VERIFICATION FAILED ❌"
        print(f"OVERALL STATUS: {final_status}")
        print("=" * 70)
        return all_passed

    finally:
        close_database(client)


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
