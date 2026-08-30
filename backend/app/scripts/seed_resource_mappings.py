"""
Seed learning_resource_mappings collection.

Links learning resources to competencies:
  - 68 iGOT courses to competencies (from course_competency_mapping.csv)
  - 46 NSSTA programmes to competencies (from nssta_competency_mapping.csv)

Creates bidirectional references between resources and competencies.

Usage:
  python -m app.scripts.seed_resource_mappings
"""

import csv
import sys
from datetime import datetime, UTC
from pathlib import Path

from pymongo.database import Database
from bson import ObjectId

from app.core.config import get_settings
from app.core.database import initialize_database


def translate_competency_code(csv_code: str, competencies_by_code: dict) -> str:
    """
    Translate CSV competency codes to database codes.
    
    CSV uses: STAT-SURVEY, TECH-PYTHON, etc.
    DB uses: STAT_SURVEY_DESIGN, TECH_PYTHON, etc.
    
    Strategy: Try exact match first, then try fuzzy matching.
    """
    
    # Try exact match first
    if csv_code in competencies_by_code:
        return csv_code
    
    # Map of known CSV -> DB code translations
    translation_map = {
        "STAT-SURVEY": "STAT_SURVEY_DESIGN",
        "STAT-SAMPLING": "STAT_SAMPLING",
        "STAT-NATACC": "STAT_NATIONAL_ACCOUNTS",
        "STAT-PRICE": "STAT_PRICE_STATISTICS",
        "STAT-LABOUR": "STAT_LABOUR_STATISTICS",
        "STAT-AGRI": "STAT_AGRICULTURAL_STATISTICS",
        "STAT-INDUS": "STAT_INDUSTRIAL_STATISTICS",
        "STAT-SDG": "STAT_SDG_INDICATORS",
        "STAT-META": "STAT_METADATA_STANDARDS",
        "STAT-DQ": "STAT_DATA_QUALITY_FRAMEWORKS",
        "TECH-PYTHON": "TECH_PYTHON",
        "TECH-R": "TECH_R",
        "TECH-SQL": "TECH_SQL",
        "TECH-STATA": "TECH_STATA",
        "TECH-SPSS": "TECH_SPSS",
        "TECH-SAS": "TECH_SAS",
        "TECH-GIS": "TECH_GIS",
        "TECH-DATAVIZ": "TECH_DATA_VISUALIZATION",
        "TECH-AIML": "TECH_AI_ML",
        "TECH-CLOUD": "TECH_CLOUD_COMPUTING",
        "TECH-APIS": "TECH_APIS",
        "TECH-OPENDATA": "TECH_OPEN_DATA",
        "DGOV-CYBER": "GOV_CYBERSECURITY",
        "DGOV-PRIVACY": "GOV_DATA_PRIVACY",
        "DGOV-DIGSIG": "GOV_DIGITAL_SIGNATURES",
        "DGOV-GOVCLOUD": "GOV_GOVERNMENT_CLOUD",
        "DGOV-DPUBINFRA": "GOV_DIGITAL_PUBLIC_INFRASTRUCTURE",
        "BM-LEADERSHIP": "BEH_LEADERSHIP",
        "BM-COMM": "BEH_COMMUNICATION",
        "BM-PM": "BEH_PROJECT_MANAGEMENT",
        "BM-ETHICS": "BEH_ETHICS",
        "BM-DM": "BEH_DECISION_MAKING",
        "BM-CM": "BEH_CHANGE_MANAGEMENT",
    }
    
    if csv_code in translation_map:
        translated = translation_map[csv_code]
        if translated in competencies_by_code:
            return translated
    
    # Fuzzy match: find DB code containing CSV code
    csv_parts = csv_code.replace("-", "_").upper()
    for db_code in competencies_by_code.keys():
        if csv_parts in db_code or db_code.startswith(csv_parts):
            return db_code
    
    # No match found
    return None


