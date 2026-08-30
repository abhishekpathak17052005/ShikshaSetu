import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "backend"))

import os
from bson import ObjectId
from pymongo import MongoClient
from app.main import app
from app.core.config import Settings
from app.skill_gaps import service as skill_gap_service
from app.learning_resources.service import RecommendationService

settings = Settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.mongodb_database]

print("=" * 80)
print("SHIKSHASETU COMPREHENSIVE BACKEND PRODUCTION READINESS AUDIT")
print(f"Target Database: {db.name}")
print("=" * 80)

# 1. API CONTRACT & ROUTER INVENTORY
print("\n--- 1. API CONTRACT & ROUTER AUDIT ---")
openapi = app.openapi()
paths = openapi.get("paths", {})
print(f"Total documented paths: {len(paths)}")
endpoints = []
for p, methods in sorted(paths.items()):
    for m, details in sorted(methods.items()):
        endpoints.append({
            "path": p,
            "method": m.upper(),
            "tag": details.get("tags", ["-"])[0],
            "summary": details.get("summary", ""),
            "operation_id": details.get("operationId", ""),
            "responses": list(details.get("responses", {}).keys())
        })
print(f"Total API operations: {len(endpoints)}")

# 2. AUTH & SECURITY AUDIT
print("\n--- 2. AUTHENTICATION & SECURITY AUDIT ---")
users = list(db.users.find())
print(f"Total users in DB: {len(users)}")
sample_user = users[0] if users else None
if sample_user:
    has_hash = sample_user.get("password_hash") is not None or sample_user.get("hashed_password") is not None
    has_email = sample_user.get("email") is not None
    has_role = sample_user.get("role_id") is not None
    has_access = sample_user.get("access_role") is not None
    print(f"User schema checks: password_hash={has_hash}, email={has_email}, role_id={has_role}, access_role={has_access}")

# 3. COMPETENCY FRAMEWORK AUDIT
print("\n--- 3. COMPETENCY FRAMEWORK AUDIT ---")
competencies = list(db.competencies.find())
print(f"Total competencies: {len(competencies)}")
domains = {}
for c in competencies:
    d = c.get("domain", "Unknown")
    domains[d] = domains.get(d, 0) + 1
for d, count in sorted(domains.items()):
    print(f"  Domain '{d}': {count} competencies")

roles = list(db.roles.find())
print(f"Active roles: {len(roles)}")
for r in roles:
    reqs = list(db.role_requirements.find({"role_id": r["_id"]}))
    print(f"  Role '{r.get('role_code')}' ({r['_id']}): {len(reqs)} requirements")

profiles = list(db.competency_profiles.find())
print(f"Total competency profiles: {len(profiles)}")
evidence_count = db.competency_evidence.count_documents({})
print(f"Total competency evidence records: {evidence_count}")

# 4. ASSESSMENT AUDIT
print("\n--- 4. ASSESSMENT AUDIT ---")
initial_assessments = list(db.assessments.find())
print(f"Initial assessment definitions: {len(initial_assessments)}")
if initial_assessments:
    ia = initial_assessments[0]
    print(f"  Assessment key: '{ia.get('assessment_key')}', Questions: {len(ia.get('questions', []))}")

configs = list(db.assessment_configurations.find())
print(f"Capability assessment configurations: {len(configs)}")
for cfg in configs:
    code = cfg.get("competency_code")
    qb_count = db.question_bank.count_documents({"competency_code": code})
    print(f"  Config '{code}': status={cfg.get('status')}, question_bank_available={qb_count}")

# 5. SKILL GAP ENGINE AUDIT
print("\n--- 5. SKILL GAP ENGINE AUDIT ---")
if users:
    test_user_id = str(users[0]["_id"])
    gap_result = skill_gap_service.calculate_skill_gaps(db, test_user_id)
    print(f"Skill gap calculation test for user {test_user_id}:")
    print(f"  Role: {gap_result.role.get('code')}, Required Competencies: {gap_result.summary.required_competencies}")
    print(f"  Gaps identified: {len(gap_result.gaps)}, Critical: {gap_result.summary.critical_gaps}, High: {gap_result.summary.high_gaps}, Med: {gap_result.summary.medium_gaps}, Low: {gap_result.summary.low_gaps}")

# 6. RECOMMENDATION ENGINE AUDIT
print("\n--- 6. RECOMMENDATION ENGINE AUDIT ---")
rec_service = RecommendationService(db)
resources = list(db.learning_resources.find())
print(f"Total learning resources in catalog: {len(resources)}")
mappings = list(db.learning_resource_mappings.find())
print(f"Total resource-to-competency mappings: {len(mappings)}")
providers = {}
for r in resources:
    p = r.get("provider", "Unknown")
    providers[p] = providers.get(p, 0) + 1
for p, cnt in sorted(providers.items()):
    print(f"  Provider '{p}': {cnt} courses")

if users:
    test_user_id = str(users[0]["_id"])
    recs = rec_service.get_recommendations_for_user(test_user_id)
    print(f"Personalized recommendation test for user {test_user_id}:")
    print(f"  Recommended items: {len(recs.recommendations)}")
    if recs.recommendations:
        top_rec = recs.recommendations[0]
        print(f"  Top course: '{top_rec.resource.title}', Score: {top_rec.score}")
        print(f"  Score Breakdown: {top_rec.explanation.score_breakdown}")

# 7. LEARNING MATERIALS & RAG AUDIT
print("\n--- 7. LEARNING MATERIALS & RAG AUDIT ---")
materials = list(db.learning_materials.find())
print(f"Total uploaded materials: {len(materials)}")
status_counts = {}
for m in materials:
    st = m.get("status", "Unknown")
    status_counts[st] = status_counts.get(st, 0) + 1
for st, cnt in sorted(status_counts.items()):
    print(f"  Status '{st}': {cnt}")

# 8. QUIZ SYSTEM AUDIT
print("\n--- 8. QUIZ SYSTEM AUDIT ---")
quizzes = list(db.quizzes.find())
print(f"Total quizzes created: {len(quizzes)}")
quiz_attempts = list(db.quiz_attempts.find())
print(f"Total quiz attempts: {len(quiz_attempts)}")

# 9. DATABASE INTEGRITY AUDIT
print("\n--- 9. DATABASE INTEGRITY AUDIT ---")
comp_ids = {c["_id"] for c in competencies}
comp_codes = {c["code"] for c in competencies}

orphaned_profiles = db.competency_profiles.count_documents({"competency_id": {"$nin": list(comp_ids)}})
orphaned_evidence = db.competency_evidence.count_documents({"competency_id": {"$nin": list(comp_ids)}})
orphaned_reqs = db.role_requirements.count_documents({"competency_id": {"$nin": list(comp_ids)}})
orphaned_qb = db.question_bank.count_documents({"competency_code": {"$nin": list(comp_codes)}})
orphaned_mappings = db.learning_resource_mappings.count_documents({"competency_code": {"$nin": list(comp_codes)}})

print(f"Orphaned competency_profiles: {orphaned_profiles}")
print(f"Orphaned competency_evidence: {orphaned_evidence}")
print(f"Orphaned role_requirements: {orphaned_reqs}")
print(f"Orphaned question_bank questions: {orphaned_qb}")
print(f"Orphaned resource mappings: {orphaned_mappings}")

print("\nAUDIT DATA EXTRACTION COMPLETE.")
