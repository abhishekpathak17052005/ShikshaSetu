"""
Unified Idempotent Master Data Synchronization Script for ShikshaSetu.

This script synchronizes and normalizes all core framework data in dependency order:
1. COMPETENCIES (42 canonical competencies with canonical underscore codes)
2. ROLES (STATISTICAL_OFFICER)
3. ROLE REQUIREMENTS (8 requirements linked to active competency ObjectIds)
4. ASSESSMENT CONFIGURATIONS (10 configurations with canonical codes; BEH_CHANGE_MANAGEMENT left as data gap)
5. QUESTION BANK (122 questions with canonical codes)
6. LEARNING RESOURCES (148 resources: 63 iGOT + 85 NSSTA)
7. LEARNING RESOURCE MAPPINGS (114 mappings linked to active resource and competency ObjectIds)
8. USERS (Preserves all 21 users with valid role_id)
9. ASSESSMENTS (Initial assessment master document with active competency ObjectIds)
10. COMPETENCY PROFILES (Repairs profile competency ObjectIds for active demo users)
11. COMPETENCY EVIDENCE (Repairs evidence competency ObjectIds for active demo users)

Usage:
  python -m app.scripts.seed_master
"""

import csv
from datetime import datetime, UTC
from pathlib import Path
from bson import ObjectId
from pymongo import UpdateOne, ReturnDocument
from pymongo.database import Database

from app.core.config import get_settings
from app.core.database import initialize_database, close_database
from app.core.framework_indexes import ensure_framework_indexes
from app.questions.seed import seed_questions
from app.auth.security import hash_password
from app.scripts.seed_learning_resources import (
    load_igot_courses,
    load_nssta_programmes,
)

# ==============================================================================
# CANONICAL CODE NORMALIZATION MAPPING
# ==============================================================================
CODE_NORMALIZATION_MAP = {
    # Statistical
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
    # Technical
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
    "TECH-API": "TECH_APIS",
    "TECH-APIS": "TECH_APIS",
    "TECH-OPENDATA": "TECH_OPEN_DATA",
    # Technical Subskills
    "TECH-PYTHON-FUND": "TECH_PYTHON_FUNDAMENTALS",
    "TECH-PYTHON-NUMPY": "TECH_PYTHON_NUMPY",
    "TECH-PYTHON-PANDAS": "TECH_PYTHON_PANDAS",
    "TECH-PYTHON-DATACLEAN": "TECH_PYTHON_DATA_CLEANING",
    "TECH-PYTHON-STATPROG": "TECH_PYTHON_STATISTICAL_PROGRAMMING",
    "TECH-PYTHON-VIZ": "TECH_PYTHON_VISUALIZATION",
    "TECH-AIML-ML": "TECH_AIML_MACHINE_LEARNING_FUNDAMENTALS",
    "TECH-AIML-GENAI": "TECH_AIML_GENERATIVE_AI_LLMS",
    "TECH-AIML-BIGDATA": "TECH_AIML_BIG_DATA_DATA_MINING",
    # Digital Governance
    "DGOV-CYBER": "DIGOV_CYBERSECURITY",
    "DGOV-PRIVACY": "DIGOV_DATA_PRIVACY",
    "DGOV-DSIG": "DIGOV_DIGITAL_SIGNATURES",
    "DGOV-DIGSIG": "DIGOV_DIGITAL_SIGNATURES",
    "DGOV-CLOUD": "DIGOV_GOVERNMENT_CLOUD",
    "DGOV-GOVCLOUD": "DIGOV_GOVERNMENT_CLOUD",
    "DGOV-DPI": "DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE",
    "DGOV-DPUBINFRA": "DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE",
    # Behavioural / Managerial
    "BM-LEADERSHIP": "BEH_LEADERSHIP",
    "BM-COMM": "BEH_COMMUNICATION",
    "BM-PM": "BEH_PROJECT_MANAGEMENT",
    "BM-ETHICS": "BEH_ETHICS",
    "BM-DECISION": "BEH_DECISION_MAKING",
    "BM-DM": "BEH_DECISION_MAKING",
    "BM-CHANGE": "BEH_CHANGE_MANAGEMENT",
    "BM-CM": "BEH_CHANGE_MANAGEMENT",
}

