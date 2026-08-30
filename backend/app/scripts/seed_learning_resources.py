"""
Seed learning_resources collection with iGOT courses and NSSTA programmes.

Loads:
  - 63 iGOT courses (with valid course_id) from igot_courses_enriched.csv
  - 5 NSSTA/MoSPI courses (NULL course_id) from igot_courses_enriched.csv
  - 80 NSSTA programmes from nssta_training_programmes.csv

Total: 148 learning resources

Combines both into a single learning_resources collection with provider field.

Usage:
  python -m app.scripts.seed_learning_resources
"""

import csv
import hashlib
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from pymongo.database import Database

from app.core.config import get_settings
from app.core.database import initialize_database


def parse_duration_hours(duration_str: Optional[str]) -> Optional[float]:
    """
    Parse duration string to hours (float).

    Handles formats like:
      "2h 42m" -> 2.7
      "5 day(s)" -> 40 (5 days * 8 hours/day)
      "Half day / 1 day" -> None (ambiguous)

    Returns:
      Duration in hours, or None if cannot parse
    """
    if not duration_str or duration_str == "NULL":
        return None

    duration_str = duration_str.strip()

    # Handle "Xh Ym" format (iGOT)
    if "h" in duration_str or "m" in duration_str:
        hours = 0.0
        parts = duration_str.split()

        for part in parts:
            if "h" in part:
                try:
                    hours += int(part.rstrip("h"))
                except ValueError:
                    return None
            elif "m" in part:
                try:
                    hours += int(part.rstrip("m")) / 60
                except ValueError:
                    return None

        return round(hours, 2) if hours > 0 else None

    # Handle "X day(s)" format (NSSTA)
    if "day" in duration_str.lower():
        parts = duration_str.split()
        try:
            days = int(parts[0])
            # Assume 8-hour training day
            return days * 8
        except (ValueError, IndexError):
            return None

    return None


