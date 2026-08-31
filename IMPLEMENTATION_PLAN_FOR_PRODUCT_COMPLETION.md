# ShikshaSetu Product Completion — Implementation Plan

**Date**: August 27, 2026  
**Status**: PHASE 0 — Planning (No code changes yet)  
**Goal**: Transform ShikshaSetu from MVP to convincing end-to-end competency development platform  
**Deadline**: SIH demo-ready (14–20 hours implementation across Phases 1–2)

---

## CONFIRMED GAPS (Audit Verified)

✅ **Gap 1: NO LEARNING ACTIVITY SYSTEM**
- Current state: Backend generates recommendations, but no interface to start/complete learning
- Impact: User sees course list but cannot track learning progress
- Priority: P0 (blocks all downstream features)

✅ **Gap 2: NO REAL PROGRESS TRACKING**
- Current state: Dashboard shows mock metrics (+8.4%, 12/18 completed)
- Impact: User can't see actual learning history or competency growth
- Priority: P0 (demo blocker)

✅ **Gap 3: BROKEN CLOSED LOOP**
- Current state: Assessment → Gap → Recommendations → (end)
- Impact: No "learning → evidence → competency update → new recommendations" cycle
- Priority: P0 (core missing feature)

✅ **Gap 4: NO LEARNING PATH SEQUENCING**
- Current state: 5-factor recommendation formula ranks courses
- Impact: Recommendations aren't sequenced; all resources shown equally
- Priority: P1 (SIH important; MVP complete without it)

✅ **Gap 5: FRONTEND NOT CALLING BACKEND APIS**
- Current state: Home.tsx has ~2000 lines of mock data
- Impact: All metrics are simulated; real learning can't be recorded
- Priority: P0 (prevents Phase 1 from working end-to-end)

---

## PROPOSED SOLUTION ARCHITECTURE

### PHASE 1: Learning Activity System + API Integration

**Objective**: Enable users to start, progress, and complete learning resources with real backend state

**New Backend Components**:
1. `learning_activity` collection (new)
2. `app/learning_activities/` module (new)
   - `repository.py` — CRUD for learning activities
   - `service.py` — Business logic (start, update, complete)
   - `router.py` — API endpoints
   - `schemas.py` — Pydantic models
   - `models.py` — Enums for activity status

3. `app/learning_resources/` updates
   - Add learning activity awareness to recommendation service
   - Filter completed/in-progress from top recommendations

**New APIs** (6 endpoints):
- `POST /api/v1/learning-activities` — Start activity
- `GET /api/v1/learning-activities` — List user's activities
- `GET /api/v1/learning-activities/{activity_id}` — Get activity details
- `PUT /api/v1/learning-activities/{activity_id}` — Update progress
- `POST /api/v1/learning-activities/{activity_id}/complete` — Mark complete
- `GET /api/v1/learning-activities/resource/{resource_id}` — Get activity for resource

**Frontend Changes**:
- Replace mock data in Home.tsx with API calls
- Create `src/services/api.ts` with axios configuration
- Update `src/pages/Learning.tsx` to show real activity state
- Update buttons: "Start Learning", "Continue Learning", "Complete"
- Add progress display on dashboard (real data, not mock)

**Database Changes**:
```
learning_activity {
  _id: ObjectId,
  user_id: ObjectId,
  resource_id: str,
  competency_id: str,
  status: "not_started" | "in_progress" | "completed",
  started_at: datetime,
  completed_at: datetime,
  progress_percent: float (0–100),
  duration_minutes: float,
  last_accessed_at: datetime,
  notes: str (optional)
}

Indexes:
- (user_id, status)
- (user_id, completed_at)
- (resource_id)
```

---

### PHASE 2: Close Learning → Evidence → Competency Loop

**Objective**: When user completes learning, generate evidence and update competency

**New Backend Components**:
1. `app/learning_activities/evidence_engine.py`
   - When activity completed → create evidence record
   - Evidence type: "LEARNING_ACTIVITY"
   - Score: deterministic (e.g., 50% base from completion + progress)