# Legacy ObjectId to Canonical Code Mapping (from initial assessment)
LEGACY_OID_TO_CODE = {
    ObjectId("6a8fe8048524f6da8ebb9861"): "STAT_SAMPLING",
    ObjectId("6a8fe8048524f6da8ebb9860"): "STAT_SURVEY_DESIGN",
    ObjectId("6a8fe8048524f6da8ebb9869"): "STAT_DATA_QUALITY_FRAMEWORKS",
    ObjectId("6a8fe8048524f6da8ebb986a"): "TECH_PYTHON",
    ObjectId("6a8fe8048524f6da8ebb986c"): "TECH_SQL",
    ObjectId("6a8fe8048524f6da8ebb9871"): "TECH_DATA_VISUALIZATION",
    ObjectId("6a8fe8048524f6da8ebb9870"): "TECH_GIS",
    ObjectId("6a8fe8048524f6da8ebb9872"): "TECH_AI_ML",
}


def normalize_code(code: str) -> str:
    """Normalize any code format into its canonical underscore representation."""
    if not code:
        return ""
    code_clean = code.strip().upper()
    if code_clean in CODE_NORMALIZATION_MAP:
        return CODE_NORMALIZATION_MAP[code_clean]
    # If already canonical or matches underscore variant
    return code_clean.replace("-", "_")


def normalize_domain(raw_domain: str) -> str:
    raw = (raw_domain or "").strip().lower()
    if "stat" in raw:
        return "STATISTICAL"
    if "tech" in raw:
        return "TECHNICAL"
    if "gov" in raw:
        return "DIGITAL_GOVERNANCE"
    if "beh" in raw or "manag" in raw:
        return "BEHAVIOURAL_MANAGERIAL"
    return "STATISTICAL"