def load_igot_courses(csv_path: str) -> list[dict]:
    """Load iGOT courses from igot_courses_enriched.csv.

    Handles both iGOT courses (valid course_id) and NSSTA/MoSPI training
    courses (NULL course_id - from official MoSPI SRC-05 document).
    """
    courses = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                course_id = row.get("course_id", "").strip()
                title = row.get("course_title", "").strip()
                course_url = row.get("course_url", "").strip() or row.get("source_url", "").strip()
                extraction_note = row.get("extraction_note", "").strip()

                # Determine if this is iGOT or NSSTA/MoSPI
                if not course_id or course_id == "NULL":
                    # This is a NSSTA/MoSPI training course (from official MoSPI document)
                    # Generate internal ID for database reference
                    internal_hash = hashlib.md5(f"{title}{row_num}".encode()).hexdigest()[:8]
                    resource_id = f"NSSTA-PROTO-{internal_hash.upper()}"
                    provider = "NSSTA"
                    resource_type = "TRAINING_PROGRAMME"
                    verification_status = "TENTATIVE"
                    source_document = "SRC-05 (NSSTA OM Annexure)"
                    stored_course_id = None  # NULL - preserved, never invented
                else:
                    # This is an iGOT course
                    resource_id = f"IGOT-{course_id}"
                    provider = "IGOT"
                    resource_type = "COURSE"
                    verification_status = "VERIFIED"
                    source_document = "SRC-01 (seed) or SRC-02 (discovered)"
                    stored_course_id = course_id

                course = {
                    "resource_id": resource_id,
                    "provider": provider,
                    "resource_type": resource_type,
                    "title": title,
                    "metadata": {
                        "duration_hours": parse_duration_hours(row.get("duration")),
                        "difficulty": row.get("difficulty_level") or None,
                        "target_roles": [],
                        "prerequisites": [],
                    },
                    "competencies": [],  # Linked by seed_resource_mappings
                    "source": {
                        "source_type": "GOVERNMENT_PUBLICATION",
                        "source_url": course_url,
                        "source_document": source_document,
                        "verification_status": verification_status,
                    },
                    "provider_specific": {
                        "course_id": stored_course_id,  # None for NSSTA/MoSPI records
                        "course_url": course_url,
                        "provider_name": row.get("provider") or row.get("author_creator"),
                        "extraction_note": extraction_note,
                    },
                    "status": "ACTIVE",
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
                courses.append(course)

            except KeyError as e:
                print(f"[ERROR] Row {row_num}: Missing column {e}")
                raise
            except Exception as e:
                print(f"[ERROR] Row {row_num}: {e}")
                raise

    return courses


def load_nssta_programmes(csv_path: str) -> list[dict]:
    """Load NSSTA programmes from nssta_training_programmes.csv."""
    programmes = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                programme = {
                    "resource_id": f"NSSTA-{row['programme_id']}",
                    "provider": "NSSTA",
                    "resource_type": "TRAINING_PROGRAMME",
                    "title": row.get("programme_name", ""),
                    "metadata": {
                        "duration_hours": parse_duration_hours(row.get("duration")),
                        "difficulty": None,  # NSSTA doesn't specify difficulty
                        "target_roles": [],
                        "prerequisites": [],
                    },
                    "competencies": [],  # Linked by seed_resource_mappings
                    "source": {
                        "source_type": "GOVERNMENT_PUBLICATION",
                        "source_url": row.get("source_url"),
                        "source_document": "SRC-03 (FY 2025-26 Advance Training Calendar)",
                        "verification_status": "TENTATIVE",  # Calendar marked tentative
                    },
                    "provider_specific": {
                        "programme_id": row["programme_id"],
                        "training_category": row.get("training_category"),
                        "batch_size": (
                            int(row["batch_size"]) if row.get("batch_size", "").isdigit() else None
                        ),
                        "venue": row.get("venue"),
                        "institute": row.get("institute"),
                        "training_year": row.get("training_year"),
                        "schedule": row.get("schedule"),
                        "recommended_by_TPAC": row.get("recommended_by_TPAC") == "Y",
                    },
                    "status": "ACTIVE",
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
                programmes.append(programme)

            except KeyError as e:
                print(f"[ERROR] Row {row_num}: Missing column {e}")
                raise
            except Exception as e:
                print(f"[ERROR] Row {row_num}: {e}")
                raise

    return programmes


def seed_learning_resources_sync(
    database: Database,
    igot_csv: str = "igot_courses_enriched.csv",
    nssta_csv: str = "nssta_training_programmes.csv",
) -> int:
    """
    Seed learning_resources collection (synchronous version).

    Args:
      database: MongoDB database instance
      igot_csv: Path to iGOT courses CSV
      nssta_csv: Path to NSSTA programmes CSV

    Returns:
      Total number of resources inserted
    """

    collection = database.learning_resources
    all_resources = []

    # Load iGOT courses (includes 5 NSSTA/MoSPI NULL-course_id records)
    print(f"\n[INFO] Reading {igot_csv}...")
    if not Path(igot_csv).exists():
        print(f"[ERROR] {igot_csv} not found")
        return 0

    igot_courses = load_igot_courses(igot_csv)
    igot_with_id   = [r for r in igot_courses if r["provider"] == "IGOT"]
    nssta_proto    = [r for r in igot_courses if r["provider"] == "NSSTA"]
    all_resources.extend(igot_courses)
    print(f"[OK] Loaded {len(igot_courses)} rows from {igot_csv}")
    print(f"     -> {len(igot_with_id)} iGOT courses (valid course_id)")
    print(f"     -> {len(nssta_proto)} NSSTA/MoSPI courses (NULL course_id - classified NSSTA)")

    # Load NSSTA programmes
    print(f"\n[INFO] Reading {nssta_csv}...")
    if not Path(nssta_csv).exists():
        print(f"[ERROR] {nssta_csv} not found")
        return 0

    nssta_programmes = load_nssta_programmes(nssta_csv)
    all_resources.extend(nssta_programmes)
    print(f"[OK] Loaded {len(nssta_programmes)} NSSTA programmes from {nssta_csv}")

    total = len(all_resources)
    print(f"\n[INFO] Total resources to insert: {total}")

    if not all_resources:
        print("[WARN] No resources to insert")
        return 0

    # Check for existing data
    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"\n[WARN] Collection already has {existing_count} documents")
        response = input("Clear and reimport? (y/n): ").strip().lower()
        if response == "y":
            collection.delete_many({})
            print("[OK] Cleared existing resources")
        else:
            print("Skipping import")
            return 0

    # Insert resources
    print(f"\n[INFO] Inserting {total} learning resources...")
    result = collection.insert_many(all_resources)
    print(f"[OK] Inserted {len(result.inserted_ids)} resources")

    # Create indexes
    print("\n[INFO] Creating indexes...")
    collection.create_index([("provider", 1)])
    print("[OK] Created index on learning_resources.provider")

    collection.create_index([("status", 1)])
    print("[OK] Created index on learning_resources.status")

    collection.create_index([("resource_id", 1)], unique=True)
    print("[OK] Created unique index on learning_resources.resource_id")

    # Summary
    igot_count  = sum(1 for r in all_resources if r["provider"] == "IGOT")
    nssta_count = sum(1 for r in all_resources if r["provider"] == "NSSTA")
    null_count  = sum(
        1 for r in all_resources
        if r["provider"] == "NSSTA" and r["provider_specific"].get("course_id") is None
    )

    print(f"\n[SUMMARY]")
    print(f"  Total resources   : {total}")
    print(f"  iGOT (IGOT)      : {igot_count}")
    print(f"  NSSTA total      : {nssta_count}")
    print(f"    of which NSSTA/MoSPI NULL course_id: {null_count}")

    if null_count > 0:
        print(f"\n[INFO] NSSTA/MoSPI NULL course_id records (provider=NSSTA, course_id=None):")
        for res in [r for r in all_resources if r["provider"] == "NSSTA" and r["provider_specific"].get("course_id") is None]:
            print(f"    resource_id={res['resource_id']}  title={res['title']}")

    print(f"\n[OK] Learning resources seeded successfully!")
    return total


def main():
    """CLI entry point."""
    print("=" * 70)
    print("PHASE 3: SEED LEARNING RESOURCES")
    print("=" * 70)

    try:
        settings = get_settings()
        client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)

        count = seed_learning_resources_sync(database)

        client.close()

        if count > 0:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