2. Modify `app/capability_assessments/service.py`
   - Handle evidence from learning activities
   - Recalculate competency profile
   - Recalculate skill gaps

**Flow**:
```
User Completes Learning Activity
  ↓
Create LEARNING_ACTIVITY evidence record
  ↓
Call existing competency profile update logic
  ↓
Competency level increases (if enough evidence)
  ↓
Skill gap recalculated (automatic)
  ↓
Return updated gap to frontend
```

**Frontend Changes**:
- On "Complete", show:
  - Score earned
  - Evidence recorded
  - Competency updated (before → after)
  - Gap reduced
- Add "View Updated Gap" button
- Trigger recommendations refresh

**Evidence Rules** (Deterministic):
```
LEARNING_ACTIVITY evidence generates:
  - Base confidence: 0.4 (lower than assessment)
  - Score contribution: completion % × 0.5
  - Full completion: +0.5 toward competency level
  
Example:
  - User completes Python learning activity (100%)
  - Evidence score: 75 out of 100
  - Competency impact: +0.35 toward level (lower than assessment)
  - Reasoning: Learning completion is supporting evidence, not definitive assessment
```

---

### PHASE 3: Learning Path Sequencing

**Objective**: Recommendations should suggest "next" learning in sequence

**Backend Changes**:
1. Add `learning_path_service.py`
   - Input: user's competency profile, gaps, learning history
   - Output: ordered list of resources with reasoning

2. Modify `get_recommendations_for_user`
   - Include learning history awareness
   - Mark completed/in-progress resources
   - Order by: prerequisites → difficulty → gap severity

**Algorithm** (Deterministic):
```
For each high-priority gap:
  1. Find all resources mapped to competency
  2. Filter to resources not yet completed
  3. Sort by difficulty (beginner first)
  4. Check prerequisites (must have completed)
  5. Rank by 5-factor formula (existing logic)
  6. Return top 5 with ordering
```

---

### PHASE 4: Progress Visualization

**Objective**: Show before → after competency improvement

**Frontend Changes**:
1. `src/pages/Progress.tsx`
   - Query real learning history
   - Show competency progression timeline
   - Before/after comparisons
   - Gap reduction visualization

2. `src/pages/Dashboard.tsx`
   - Replace mock metrics with real data
   - Show actual resources completed
   - Show current learning
   - Show improvement trend

**Backend Endpoints** (Already exist, just call them):
- `GET /api/v1/skill-gaps/me` — Current gaps
- `GET /api/v1/recommendations/me` — Current recommendations
- `GET /api/v1/users/me` — User profile
- Plus new learning activity endpoints

---

## FILES AFFECTED

### New Files

**Backend**:
- `backend/app/learning_activities/__init__.py`
- `backend/app/learning_activities/models.py`
- `backend/app/learning_activities/schemas.py`
- `backend/app/learning_activities/repository.py`
- `backend/app/learning_activities/service.py`
- `backend/app/learning_activities/router.py`
- `backend/app/learning_activities/evidence_engine.py`

**Frontend**:
- `frontend/client/src/services/api.ts` (new axios client)
- `frontend/client/src/hooks/useLearningActivity.ts` (optional)

**Tests**:
- `backend/tests/test_learning_activities.py`
- `backend/tests/test_learning_activity_evidence.py`
- `backend/tests/test_e2e_closed_loop.py` (most important)

### Modified Files

**Backend**:
- `backend/app/main.py` (register new router)
- `backend/app/core/database.py` (ensure indexes)
- `backend/app/learning_resources/service.py` (add activity awareness)
- `backend/app/skill_gaps/engine.py` (no change — reuse existing)
- `backend/app/capability_assessments/service.py` (handle learning evidence)