def sync_competencies(database: Database, base_dir: Path) -> dict[str, ObjectId]:
    """
    Step 1: Synchronize all 42 canonical competencies from competency_taxonomy.csv.
    Returns: Mapping of canonical_code -> ObjectId.
    """
    print("\n[1/11] Synchronizing Competencies...")
    csv_path = base_dir / "competency_taxonomy.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}")

    now = datetime.now(UTC)
    comp_map = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_code = row["competency_id"]
            canonical_code = normalize_code(raw_code)
            parent_raw = row.get("parent_competency_id")
            parent_code = (
                normalize_code(parent_raw)
                if parent_raw and parent_raw != "NULL"
                else None
            )

            doc = {
                "code": canonical_code,
                "name": row["competency_name"],
                "domain": normalize_domain(row.get("domain", "")),
                "parent_competency_code": parent_code,
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
                "source_type": "PROTOTYPE",
                "source_reference": "competency_taxonomy.csv",
                "status": "active",
                "source": "competency_taxonomy.csv",
                "updated_at": now,
            }

            # Upsert by canonical code
            res = database.competencies.find_one_and_update(
                {"code": canonical_code},
                {"$set": doc, "$setOnInsert": {"created_at": now}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
            comp_map[canonical_code] = res["_id"]

    # Also remove any old hyphenated duplicate records if present with distinct codes
    for raw_code, canonical_code in CODE_NORMALIZATION_MAP.items():
        if raw_code != canonical_code:
            database.competencies.delete_many({"code": raw_code})

    print(f"  -> Synced {len(comp_map)} canonical competencies.")
    return comp_map


def sync_roles(database: Database) -> ObjectId:
    """
    Step 2: Synchronize STATISTICAL_OFFICER role.
    Returns: Role ObjectId.
    """
    print("\n[2/11] Synchronizing Roles...")
    now = datetime.now(UTC)
    role_doc = {
        "role_code": "STATISTICAL_OFFICER",
        "role_name": "Statistical Officer",
        "domain": "Statistical Analysis & Governance",
        "description": "Officer responsible for statistical survey design, sampling, data processing, and analysis in official statistics.",
        "status": "active",
        "source": "master_seed",
        "updated_at": now,
    }

    res = database.roles.find_one_and_update(
        {"role_code": "STATISTICAL_OFFICER"},
        {"$set": role_doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    role_id = res["_id"]
    print(f"  -> Active role: STATISTICAL_OFFICER (ID: {role_id})")
    return role_id


def sync_role_requirements(
    database: Database, role_id: ObjectId, comp_map: dict[str, ObjectId]
) -> None:
    """
    Step 3: Synchronize 8 role requirements for STATISTICAL_OFFICER with active competency IDs.
    """
    print("\n[3/11] Synchronizing Role Requirements...")
    requirements_spec = [
        ("STAT_SAMPLING", 4, 1, 1.0),
        ("STAT_SURVEY_DESIGN", 4, 1, 1.0),
        ("STAT_DATA_QUALITY_FRAMEWORKS", 4, 1, 1.0),
        ("TECH_PYTHON", 3, 2, 0.75),
        ("TECH_SQL", 3, 2, 0.75),
        ("TECH_DATA_VISUALIZATION", 3, 2, 0.75),
        ("TECH_GIS", 2, 3, 0.50),
        ("TECH_AI_ML", 2, 3, 0.50),
    ]

    now = datetime.now(UTC)
    database.role_requirements.delete_many({"role_id": role_id})

    req_docs = []
    for code, req_level, priority, importance in requirements_spec:
        comp_id = comp_map.get(code)
        if not comp_id:
            raise ValueError(f"Competency code {code} not found in comp_map!")
        req_docs.append({
            "role_id": role_id,
            "competency_id": comp_id,
            "required_level": req_level,
            "priority": priority,
            "importance": importance,
            "framework_status": "prototype",
            "created_at": now,
            "updated_at": now,
        })

    database.role_requirements.insert_many(req_docs)
    print(f"  -> Inserted {len(req_docs)} role requirements for STATISTICAL_OFFICER.")


def sync_assessment_configurations(database: Database) -> None:
    """
    Step 4: Synchronize 10 assessment configurations with canonical codes.
    BEH_CHANGE_MANAGEMENT is intentionally excluded as a legitimate data gap.
    """
    print("\n[4/11] Synchronizing Assessment Configurations...")
    now = datetime.now(UTC)
    configs = [
        ("TECH_PYTHON", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 30),
        ("TECH_SQL", ["MCQ", "SCENARIO"], 12, "MIXED", 70.0, 35),
        ("TECH_R", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 30),
        ("STAT_SAMPLING", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 30),
        ("STAT_SURVEY_DESIGN", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 30),
        ("DIGOV_CYBERSECURITY", ["MCQ", "SCENARIO"], 12, "MIXED", 70.0, 35),
        ("DIGOV_DATA_PRIVACY", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 30),
        ("BEH_LEADERSHIP", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 25),
        ("BEH_COMMUNICATION", ["MCQ", "SCENARIO"], 10, "MIXED", 70.0, 25),
        ("BEH_PROJECT_MANAGEMENT", ["MCQ", "SCENARIO"], 12, "MIXED", 70.0, 35),
    ]

    database.assessment_configurations.delete_many({})
    docs = []
    for code, q_types, num_q, diff, threshold, time_limit in configs:
        docs.append({
            "competency_code": code,
            "assessment_types": q_types,
            "number_of_questions": num_q,
            "difficulty": diff,
            "passing_threshold": threshold,
            "time_limit_minutes": time_limit,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        })

    database.assessment_configurations.insert_many(docs)
    print(f"  -> Inserted {len(docs)} assessment configurations.")


def sync_question_bank(database: Database) -> None:
    """
    Step 5: Synchronize 122 questions in question_bank with canonical codes.
    """
    print("\n[5/11] Synchronizing Question Bank...")
    database.question_bank.delete_many({})
    res = seed_questions(database)
    total_inserted = res.get("total_questions", database.question_bank.count_documents({})) if isinstance(res, dict) else database.question_bank.count_documents({})
    by_comp = res.get("by_competency", {}) if isinstance(res, dict) else {}
    print(f"  -> Seeded {total_inserted} questions across {len(by_comp)} competencies.")


def sync_learning_resources(database: Database, base_dir: Path) -> dict[str, ObjectId]:
    """
    Step 6: Synchronize 148 learning resources from CSVs.
    Returns: Mapping of resource_id (string) -> ObjectId.
    """
    print("\n[6/11] Synchronizing Learning Resources...")
    igot_path = str(base_dir / "igot_courses_enriched.csv")
    nssta_path = str(base_dir / "nssta_training_programmes.csv")

    courses = load_igot_courses(igot_path)
    programmes = load_nssta_programmes(nssta_path)
    all_resources = courses + programmes

    now = datetime.now(UTC)
    res_map = {}

    for r in all_resources:
        rid = r["resource_id"]
        set_doc = dict(r)
        created_at_val = set_doc.pop("created_at", now)
        set_doc["updated_at"] = now
        res = database.learning_resources.find_one_and_update(
            {"resource_id": rid},
            {"$set": set_doc, "$setOnInsert": {"created_at": created_at_val}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        res_map[rid] = res["_id"]

    print(f"  -> Synced {len(res_map)} learning resources.")
    return res_map


def sync_learning_resource_mappings(
    database: Database,
    base_dir: Path,
    res_map: dict[str, ObjectId],
    comp_map: dict[str, ObjectId],
) -> None:
    """
    Step 7: Synchronize 114 learning resource mappings with active ObjectIds and canonical codes.
    """
    print("\n[7/11] Synchronizing Learning Resource Mappings...")
    course_map_csv = base_dir / "course_competency_mapping.csv"
    nssta_map_csv = base_dir / "nssta_competency_mapping.csv"

    now = datetime.now(UTC)
    mappings = []

    # 1. iGOT mappings
    if course_map_csv.exists():
        with open(course_map_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                course_id = row.get("course_id", "").strip()
                if not course_id or course_id == "NULL":
                    continue
                full_rid = f"IGOT-{course_id}"
                r_oid = res_map.get(full_rid)
                if not r_oid:
                    continue

                raw_comp = row.get("competency_id", "").strip()
                canon_code = normalize_code(raw_comp)
                c_oid = comp_map.get(canon_code)
                if not c_oid:
                    continue

                mappings.append({
                    "resource_id": r_oid,
                    "competency_id": c_oid,
                    "competency_code": canon_code,
                    "competency_name": row.get("competency_name", ""),
                    "provider": "IGOT",
                    "mapping_type": row.get("mapping_type", "DERIVED"),
                    "confidence": float(row.get("confidence", 0.5) or 0.5),
                    "evidence": row.get("evidence", ""),
                    "created_at": now,
                })

    # 2. NSSTA mappings
    if nssta_map_csv.exists():
        with open(nssta_map_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prog_id = row.get("programme_id", "").strip()
                if not prog_id:
                    continue
                full_rid = f"NSSTA-{prog_id}"
                r_oid = res_map.get(full_rid)
                if not r_oid:
                    continue

                raw_comp = row.get("competency_id", "").strip()
                canon_code = normalize_code(raw_comp)
                c_oid = comp_map.get(canon_code)
                if not c_oid:
                    continue

                mappings.append({
                    "resource_id": r_oid,
                    "competency_id": c_oid,
                    "competency_code": canon_code,
                    "competency_name": row.get("competency_name", ""),
                    "provider": "NSSTA",
                    "mapping_type": row.get("mapping_type", "MANUAL_PRIMARY"),
                    "confidence": float(row.get("confidence", 1.0) or 1.0),
                    "evidence": row.get("evidence", ""),
                    "created_at": now,
                })

    database.learning_resource_mappings.delete_many({})
    if mappings:
        database.learning_resource_mappings.insert_many(mappings)

    print(f"  -> Inserted {len(mappings)} learning resource mappings.")


def sync_users(database: Database, default_role_id: ObjectId) -> None:
    """
    Step 8: Resolve department-specific role_id for each user, migrate legacy access roles,
    seed multi-department demo accounts, and safely reconcile user competency profiles.
    """
    print("\n[8/11] Verifying & Preserving Users & Department Roles...")
    now = datetime.now(UTC)
    from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies

    # 1. Migrate legacy access_role: EMPLOYEE -> OFFICIAL
    res_access = database.users.update_many(
        {"$or": [{"access_role": "EMPLOYEE"}, {"access_role": {"$exists": False}}]},
        {"$set": {"access_role": "OFFICIAL", "updated_at": now}},
    )

    # 2. Seed / Upsert the standard multi-department system role demo accounts
    demo_accounts = [
        {
            "email": "official@shikshasetu.gov.in",
            "full_name": "Demo Official (Statistical Officer)",
            "designation": "Statistical Officer",
            "department": "National Sample Survey Office (NSSO)",
            "employee_id": "DEMO-OFF-001",
            "access_role": "OFFICIAL",
            "status": "active",
        },
        {
            "email": "trainer@shikshasetu.gov.in",
            "full_name": "Demo Trainer (NSSTA Faculty)",
            "designation": "Senior Faculty & Trainer",
            "department": "National Statistical Systems Training Academy (NSSTA)",
            "employee_id": "DEMO-TRN-001",
            "access_role": "TRAINER",
            "status": "active",
        },
        {
            "email": "admin@shikshasetu.gov.in",
            "full_name": "Demo Administrator (MoSPI HQ)",
            "designation": "Director (Capability & Human Capital)",
            "department": "Ministry of Statistics & Programme Implementation",
            "employee_id": "DEMO-ADM-001",
            "access_role": "ADMIN",
            "status": "active",
        },
        {
            "email": "edu.officer@shikshasetu.gov.in",
            "full_name": "Dr. Ramesh Verma (Education Officer)",
            "designation": "Teacher",
            "department": "Ministry of Education",
            "employee_id": "DEMO-EDU-001",
            "access_role": "OFFICIAL",
            "status": "active",
        },
        {
            "email": "meity.officer@shikshasetu.gov.in",
            "full_name": "Priya Sundaram (Informatics Officer)",
            "designation": "Informatics Officer / Scientist 'B'",
            "department": "Ministry of Electronics and Information Technology (MeitY)",
            "employee_id": "DEMO-MEITY-001",
            "access_role": "OFFICIAL",
            "status": "active",
        },
        {
            "email": "finance.officer@shikshasetu.gov.in",
            "full_name": "Amitabh Sen (Accounts Officer)",
            "designation": "Accounts Officer (AAO / AO)",
            "department": "Ministry of Finance",
            "employee_id": "DEMO-FIN-001",
            "access_role": "OFFICIAL",
            "status": "active",
        },
    ]

    for acc in demo_accounts:
        resolved_r_oid = resolve_role_for_user(database, acc["department"], acc["designation"]) or default_role_id
        existing = database.users.find_one({"email": acc["email"]})
        if not existing:
            doc = {
                **acc,
                "role_id": resolved_r_oid,
                "password_hash": hash_password("Password123!"),
                "created_at": now,
                "updated_at": now,
                "last_login_at": None,
            }
            database.users.insert_one(doc)
        else:
            database.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "role_id": resolved_r_oid,
                    "access_role": acc["access_role"],
                    "designation": acc["designation"],
                    "department": acc["department"],
                    "status": "active",
                    "updated_at": now,
                }}
            )

    # 3. Resolve role and reconcile competency profiles for all active users
    all_users = list(database.users.find({}))
    reconciled_count = 0
    for u in all_users:
        dept = u.get("department")
        desig = u.get("designation")
        user_role_id = resolve_role_for_user(database, dept, desig) or default_role_id
        reconcile_user_competencies(database, u["_id"], user_role_id)
        reconciled_count += 1

    total_users = database.users.count_documents({})
    print(f"  -> Total users: {total_users} (Reconciled department roles for {reconciled_count} users, migrated access_role: {res_access.modified_count}).")



def sync_initial_assessment(
    database: Database, comp_map: dict[str, ObjectId]
) -> None:
    """
    Step 9: Synchronize Initial Competency Assessment document with active competency IDs.
    """
    print("\n[9/11] Synchronizing Initial Competency Assessment...")
    assessment = database.assessments.find_one()
    if not assessment:
        print("  -> No initial assessment found to update.")
        return

    questions = assessment.get("questions", [])
    updated_questions = []
    for q in questions:
        qid = q.get("question_id", "")
        # Extract code from question_id: e.g. self_stat_sampling -> STAT_SAMPLING
        parts = qid.split("_", 1)
        suffix = parts[1].upper() if len(parts) > 1 else ""
        canon_code = normalize_code(suffix)
        c_oid = comp_map.get(canon_code)
        if c_oid:
            q["competency_id"] = c_oid
        updated_questions.append(q)

    database.assessments.update_one(
        {"_id": assessment["_id"]},
        {"$set": {"questions": updated_questions, "updated_at": datetime.now(UTC)}},
    )
    print(f"  -> Updated {len(updated_questions)} questions in master assessment.")


def repair_competency_profiles(
    database: Database, comp_map: dict[str, ObjectId]
) -> None:
    """
    Step 10: Repair competency_profiles by resolving old competency IDs to canonical ones.
    """
    print("\n[10/11] Repairing Competency Profiles...")
    profiles = list(database.competency_profiles.find())
    repaired = 0

    for p in profiles:
        old_cid = p.get("competency_id")
        # Check if old_cid maps via LEGACY_OID_TO_CODE
        code = LEGACY_OID_TO_CODE.get(old_cid)
        if not code and old_cid:
            # Check if old_cid already matches a canonical competency
            comp = database.competencies.find_one({"_id": old_cid})
            if comp:
                code = comp.get("code")

        if code and code in comp_map:
            new_cid = comp_map[code]
            database.competency_profiles.update_one(
                {"_id": p["_id"]},
                {"$set": {"competency_id": new_cid, "updated_at": datetime.now(UTC)}},
            )
            repaired += 1

    print(f"  -> Checked {len(profiles)} profiles, repaired {repaired} competency references.")


def repair_competency_evidence(
    database: Database, comp_map: dict[str, ObjectId]
) -> None:
    """
    Step 11: Repair competency_evidence by resolving old competency IDs to canonical ones.
    """
    print("\n[11/11] Repairing Competency Evidence Records...")
    evidence = list(database.competency_evidence.find())
    repaired = 0

    for ev in evidence:
        old_cid = ev.get("competency_id")
        code = LEGACY_OID_TO_CODE.get(old_cid)
        if not code and old_cid:
            comp = database.competencies.find_one({"_id": old_cid})
            if comp:
                code = comp.get("code")
        if not code and ev.get("competency_code"):
            code = normalize_code(ev.get("competency_code"))

        if code and code in comp_map:
            new_cid = comp_map[code]
            if ev.get("competency_id") != new_cid:
                database.competency_evidence.update_one(
                    {"_id": ev["_id"]},
                    {"$set": {"competency_id": new_cid}},
                )
                repaired += 1

    print(f"  -> Checked {len(evidence)} evidence records, repaired {repaired} competency references.")


def main():
    print("=" * 70)
    print("SHIKSHASETU: MASTER DATA SYNCHRONIZATION")
    print("=" * 70)

    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    print(f"Connected to Database: {database.name}")

    base_dir = Path(__file__).resolve().parent.parent.parent
    if not (base_dir / "competency_taxonomy.csv").exists():
        base_dir = Path.cwd()

    try:
        ensure_framework_indexes(database)

        # Execute synchronization steps in strict dependency order
        comp_map = sync_competencies(database, base_dir)
        role_id = sync_roles(database)
        sync_role_requirements(database, role_id, comp_map)
        from app.scripts.seed_department_roles import sync_department_roles
        sync_department_roles(database)
        sync_assessment_configurations(database)
        sync_question_bank(database)
        res_map = sync_learning_resources(database, base_dir)
        sync_learning_resource_mappings(database, base_dir, res_map, comp_map)
        sync_users(database, role_id)
        sync_initial_assessment(database, comp_map)
        repair_competency_profiles(database, comp_map)
        repair_competency_evidence(database, comp_map)
        from app.scripts.seed_demo_course_quizzes import sync_demo_quizzes
        sync_demo_quizzes(database)

        print("\n" + "=" * 70)
        print("MASTER DATA SYNCHRONIZATION COMPLETED SUCCESSFULLY")
        print("=" * 70)

    finally:
        close_database(client)


if __name__ == "__main__":
    main()
