# ShikshaSetu — Immediate Next Steps (Action Plan)

**Current State:** Phase 1D complete. Core loop verified. Product audit done.

**Question:** What do we build next?

**Answer:** Don't build yet. First, make these decisions. Then build.

---

## DECISION 1: SIH Round 1 Submission Timeline

**Question:** When is the SIH Round 1 deadline?

**Options:**
- A) Deadline is **soon** (< 2 weeks) → Skip P1.x, focus on P0 only
- B) Deadline is **soon-ish** (2-4 weeks) → Do P0 + maybe quick P1.1 admin UI
- C) Deadline is **later** (> 4 weeks) → Do P0 + P1.1 + P1.2 (admin + analytics)
- D) No deadline, doing institutional pilot first → Do P0 + P1.1 + P1.2

**Action:** Clarify which applies. This determines scope.

---

## DECISION 2: iGOT/NSSTA Integration Availability

**Question:** Do we have or can we get iGOT/NSSTA API credentials?

**Options:**
- A) **YES** — We have credentials or will get them soon → Include in Phase 2 roadmap
- B) **NO** — No access available → Continue with seeded data (honest, not misleading)
- C) **UNKNOWN** — Need to ask stakeholders → Clarify ASAP

**Action:** Send this question to project lead/stakeholders. Document the answer.

**Impact:** This determines whether P1.4 (live integration) is feasible or should be deprioritized.

---

## DECISION 3: Pilot vs. SIH Demo-Only

**Question:** After Round 1, is the goal...

**Options:**
- A) **SIH Judge Demo Only** → Build for impression, don't worry about institutional scalability
- B) **Institutional Pilot (10-20 users)** → Need admin tools + analytics (P1.1-P1.2)
- C) **Institutional Rollout (50+ users)** → Need full Phase 2

**Action:** Clarify with stakeholders. This shapes Phase 2 priorities.

---

## IF TIMELINE IS TIGHT (< 2 weeks to SIH submission)

**Do P0 Only (3-5 days):**

```
[ ] Day 1: Add 3-4 more roles to seed script
       - Statistical Officer (already exists)
       - Senior Statistical Officer (higher requirements)
       - Data Analyst (Technical focus)
       - Manager (Leadership focus)
       - Supervisor (Mixed focus)

[ ] Day 1-2: Expand question bank (40 → 80 questions)
       - Add 5-6 more questions per competency
       - Vary difficulty (some easy, some hard)
       - Update seed_assessment.py or question_bank seed

[ ] Day 2: Verify learning resource mappings
       - Check: do 70%+ of competencies have 2+ mapped resources?
       - Add mappings if gaps exist
       - Document in seed script

[ ] Day 2-3: Data consistency audit
       - Orphan check: role_requirements → real competencies?
       - Orphan check: learning_resource_mappings → real resources?
       - Delete orphans, fix inconsistencies
       - Run seed script, verify clean state

[ ] Day 3: E2E Test + Demo Dry Run
       - Run test_e2e_closed_loop.py (must pass)
       - Demo scenario: register → assess → get gaps → get recommendations
       - Try with multiple roles (verify role-awareness works)
       - Document anything that breaks
```

**Deliverable:** Robust, multi-role seed data. Ready for SIH judge demo.

**Risk:** None. This is data/config only, no code changes.

---

## IF TIMELINE IS COMFORTABLE (2-4 weeks to SIH submission)

**Do P0 + Quick P1.1 (10-14 days):**

```
WEEK 1 — P0 (Data Quality)
[ ] Day 1: Add multiple roles + expand question bank
[ ] Day 2: Verify resource mappings + consistency audit
[ ] Day 2-3: E2E test + dry run
[ ] Day 3: Document data scope for demo

WEEK 2 — P1.1 (Admin User Management - Lightweight)
[ ] Day 4-5: Build simple admin endpoints
       GET /admin/users (list users)
       GET /admin/users/{id} (view user profile)
       Can filter by department, role, status
       
[ ] Day 5-6: Build admin UI (read-only for now)
       Admin page: User list
       Admin page: User detail (view competencies, gaps, recommendations)
       No editing yet (that's Phase 2)

[ ] Day 6-7: Integration + testing
       Wire admin endpoints to frontend
       Manual test with 10+ mock users
       E2E test still passes
```