**Frontend**:
- `frontend/client/src/pages/Home.tsx` (replace mock data)
- `frontend/client/src/pages/Learning.tsx` (real activity tracking)
- `frontend/client/src/pages/Dashboard.tsx` (real metrics)
- `frontend/client/src/pages/Progress.tsx` (real history)
- `frontend/client/src/pages/Recommendations.tsx` (activity awareness)
- `frontend/client/package.json` (axios already imported)

---

## DATABASE COLLECTIONS AFFECTED

### New
- `learning_activity` (new collection)

### Modified
- `competency_profiles` — Already updated after evidence (no schema change)
- `competency_evidence` — New evidence type added (no schema change, new enum value)

### Unchanged
- `competencies`, `roles`, `users`, `learning_resources`, `assessments`, etc.

---

## EXISTING APIS THAT CAN BE REUSED

✅ **Don't rebuild these**:
- `GET /api/v1/competencies` — Competency taxonomy
- `GET /api/v1/roles/{role_id}/requirements` — Role requirements
- `GET /api/v1/skill-gaps/me` — Skill gap calculation (call after learning complete)
- `GET /api/v1/recommendations/me` — Recommendations (already accounts for evidence)
- `GET /api/v1/users/me` — User profile
- Existing evidence recording in `app/capability_assessments/service.py`

✅ **Reuse these services**:
- `SkillGapService.calculate_skill_gaps()` — Call after competency update
- `RecommendationService.get_recommendations_for_user()` — Call after gap recalculation
- Evidence creation pattern from assessments

---

## NEW APIS REQUIRED

### Learning Activity Management

```python
POST /api/v1/learning-activities
{
  "resource_id": "IGOT-12345",
  "competency_id": "TECH-PYTHON"
}
Response:
{
  "activity_id": "ObjectId",
  "user_id": "ObjectId",
  "resource_id": "IGOT-12345",
  "status": "in_progress",
  "started_at": "2026-08-27T10:00:00Z",
  "progress_percent": 0
}

PUT /api/v1/learning-activities/{activity_id}
{
  "progress_percent": 45,
  "duration_minutes": 30
}
Response: Updated activity

POST /api/v1/learning-activities/{activity_id}/complete
{
  "final_score": 85 (optional)
}
Response:
{
  "activity": {...},
  "evidence_created": true,
  "evidence_id": "ObjectId",
  "competency_updated": {
    "before": 2.5,
    "after": 2.8,
    "change": 0.3
  },
  "gap_recalculated": {
    "before": 1.5,
    "after": 1.2,
    "change": -0.3
  }
}

GET /api/v1/learning-activities
Query params: ?status=in_progress&limit=10
Response: List of user's activities

GET /api/v1/learning-activities/{activity_id}
Response: Activity details + current competency state
```

---

## SECURITY CONSIDERATIONS

✅ **All new endpoints must**:
- Require authentication: `@requires_auth`
- Validate user ownership: User can only access their own activities
- Check resource existence before creating activity
- Prevent cross-user access via user_id validation

✅ **Evidence creation**:
- Only backend can create LEARNING_ACTIVITY evidence
- Evidence is append-only (not deletable)
- Competency updates deterministic (same inputs = same result)

✅ **No privilege escalation**:
- Employee cannot create evidence of assessment completion
- Only completed quizzes/assessments create assessment-level evidence
- Learning activity evidence weighted lower (0.4 confidence vs 0.8 for assessments)

---

## TESTING STRATEGY

### Unit Tests (Existing Must Pass)

✅ All 189 existing tests must continue passing
- No changes to existing business logic
- Only additions

### New Tests Required

**Phase 1 Tests**:
1. `test_create_learning_activity` — Can start learning
2. `test_update_learning_activity` — Can update progress
3. `test_complete_learning_activity` — Can mark complete
4. `test_cross_user_access_rejected` — User A cannot access User B's activity
5. `test_learning_activity_repository` — CRUD operations

