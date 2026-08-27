#!/usr/bin/env python
"""Manual verification of Phase 5 skill gap engine."""

from datetime import UTC, datetime
import uuid

from app.auth.security import hash_password
from app.core.config import get_settings
from app.core.database import initialize_database
from app.scripts.seed_framework import seed_framework
from app.skill_gaps import service
from bson import ObjectId


def main():
    """Run manual verification."""
    settings = get_settings()
    client, db = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    
    print("=" * 80)
    print("PHASE 5 MANUAL VERIFICATION — SKILL GAP ENGINE")
    print("=" * 80)
    
    # STEP 1: Seed framework
    print("\n[STEP 1] Seeding competency framework...")
    result = seed_framework(db)
    print(f"  ✓ Seeded: {result}")
    
    # STEP 2: Create test user with role
    print("\n[STEP 2] Creating test user with Statistical Officer role...")
    now = datetime.now(UTC)
    
    role_doc = db.roles.find_one({"role_code": "STATISTICAL_OFFICER"})
    if not role_doc:
        raise ValueError("Statistical Officer role not found after seed")
    role_id = role_doc["_id"]
    
    unique_id = str(uuid.uuid4())[:8]
    user_doc = {
        "_id": ObjectId(),
        "email": f"test-{unique_id}@shikshasetu.local",
        "password_hash": hash_password("Test@1234"),
        "full_name": "Test Employee",
        "role_id": role_id,
        "designation": "Statistical Officer",
        "department": "Statistics",
        "employee_id": f"EMP-TEST-{unique_id}",
        "status": "active",
        "access_role": "EMPLOYEE",
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
    db.users.insert_one(user_doc)
    user_id = str(user_doc["_id"])
    print(f"  ✓ Created user: {user_id}")
    print(f"    Email: {user_doc['email']}")
    print(f"    Role: Statistical Officer")
    
    # STEP 3: Create partial competency assessments
    print("\n[STEP 3] Creating sample competency profiles...")
    
    competencies_to_assess = [
        ("STAT_SAMPLING", 2.63, 0.80),
        ("STAT_SURVEY_DESIGN", 3.50, 0.90),
        ("TECH_SQL", 2.10, 0.70),
        ("TECH_PYTHON", None, 0.0),  # Not assessed
    ]
    
    for comp_code, level, confidence in competencies_to_assess:
        comp = db.competencies.find_one({"code": comp_code})
        if not comp:
            print(f"  ✗ Competency {comp_code} not found")
            continue
        
        if level is not None:
            db.competency_profiles.insert_one(
                {
                    "user_id": ObjectId(user_id),
                    "competency_id": comp["_id"],
                    "current_level": level,
                    "confidence": confidence,
                    "last_assessed_at": now,
                    "status": "active",
                    "created_at": now,
                    "updated_at": now,
                }
            )
            print(f"  ✓ {comp_code}: Level {level}, Confidence {confidence}")
        else:
            print(f"  ○ {comp_code}: Not assessed")
    
    # STEP 4: Calculate skill gaps
    print("\n[STEP 4] Calculating skill gaps...")
    try:
        response = service.calculate_skill_gaps(db, user_id)
        print(f"  ✓ Skill gaps calculated successfully")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # STEP 5: Verify results
    print("\n[STEP 5] Verifying skill gap results...")
    print(f"\n  Role: {response.role['code']} ({response.role['name']})")
    print(f"  Summary:")
    print(f"    - Required competencies: {response.summary.required_competencies}")
    print(f"    - Total gaps: {response.summary.total_gaps}")
    print(f"    - No gaps: {response.summary.no_gap_count}")
    print(f"    - Not assessed: {response.summary.not_assessed_count}")
    print(f"    - Critical gaps: {response.summary.critical_gaps}")
    print(f"    - High gaps: {response.summary.high_gaps}")
    print(f"    - Medium gaps: {response.summary.medium_gaps}")
    print(f"    - Low gaps: {response.summary.low_gaps}")
    
    print(f"\n  Gaps (sorted by priority, top 5):")
    for i, gap in enumerate(response.gaps[:5], 1):
        status_icon = "✓" if gap.gap_category == "NO_GAP" else "●"
        assess_status = " [NOT ASSESSED]" if gap.assessment_status == "NOT_ASSESSED" else ""
        print(f"\n    {i}. {status_icon} {gap.competency_code} ({gap.competency_name})")
        print(f"       Required: {gap.required_level:.1f} | Current: {gap.current_level}{assess_status}")
        print(f"       Gap: {gap.gap:.2f} ({gap.gap_category}) | Priority Score: {gap.priority_score:.2f}")
    
    # STEP 6: Validate correctness
    print("\n[STEP 6] Validating correctness...")
    
    checks = [
        ("Role resolved correctly", response.role["code"] == "STATISTICAL_OFFICER"),
        ("Required competencies = 8", response.summary.required_competencies == 8),
        ("Assessment status distinction", 
         any(g.assessment_status == "NOT_ASSESSED" for g in response.gaps)),
        ("Gap calculation (Sampling)", 
         any(g.competency_code == "STAT_SAMPLING" and g.gap == 1.37 for g in response.gaps)),
        ("Gap category mapping (HIGH)", 
         any(g.competency_code == "STAT_SAMPLING" and g.gap_category == "HIGH" for g in response.gaps)),
        ("Priority ranking (deterministic)", 
         len(response.gaps) > 1 and response.gaps[0].priority_score >= response.gaps[-1].priority_score),
        ("No negative gaps", all(g.gap >= 0 for g in response.gaps)),
        ("Confidence in range", all(0 <= g.confidence <= 1 for g in response.gaps)),
    ]
    
    passed = 0
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n  Passed: {passed}/{len(checks)}")
    
    # STEP 7: Summary
    print("\n" + "=" * 80)
    if passed == len(checks):
        print("✓ PHASE 5 VERIFICATION PASSED")
    else:
        print("✗ PHASE 5 VERIFICATION FAILED")
    print("=" * 80)


if __name__ == "__main__":
    main()