def load_igot_mappings(csv_path: str) -> list[dict]:
    """Load iGOT course-to-competency mappings from CSV."""
    mappings = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                mapping = {
                    "course_id": row["course_id"],
                    "competency_code": row["competency_id"],
                    "competency_name": row.get("competency_name", ""),
                    "provider": "IGOT",
                    "mapping_type": row.get("mapping_type", "DERIVED"),
                    "confidence": float(row.get("confidence", 0.5)),
                    "evidence": row.get("evidence", ""),
                    "mapping_quality": {
                        "content_alignment": float(row.get("confidence", 0.5)),
                        "accuracy_score": None,
                        "recency_score": None,
                    },
                }
                mappings.append(mapping)
                
            except (KeyError, ValueError) as e:
                print(f"[ERROR] Row {row_num}: {e}")
                raise
    
    return mappings


def load_nssta_mappings(csv_path: str) -> list[dict]:
    """Load NSSTA programme-to-competency mappings from CSV."""
    mappings = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):
            try:
                mapping = {
                    "programme_id": row["programme_id"],
                    "competency_code": row["competency_id"],
                    "competency_name": row.get("competency_name", ""),
                    "provider": "NSSTA",
                    "mapping_type": row.get("mapping_type", "DERIVED"),
                    "confidence": float(row.get("confidence", 0.55)),
                    "evidence": row.get("evidence", ""),
                    "mapping_quality": {
                        "content_alignment": float(row.get("confidence", 0.55)),
                        "accuracy_score": None,
                        "recency_score": None,
                    },
                }
                mappings.append(mapping)
                
            except (KeyError, ValueError) as e:
                print(f"[ERROR] Row {row_num}: {e}")
                raise
    
    return mappings