**Phase 2 Tests**:
6. `test_learning_activity_generates_evidence` — Evidence created on completion
7. `test_competency_updated_from_learning` — Competency increases after learning
8. `test_skill_gap_recalculated` — Gap recalculated after competency update
9. `test_confidence_calculation` — Learning evidence gets lower confidence

**Critical End-to-End Test**:
10. `test_e2e_closed_loop` (MANDATORY)
```python
# Pseudo-code
def test_e2e_closed_loop():
    # 1. Register user
    user = register_user("Ananya", "Statistical Officer")
    
    # 2. Initial assessment
    assessment_score = take_assessment(user, questions=[...])
    initial_python_level = get_competency(user, "TECH-PYTHON")  # e.g., 2.5
    initial_gap = get_skill_gap(user, "TECH-PYTHON")  # e.g., 1.5
    
    # 3. Get recommendations
    recs = get_recommendations(user)
    python_course = find_recommendation_for_competency(recs, "TECH-PYTHON")
    
    # 4. START learning
    activity = start_learning_activity(user, python_course["resource_id"], "TECH-PYTHON")
    assert activity["status"] == "in_progress"
    
    # 5. PROGRESS learning
    update_activity(activity, progress_percent=50, duration_minutes=60)
    activity = get_activity(activity)
    assert activity["progress_percent"] == 50
    
    # 6. COMPLETE learning
    result = complete_learning_activity(activity)
    assert result["evidence_created"] == true
    assert result["competency_updated"]["after"] > initial_python_level
    
    # 7. VERIFY gap reduced
    new_gap = get_skill_gap(user, "TECH-PYTHON")
    assert new_gap < initial_gap
    
    # 8. VERIFY recommendations updated
    new_recs = get_recommendations(user)
    # Python course should no longer be top recommendation (or marked completed)
    assert python_course not in top_3_recommendations(new_recs)
    
    # 9. REASSESS
    reassessment_score = take_assessment(user, questions=[...])
    assert reassessment_score > assessment_score
    
    # Database state verified
    assert user_activities_count(user) == 1
    assert evidence_count_for_user(user) > 2  # Initial assessment + learning evidence
```

---

## RISK ANALYSIS

### Risk 1: Regression in Existing Tests
**Severity**: HIGH  
**Mitigation**: 
- Run full test suite after each phase
- Do not modify existing business logic
- Only add new code

### Risk 2: Frontend Mock Data Not Replaced
**Severity**: HIGH  
**Mitigation**:
- Create `src/services/api.ts` immediately
- Replace one endpoint at a time
- Verify with dev tools that API calls are made

### Risk 3: Learning Evidence Breaks Competency Calculation
**Severity**: MEDIUM  
**Mitigation**:
- Use same evidence pattern as existing code
- Test evidence weighting thoroughly
- Evidence is supporting, not definitive

### Risk 4: Circular Dependency in Skill Gap Recalculation
**Severity**: LOW  
**Mitigation**:
- Call existing `calculate_skill_gaps()` (pure function)
- No state mutation

---

## IMPLEMENTATION ORDER

### PHASE 1: Learning Activity Backend (4–5 hours)

**Step 1.1**: Create `app/learning_activities/` module structure  
**Step 1.2**: Implement repository layer (CRUD)  
**Step 1.3**: Implement service layer (business logic)  
**Step 1.4**: Implement router (API endpoints)  
**Step 1.5**: Register router in `app/main.py`  
**Step 1.6**: Run tests (verify no regressions)  

**Stop Condition**: All new endpoints working, no test failures

---

### PHASE 1B: Frontend API Integration (3–4 hours)

**Step 1B.1**: Create `src/services/api.ts` with axios client  
**Step 1B.2**: Replace mock data in `Home.tsx` with API calls  
**Step 1B.3**: Update `Dashboard.tsx` to call real endpoints  
**Step 1B.4**: Update `Learning.tsx` with activity start/update  
**Step 1B.5**: Add error handling and loading states  

**Stop Condition**: Frontend calls real backend, displays real data

---

