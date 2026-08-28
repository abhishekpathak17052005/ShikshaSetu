#!/usr/bin/env python3
"""Execute seeding with automatic clearing of existing collections."""

import sys
from app.core.config import get_settings
from app.core.database import initialize_database
from app.assessments.seed_capability import seed_capability_assessment_configs


def main():
    print("\n" + "=" * 80)
    print("PHASE 3: AUTOMATED SEEDING EXECUTION")
    print("=" * 80 + "\n")

    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

    print("[STEP 1] Clear existing Phase 3 collections")
    print("-" * 80)

    # ONLY clearing Phase 3 seeded collections - NOT users/assessments/evidence/quiz data
    collections_to_clear = ["competencies", "learning_resources", "learning_resource_mappings"]
    for coll_name in collections_to_clear:
        coll = database[coll_name]
        count = coll.count_documents({})
        if count > 0:
            coll.delete_many({})
            print(f"  [OK] Cleared {coll_name} ({count} documents)")
        else:
            print(f"  [OK] {coll_name} already empty")

    client.close()

    print("\n[STEP 2] Execute seed scripts")
    print("-" * 80 + "\n")

    import subprocess

    scripts = [
        ("seed_competencies.py", "Competencies"),
        ("seed_learning_resources.py", "Learning Resources"),
        ("seed_resource_mappings.py", "Resource Mappings"),
    ]

    for script, name in scripts:
        print(f"\nExecuting: {name} ({script})")
        print("-" * 40)
        try:
            result = subprocess.run(
                [sys.executable, "-m", f"app.scripts.{script.replace('.py', '')}"],
                cwd=".",
                capture_output=False,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                print(f"[OK] {name} seeded successfully")
            else:
                print(f"[FAIL] {name} seeding failed (exit code: {result.returncode})")
                return False
        except Exception as e:
            print(f"[ERROR] Error executing {name}: {e}")
            return False

    # Seed assessment configurations (this is not a subprocess script)
    print(f"\nExecuting: Assessment Configurations")
    print("-" * 40)
    try:
        client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
        count = seed_capability_assessment_configs(database)
        print(f"[OK] Assessment Configurations seeded successfully ({count} configurations)")
        client.close()
    except Exception as e:
        print(f"[FAIL] Assessment Configurations seeding failed: {e}")
        return False

    print("\n" + "=" * 80)
    print("[DONE] SEEDING COMPLETE")
    print("=" * 80 + "\n")

    # Verify counts
    print("[STEP 3] VERIFICATION: Final document counts")
    print("-" * 80)

    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

    counts = {}
    for coll_name in collections_to_clear:
        count = database[coll_name].count_documents({})
        counts[coll_name] = count
        print(f"  {coll_name}: {count}")

    print("\n[INFO] PROVIDER BREAKDOWN:")
    resources = database.learning_resources
    igot_count = resources.count_documents({"provider": "IGOT"})
    nssta_count = resources.count_documents({"provider": "NSSTA"})
    null_course_id_count = resources.count_documents(
        {"provider_specific.course_id": None, "provider": "NSSTA"}
    )

    print(f"  iGOT courses: {igot_count}")
    print(f"  NSSTA/MoSPI total: {nssta_count}")
    print(f"  NSSTA/MoSPI with NULL course_id (MoSPI Annexure): {null_course_id_count}")

    # Verify expected counts
    print("\n[INFO] EXPECTED vs ACTUAL:")
    print(f"  competencies              expected=42   actual={counts.get('competencies', 0)}")
    print(f"  learning_resources        expected=148  actual={counts.get('learning_resources', 0)}")
    print(f"  learning_resource_mappings expected=114  actual={counts.get('learning_resource_mappings', 0)}")
    print(f"  iGOT resources            expected=63   actual={igot_count}")
    print(f"  NSSTA resources           expected=85   actual={nssta_count}")
    print(f"  NSSTA with NULL course_id expected=5    actual={null_course_id_count}")

    all_match = (
        counts.get("competencies", 0) == 42
        and counts.get("learning_resources", 0) == 148
        and counts.get("learning_resource_mappings", 0) == 114
        and igot_count == 63
        and nssta_count == 85
        and null_course_id_count == 5
    )

    if all_match:
        print("\n[PASS] All counts match expected values.")
    else:
        print("\n[WARN] One or more counts do not match expected values. Review above.")

    client.close()

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