**Deliverable:** Admin can view users and their profiles. Demonstrates institutional scalability.

**Risk:** Low. Read-only operations, no complex logic.

---

## IF TIMELINE IS RELAXED (> 4 weeks) OR DOING PILOT

**Do P0 + P1.1 + P1.2 (3-4 weeks):**

```
WEEK 1 — P0 (Data Quality)
[ ] Implement as above

WEEK 2-3 — P1.1 (Admin Dashboard)
[ ] User management endpoints + UI (as above)

WEEK 3-4 — P1.2 (Analytics - Lightweight)
[ ] Build simple analytics endpoints
       GET /analytics/competency-summary
       GET /analytics/gap-distribution
       GET /analytics/learning-adoption
       
[ ] Build analytics dashboard
       Show avg competency by role
       Show gap distribution (how many users have gap > 1.5?)
       Show learning adoption (% of users with learning activities)
       
[ ] Integration + testing
       Wire endpoints to frontend
       Verify data accuracy
       E2E test still passes
```

**Deliverable:** Admin sees institutional value (user management + trends). Ready for pilot conversations.

**Risk:** Medium. Analytics queries need optimization for large datasets.

---

## SPECIFIC IMPLEMENTATION TASKS

### Task P0.1: Add Multiple Roles

**File:** `backend/app/scripts/seed_framework.py`

**Current state:** Only 1 role (Statistical Officer with 8 competencies)

**Change:**

```python
# Add to roles list:
roles = [
    {
        "role_id": "ROLE_OFFICER",
        "role_name": "Statistical Officer",
        "role_description": "Collects, analyzes and disseminates official statistics",
        "competencies": {
            "STAT_SURVEY": 4,
            "STAT_SAMPLING": 4,
            "STAT_DATA_QUALITY": 4,
            "TECH_PYTHON": 3,
            "TECH_SQL": 3,
            "TECH_DATA_VIZ": 3,
            "GIS": 2,
            "AI_ML": 2,
        }
    },
    {
        "role_id": "ROLE_SENIOR_OFFICER",
        "role_name": "Senior Statistical Officer",
        "role_description": "Leads statistical operations and mentors junior staff",
        "competencies": {
            "STAT_SURVEY": 5,
            "STAT_SAMPLING": 5,
            "STAT_NATACC": 4,
            "TECH_PYTHON": 4,
            "TECH_R": 4,
            "LEAD_LEADERSHIP": 4,
            "LEAD_COMMUNICATION": 4,
        }
    },
    {
        "role_id": "ROLE_DATA_ANALYST",
        "role_name": "Data Analyst",
        "role_description": "Analyzes and visualizes data",
        "competencies": {
            "TECH_PYTHON": 4,
            "TECH_SQL": 4,
            "TECH_DATA_VIZ": 4,
            "STAT_DATA_QUALITY": 3,
            "AI_ML": 3,
        }
    },
    # ... more roles
]
```

**Effort:** 1-2 hours

**Verification:**
```bash
GET /api/v1/roles
# Should return 5 roles with different requirements
```

---

### Task P0.2: Expand Question Bank

**File:** `backend/app/assessments/seed.py` (or equivalent question seeding)

**Current state:** 40 questions (5 per competency)

**Change:** Add 40 more questions (target 80-100 total)

**How:**
- Keep existing questions
- Add 5-10 more questions per major competency
- Vary difficulty (some "easy", some "hard")
- Ensure all questions are grounded in competency

**Example New Questions:**

```python
# For STAT_SAMPLING (add to existing 5 questions):
{
    "competency_code": "STAT_SAMPLING",
    "question_type": "MCQ",
    "difficulty": "BEGINNER",
    "text": "What is systematic sampling?",
    "options": [
        "Selecting every nth unit from the population",
        "Randomly selecting units without replacement",
        "Dividing population into strata",
        "Selecting units based on availability"
    ],
    "correct_answer": 0,
},
# ... more questions
```

**Effort:** 2-4 hours (data entry + validation)

**Verification:**
```bash
GET /api/v1/assessments/configs/STAT_SAMPLING
# Should return 8-10 questions, not 5
```

---

### Task P0.3: Verify Learning Resource Mappings

**File:** `backend/app/scripts/seed_framework.py`

**Current state:** ~88 mappings covering ~148 resources