### PHASE 2: Evidence & Loop Closure (4–5 hours)

**Step 2.1**: Implement `learning_activities/evidence_engine.py`  
**Step 2.2**: Modify `/complete` endpoint to create evidence  
**Step 2.3**: Call competency update logic  
**Step 2.4**: Call skill gap recalculation  
**Step 2.5**: Return updated state to frontend  
**Step 2.6**: Update frontend to show before/after  
**Step 2.7**: Run full E2E test  

**Stop Condition**: Complete learning → evidence → competency → gap update cycle works

---

### PHASE 3: Sequencing & Path Intelligence (3–4 hours)

**Step 3.1**: Implement learning path sequencing  
**Step 3.2**: Update recommendation endpoint to mark completed/in-progress  
**Step 3.3**: Verify path ordering correct  
**Step 3.4**: Update frontend to show path sequence  

**Stop Condition**: Recommendations show learning path, not random list

---

### PHASE 4: Progress Visualization (2–3 hours)

**Step 4.1**: Update `Progress.tsx` with real data  
**Step 4.2**: Add before/after comparison UI  
**Step 4.3**: Show learning history timeline  
**Step 4.4**: Polish dashboard metrics  

**Stop Condition**: Dashboard shows real metrics for demo

---

## STOP CONDITIONS (After Each Phase)

After Phase 1:
- ✅ All 189 existing tests still pass
- ✅ 6 new learning activity tests pass
- ✅ No regressions in existing APIs

After Phase 1B:
- ✅ Frontend makes real API calls (verify in Network tab)
- ✅ No errors in console
- ✅ All pages display real data

After Phase 2:
- ✅ E2E closed-loop test passes
- ✅ Learning → Evidence → Competency → Gap update works
- ✅ Skill gap actually shrinks after learning

After Phase 3:
- ✅ Learning paths show in recommendations
- ✅ Completed courses removed from recommendations
- ✅ Sequencing correct

After Phase 4:
- ✅ Dashboard shows real progress (not mock +8.4%)
- ✅ Demo story demonstrable end-to-end
- ✅ All pages use real data

---

## SUCCESS CRITERIA (SIH Demo)

### Must Work
1. ✅ User can see role requirements
2. ✅ User can take initial assessment
3. ✅ System calculates current capability
4. ✅ System identifies skill gaps
5. ✅ System recommends learning resources
6. ✅ **User can start a learning resource**
7. ✅ **User can track learning progress**
8. ✅ **User can complete learning**
9. ✅ **Evidence is recorded in backend**
10. ✅ **Competency level increases**
11. ✅ **Skill gap shrinks**
12. ✅ **New recommendations generated**
13. ✅ User can reassess
14. ✅ Improvement visible (before → after)
15. ✅ All real data (no mock metrics)

### Must NOT Happen
- ❌ Any fake data in production paths
- ❌ Any broken existing tests
- ❌ Any cross-user access
- ❌ Any unhandled errors
- ❌ Any security gaps

---

## EFFORT ESTIMATE

| Phase | Task | Hours | Risk |
|-------|------|-------|------|
| 1 | Backend learning activities | 4–5h | LOW |
| 1B | Frontend API integration | 3–4h | MEDIUM |
| 2 | Evidence & loop closure | 4–5h | MEDIUM |
| 3 | Path sequencing | 3–4h | LOW |
| 4 | Progress visualization | 2–3h | LOW |
| **Total** | **All Phases** | **16–21h** | **MEDIUM** |

**SIH Demo Minimum** (Phases 1–2): 11–14 hours

---

## FINAL NOTE

This plan prioritizes the **closed learning loop** as the critical missing piece. Once learning activities work end-to-end (start → progress → complete → evidence → competency update → gap reduction), the product feels complete from a user's perspective.

Phases 3–4 are polish and can be deferred if time is short, but Phases 1–2 are non-negotiable for demo.

**Next Step**: BEGIN PHASE 1 implementation. No code changes until this plan is approved.