def seed_resource_mappings_sync(
    database: Database,
    igot_csv: str = "course_competency_mapping.csv",
    nssta_csv: str = "nssta_competency_mapping.csv",
) -> int:
    """
    Seed learning_resource_mappings collection (synchronous version).
    
    Links resources to competencies using ObjectIds from MongoDB.
    
    Args:
      database: MongoDB database instance
      igot_csv: Path to iGOT mappings CSV
      nssta_csv: Path to NSSTA mappings CSV
    
    Returns:
      Total number of mappings inserted
    """
    
    mapping_collection = database.learning_resource_mappings
    resource_collection = database.learning_resources
    competency_collection = database.competencies
    
    # Build lookup maps for ObjectIds
    print("\n[INFO] Building lookup maps...")
    
    # iGOT courses by course_id
    igot_by_course_id = {}
    for doc in resource_collection.find({"provider": "IGOT"}):
        course_id = doc.get("provider_specific", {}).get("course_id")
        if course_id:
            igot_by_course_id[course_id] = doc["_id"]
    print(f"[OK] Found {len(igot_by_course_id)} iGOT courses in resources")
    
    # NSSTA programmes by programme_id
    nssta_by_prog_id = {}
    for doc in resource_collection.find({"provider": "NSSTA"}):
        prog_id = doc.get("provider_specific", {}).get("programme_id")
        if prog_id:
            nssta_by_prog_id[prog_id] = doc["_id"]
    print(f"[OK] Found {len(nssta_by_prog_id)} NSSTA programmes in resources")
    
    # Competencies by code
    competencies_by_code = {}
    for doc in competency_collection.find():
        competencies_by_code[doc["code"]] = doc["_id"]
    print(f"[OK] Found {len(competencies_by_code)} competencies")
    
    all_mappings = []
    skipped = 0
    
    # Load and map iGOT mappings
    print(f"\n[INFO] Reading {igot_csv}...")
    if not Path(igot_csv).exists():
        print(f"[ERROR] {igot_csv} not found")
        return 0
    
    igot_mappings = load_igot_mappings(igot_csv)
    print(f"[OK] Loaded {len(igot_mappings)} iGOT mappings from CSV")
    
    for mapping in igot_mappings:
        course_id = mapping["course_id"]
        csv_competency_code = mapping["competency_code"]
        
        resource_id = igot_by_course_id.get(course_id)
        
        # Translate CSV code to DB code
        competency_code = translate_competency_code(csv_competency_code, competencies_by_code)
        competency_id = competencies_by_code.get(competency_code) if competency_code else None
        
        if not resource_id:
            print(f"  [SKIP] iGOT course {course_id} not found in resources")
            skipped += 1
            continue
        
        if not competency_id:
            print(f"  [SKIP] Competency {csv_competency_code} (translated: {competency_code}) not found")
            skipped += 1
            continue
        
        all_mappings.append({
            "resource_id": resource_id,
            "competency_id": competency_id,
            "competency_code": competency_code,
            "competency_name": mapping["competency_name"],
            "provider": "IGOT",
            "mapping_type": mapping["mapping_type"],
            "confidence": mapping["confidence"],
            "evidence": mapping["evidence"],
            "mapping_quality": mapping["mapping_quality"],
            "verified_at": None,
            "verified_by": None,
            "created_at": datetime.now(UTC),
        })
    
    print(f"[OK] Mapped {len(all_mappings)} iGOT mappings (skipped {skipped})")
    
    # Load and map NSSTA mappings
    skipped = 0
    print(f"\n[INFO] Reading {nssta_csv}...")
    if not Path(nssta_csv).exists():
        print(f"[ERROR] {nssta_csv} not found")
        return 0
    
    nssta_mappings = load_nssta_mappings(nssta_csv)
    print(f"[OK] Loaded {len(nssta_mappings)} NSSTA mappings from CSV")
    
    for mapping in nssta_mappings:
        prog_id = mapping["programme_id"]
        csv_competency_code = mapping["competency_code"]
        
        resource_id = nssta_by_prog_id.get(prog_id)
        
        # Translate CSV code to DB code
        competency_code = translate_competency_code(csv_competency_code, competencies_by_code)
        competency_id = competencies_by_code.get(competency_code) if competency_code else None
        
        if not resource_id:
            print(f"  [SKIP] NSSTA programme {prog_id} not found in resources")
            skipped += 1
            continue
        
        if not competency_id:
            print(f"  [SKIP] Competency {csv_competency_code} (translated: {competency_code}) not found")
            skipped += 1
            continue
        
        all_mappings.append({
            "resource_id": resource_id,
            "competency_id": competency_id,
            "competency_code": competency_code,
            "competency_name": mapping["competency_name"],
            "provider": "NSSTA",
            "mapping_type": mapping["mapping_type"],
            "confidence": mapping["confidence"],
            "evidence": mapping["evidence"],
            "mapping_quality": mapping["mapping_quality"],
            "verified_at": None,
            "verified_by": None,
            "created_at": datetime.now(UTC),
        })
    
    print(f"[OK] Mapped {len(nssta_mappings) - skipped} NSSTA mappings (skipped {skipped})")
    
    total = len(all_mappings)
    if not all_mappings:
        print("[WARN] No mappings to insert")
        return 0
    
    # Check for existing data
    existing_count = mapping_collection.count_documents({})
    if existing_count > 0:
        print(f"\n[WARN] Collection already has {existing_count} documents, clearing...")
        mapping_collection.delete_many({})
        print("[OK] Cleared existing mappings")
    
    # Insert mappings
    print(f"\n[INFO] Inserting {total} mappings...")
    result = mapping_collection.insert_many(all_mappings)
    print(f"[OK] Inserted {len(result.inserted_ids)} mappings")
    
    # Create indexes
    print("\n[INFO] Creating indexes...")
    mapping_collection.create_index([("resource_id", 1)])
    print("[OK] Created index on learning_resource_mappings.resource_id")
    
    mapping_collection.create_index([("competency_code", 1)])
    print("[OK] Created index on learning_resource_mappings.competency_code")
    
    mapping_collection.create_index([("provider", 1)])
    print("[OK] Created index on learning_resource_mappings.provider")
    
    mapping_collection.create_index(
        [("resource_id", 1), ("competency_code", 1)],
        unique=True
    )
    print("[OK] Created unique index on (resource_id, competency_code)")
    
    # Summary
    print(f"\n[SUMMARY]")
    igot_count = sum(1 for m in all_mappings if m["provider"] == "IGOT")
    nssta_count = sum(1 for m in all_mappings if m["provider"] == "NSSTA")
    print(f"  iGOT mappings: {igot_count}")
    print(f"  NSSTA mappings: {nssta_count}")
    print(f"  Total: {total}")
    
    print(f"\n[OK] Resource mappings seeded successfully!")
    return total


def main():
    """CLI entry point."""
    print("=" * 70)
    print("PHASE 3: SEED RESOURCE MAPPINGS")
    print("=" * 70)
    
    try:
        settings = get_settings()
        client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
        
        count = seed_resource_mappings_sync(database)
        
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