**Check:**
```python
# For each competency, verify at least 2 resources are mapped
competencies = ["STAT_SURVEY", "STAT_SAMPLING", "TECH_PYTHON", "TECH_SQL", ...]
for comp in competencies:
    mappings = db.learning_resource_mappings.find({"competency_code": comp})
    count = len(mappings)
    if count < 2:
        print(f"WARNING: {comp} has only {count} mapping(s)")
```

**Effort:** 1-2 hours (mostly query verification)

**Fix if needed:** Add more resource → competency mappings in seed data.

---

### Task P0.4: Data Consistency Audit

**Create File:** `backend/audit_data_consistency.py`

**Script:**

```python
from pymongo import MongoClient
from bson import ObjectId

db = MongoClient()["shikshasetu"]

def audit():
    print("🔍 Auditing data consistency...")
    
    # 1. Check role_requirements reference real competencies
    missing_comps = []
    for req in db.role_requirements.find():
        comp = db.competencies.find_one({"competency_code": req["competency_code"]})
        if not comp:
            missing_comps.append(req)
    
    if missing_comps:
        print(f"❌ {len(missing_comps)} role requirements reference missing competencies")
        for req in missing_comps:
            db.role_requirements.delete_one({"_id": req["_id"]})
            print(f"  Deleted: {req}")
    else:
        print("✅ All role requirements reference real competencies")
    
    # 2. Check learning_resource_mappings reference real resources
    missing_resources = []
    for mapping in db.learning_resource_mappings.find():
        res = db.learning_resources.find_one({"_id": mapping["resource_id"]})
        if not res:
            missing_resources.append(mapping)
    
    if missing_resources:
        print(f"❌ {len(missing_resources)} mappings reference missing resources")
        for mapping in missing_resources:
            db.learning_resource_mappings.delete_one({"_id": mapping["_id"]})
            print(f"  Deleted: {mapping}")
    else:
        print("✅ All mappings reference real resources")
    
    # 3. Check role_requirements reference real roles
    missing_roles = []
    for req in db.role_requirements.find():
        role = db.roles.find_one({"_id": ObjectId(req["role_id"])})
        if not role:
            missing_roles.append(req)
    
    if missing_roles:
        print(f"❌ {len(missing_roles)} requirements reference missing roles")
        for req in missing_roles:
            db.role_requirements.delete_one({"_id": req["_id"]})
            print(f"  Deleted: {req}")
    else:
        print("✅ All requirements reference real roles")
    
    print("\n✅ Audit complete")

if __name__ == "__main__":
    audit()
```

**Run:**
```bash
python backend/audit_data_consistency.py
```

**Effort:** 1-2 hours

---

### Task P1.1: Admin User Management Endpoint

**File:** `backend/app/admin/router.py` (new file)

**Skeleton:**

```python
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user, require_admin
from bson import ObjectId

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.get("/users")
async def list_users(
    database = Depends(get_database),
    current_user = Depends(get_current_user),
    _admin = Depends(require_admin),
    department: str = None,
    role_id: str = None,
):
    """List all users with optional filtering"""
    query = {}
    if department:
        query["department"] = department
    if role_id:
        query["role_id"] = role_id
    
    users = list(database.users.find(query))
    return {
        "count": len(users),
        "users": [
            {
                "id": str(u["_id"]),
                "email": u["email"],
                "full_name": u["full_name"],
                "designation": u["designation"],
                "department": u["department"],
                "role_id": u["role_id"],
                "status": u["status"],
            }
            for u in users
        ]
    }

@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    database = Depends(get_database),
    current_user = Depends(get_current_user),
    _admin = Depends(require_admin),
):
    """View specific user's profile + competencies"""
    user = database.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get competency profile
    profile = database.competency_profiles.find_one({"user_id": ObjectId(user_id)})
    
    # Get skill gaps
    # ... (reuse existing skill gap logic)
    
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "role_id": user["role_id"],
        "competency_profile": profile,
        "skill_gaps": gaps,
    }
```

**Then register in main.py:**

```python
from app.admin import router as admin_router
app.include_router(admin_router.router)
```

**Effort:** 4-6 hours (including tests)

---

### Task P1.2: Analytics Endpoint (Lightweight)

**File:** `backend/app/analytics/router.py` (new file)

**Skeleton:**

