"""
Seed competency_taxonomy.csv into MongoDB competencies collection.

Loads 42 competencies and subskills from competency_taxonomy.csv.
Preserves framework_status, level definitions, domains, and all metadata.

Usage:
  python -m app.scripts.seed_competencies
"""

import csv
import sys
from datetime import datetime, UTC
from pathlib import Path

from pymongo.database import Database

from app.core.config import get_settings
from app.core.database import initialize_database


def load_competencies_from_csv(csv_path: str) -> list[dict]:
    """
    Load competencies from CSV file.
    
    CSV columns:
      competency_id, competency_name, domain, parent_competency_id, is_subskill,
      description, level_1_definition, level_2_definition, ..., level_5_definition,
      related_skills, related_roles, framework_status
    
    Returns:
      List of competency dictionaries ready for MongoDB insertion.
    """
    competencies = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (skip header)
            try:
                competency = {
                    "code": row["competency_id"],
                    "name": row["competency_name"],
                    "domain": row["domain"],
                    "parent_competency_code": (
                        row["parent_competency_id"]
                        if row["parent_competency_id"] and row["parent_competency_id"] != "NULL"
                        else None
                    ),
                    "is_subskill": row.get("is_subskill", "N") == "Y",
                    "description": row.get("description", ""),
                    "level_definitions": {
                        "1": row.get("level_1_definition", ""),
                        "2": row.get("level_2_definition", ""),
                        "3": row.get("level_3_definition", ""),
                        "4": row.get("level_4_definition", ""),
                        "5": row.get("level_5_definition", ""),
                    },
                    "related_skills": [
                        s.strip()
                        for s in (row.get("related_skills", "") or "").split(",")
                        if s.strip()
                    ],
                    "related_roles": [
                        r.strip()
                        for r in (row.get("related_roles", "") or "").split(",")
                        if r.strip()
                    ],
                    "framework_status": row.get("framework_status", "prototype"),
                    "source": "competency_taxonomy.csv",
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
                
                competencies.append(competency)
                
            except KeyError as e:
                print(f"[ERROR] Row {row_num}: Missing column {e}")
                raise
            except Exception as e:
                print(f"[ERROR] Row {row_num}: {e}")
                raise
    
    return competencies


def main():
    """CLI entry point."""
    print("=" * 70)
    print("PHASE 3: SEED COMPETENCIES")
    print("=" * 70)
    
    try:
        # Get settings and database
        settings = get_settings()
        client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
        
        # Determine CSV path
        csv_path = "competency_taxonomy.csv"
        if not Path(csv_path).exists():
            print(f"[ERROR] {csv_path} not found")
            print(f"   Current directory: {Path.cwd()}")
            sys.exit(1)
        
        # Run seed (synchronous call)
        count = seed_competencies_sync(database, csv_path)
        
        # Close client
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


def seed_competencies_sync(database: Database, csv_path: str = "competency_taxonomy.csv") -> int:
    """
    Seed competencies from CSV into MongoDB (synchronous version).
    
    Args:
      database: MongoDB database instance
      csv_path: Path to competency_taxonomy.csv
    
    Returns:
      Number of competencies inserted
    """
    
    collection = database.competencies
    
    # Load competencies from CSV
    print(f"\n[INFO] Reading {csv_path}...")
    competencies = load_competencies_from_csv(csv_path)
    print(f"[OK] Loaded {len(competencies)} competencies from CSV")
    
    if not competencies:
        print("[WARN] No competencies to insert")
        return 0
    
    # Check for existing data
    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"\n[WARN] Collection already has {existing_count} documents")
        response = input("Clear and reimport? (y/n): ").strip().lower()
        if response == "y":
            collection.delete_many({})
            print("[OK] Cleared existing competencies")
        else:
            print("Skipping import")
            return 0
    
    # Insert competencies
    print(f"\n[INFO] Inserting {len(competencies)} competencies...")
    result = collection.insert_many(competencies)
    print(f"[OK] Inserted {len(result.inserted_ids)} competencies")
    
    # Create index on competency code (unique)
    print("\n[INFO] Creating indexes...")
    try:
        collection.create_index([("code", 1)], unique=True)
        print("[OK] Created unique index on competencies.code")
    except Exception as e:
        print(f"[WARN] Could not create unique index (may already exist): {e}")
    
    # Create index on domain
    collection.create_index([("domain", 1)])
    print("[OK] Created index on competencies.domain")
    
    # Create index on framework_status
    collection.create_index([("framework_status", 1)])
    print("[OK] Created index on competencies.framework_status")
    
    # Summary
    print(f"\n[SUMMARY]")
    print(f"  Total competencies: {len(competencies)}")
    
    # Count by type
    top_level = sum(1 for c in competencies if not c["is_subskill"])
    subskills = sum(1 for c in competencies if c["is_subskill"])
    print(f"  Top-level: {top_level}")
    print(f"  Subskills: {subskills}")
    
    # Count by domain
    domains = {}
    for c in competencies:
        domain = c["domain"]
        domains[domain] = domains.get(domain, 0) + 1
    
    print(f"  Domains:")
    for domain, count in sorted(domains.items()):
        print(f"    - {domain}: {count}")
    
    print(f"\n[OK] Competencies seeded successfully!")
    return len(competencies)


if __name__ == "__main__":
    main()