```python
@router.get("/analytics/competency-summary")
async def competency_summary(database = Depends(get_database)):
    """Average competency level across all users"""
    pipeline = [
        {
            "$group": {
                "_id": "$competency_code",
                "avg_level": {"$avg": "$current_level"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"avg_level": -1}}
    ]
    
    results = list(database.competency_profiles.aggregate(pipeline))
    return {"summary": results}

@router.get("/analytics/gap-distribution")
async def gap_distribution(database = Depends(get_database)):
    """How many users have gaps of each size?"""
    gaps = list(database.skill_gaps.find())
    
    distribution = {
        "no_gap": len([g for g in gaps if g["gap"] == 0]),
        "low": len([g for g in gaps if 0 < g["gap"] <= 0.5]),
        "medium": len([g for g in gaps if 0.5 < g["gap"] <= 1.0]),
        "high": len([g for g in gaps if 1.0 < g["gap"] <= 1.5]),
        "critical": len([g for g in gaps if g["gap"] > 1.5]),
    }
    
    return {"distribution": distribution}
```

**Effort:** 4-6 hours (query optimization required)

---

## Timeline Summary

| Task | Time | Blocker? |
|------|------|----------|
| P0.1: Add multiple roles | 1-2h | No |
| P0.2: Expand question bank | 2-4h | No |
| P0.3: Verify resource mappings | 1-2h | No |
| P0.4: Consistency audit | 1-2h | No |
| **P0 TOTAL** | **5-10h** | **No** |
| P1.1: Admin user mgmt | 4-6h | No |
| P1.2: Analytics | 4-6h | No |
| **P1 TOTAL** | **8-12h** | **No** |

---

## Acceptance Criteria for DONE

### P0 (Data Quality) ✅ DONE When:

```
[ ] 5+ roles seeded (not just 1)
[ ] 80+ questions in question bank
[ ] 70%+ of competencies have 2+ resource mappings
[ ] Zero orphaned records (audit script passes)
[ ] E2E test passes (core loop still works)
[ ] Multiple-role demo scenario works
```

### P1.1 (Admin UI) ✅ DONE When:

```
[ ] GET /admin/users returns list of users
[ ] Filtering by department works
[ ] Filtering by role works
[ ] GET /admin/users/{id} returns user detail
[ ] Detail shows competencies, gaps, recommendations
[ ] No 403 errors (admin auth works)
```

### P1.2 (Analytics) ✅ DONE When:

```
[ ] GET /analytics/competency-summary returns real data
[ ] Data matches direct DB queries (spot-checked)
[ ] GET /analytics/gap-distribution accurate
[ ] GET /analytics/learning-adoption accurate
[ ] Dashboard UI loads without errors
[ ] No performance issues (queries < 2s)
```

---

## Who Does What?

**Backend Dev:**
- P0.1-P0.4 (data quality, multiple roles, seeding)
- P1.1 endpoints (admin API)
- P1.2 endpoints (analytics API)

**Frontend Dev:**
- P1.1 UI (admin dashboard)
- P1.2 UI (analytics dashboard)

**QA:**
- Verify all tasks meet acceptance criteria
- Run E2E test after each task
- Document any breaking changes

---

## Risk Mitigation

**Risk:** New roles break existing tests

**Mitigation:** Run E2E test after each task. If it breaks, fix before moving on.

**Risk:** Data inconsistency breaks demo

**Mitigation:** Run consistency audit script before demo. Fix orphans.

**Risk:** Admin endpoints not secure

**Mitigation:** Verify require_admin() is enforced. Test with non-admin user (should get 403).

---

## Decision Time

**Before starting any of these tasks, confirm:**

1. ✅ **SIH Deadline:** When is it?
2. ✅ **API Access:** iGOT/NSSTA credentials available?
3. ✅ **Pilot Plan:** Doing institutional pilot after Round 1?

**Based on answers:**
- Tight deadline → Do P0 only (3-5 days)
- Comfortable deadline + no pilot → Do P0 + P1.1 (10-14 days)
- Comfortable deadline + pilot planned → Do P0 + P1.1 + P1.2 (3-4 weeks)

---

## Next Action

📋 **Schedule 30-min meeting to clarify:**
1. SIH submission deadline
2. iGOT/NSSTA API status
3. Institutional pilot timeline (yes/no)
4. Which option (tight/comfortable/relaxed) applies

Then execute tasks accordingly.

**Do not start coding until these are clarified.**
