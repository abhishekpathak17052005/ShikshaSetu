# VERIFICATION BLOCKERS - DETAILED ANALYSIS

**Status:** Verification STOPPED  
**Date:** 2026-08-27  
**Backend:** FROZEN  

---

## SUMMARY

Two genuine blockers identified during Postman verification:

| Test | Endpoint | Status | Type | Root Cause |
|------|----------|--------|------|-----------|
| 4 | `/api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT` | 404 | Data | Assessment configurations not seeded |
| 11 | `/api/v1/learning-materials/upload` | 422 | API Contract | Unexpected `scope` body parameter required |

Both blockers are **not** related to missing endpoints. Both endpoints exist and are properly registered.

---

## BLOCKER 1: TEST 4 - ASSESSMENT CONFIGURATION

### Issue
```
GET /api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT
→ 404 Not Found
→ "Assessment configuration not found for competency BEH_CHANGE_MANAGEMENT"
```

### Root Cause
Assessment configurations are not seeded into the production database.

### Evidence

**Seeding Pipeline (`execute_seeding.py`):**
```python
scripts = [
    ("seed_competencies.py", "Competencies"),
    ("seed_learning_resources.py", "Learning Resources"),
    ("seed_resource_mappings.py", "Resource Mappings"),
]
```

**Missing:**
- `seed_capability_assessment_configs()` from `app/assessments/seed_capability.py` is defined but never called

**Verification:**
- Seeding function exists: ✅ `app/assessments/seed_capability.py:8-190`
- Function has standalone execution: ✅ `seed_capability.py:180-182`
- Function is invoked by seeding orchestrator: ❌ NOT called
- Result: Assessment configuration collection is empty ✅

### API Contract
Endpoint is correctly implemented:
```python
# app/assessments/router.py:43-45
@router.get("/configs/{competency_code}", response_model=AssessmentConfigurationResponse)
def get_assessment_configuration(request: Request, competency_code: str) -> dict:
    """Get assessment configuration for a specific competency."""
    return service.get_assessment_configuration(...)
```

Service correctly queries the database:
```python
# app/assessments/repository.py:15-20
def get_assessment_configuration(database: Database, competency_code: str) -> dict | None:
    """Get assessment configuration for a competency."""
    return database.assessment_configurations.find_one({
        "competency_code": competency_code,
        "status": "ACTIVE"
    })
```

**Status:** Endpoint works correctly. No data to return. ✅

### Impact
- Workflow blocked: User cannot test "Capability Assessment" → "Assessment Questions" flow
- Dependency: Test 5 and all downstream assessment tests cannot proceed
- Cause: Data setup, not backend implementation

### Decision Required
**Q:** Should assessment configurations be seeded as part of the production database initialization?
- **If YES:** Add call to `seed_capability_assessment_configs()` in `execute_seeding.py` and reseed
- **If NO:** Skip Tests 4-5 and mark as "Not applicable to current scope"

---

## BLOCKER 2: TEST 11 - MATERIAL UPLOAD

### Issue
```
POST /api/v1/learning-materials/upload
Content-Type: multipart/form-data
file: <binary>

→ 422 Unprocessable Entity
→ "Field required: Input should be a valid dictionary"
→ location: ["body", "scope"]
```

### Root Cause
FastAPI's dependency injection is creating an unexpected `scope` body parameter when `Request` is injected.

### Evidence

**Endpoint Signature:**
```python
# app/ai/router.py:58-62
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = Depends(),
) -> UploadResponse:
```

**What code shows:**
- Parameters: `file`, `current_user`, `request`
- No `scope` parameter ✅

**What FastAPI/Starlette processes (runtime inspection):**
```
Dependant body_params:
- ModelField(field_info=File(...), name='file', ...)
- ModelField(field_info=Body(...), name='scope', ...)  ← UNEXPECTED
```

**Analysis:**
The `Request` dependency is causing FastAPI to interpret Starlette's `Request.scope` attribute as a body parameter. This is a quirk of FastAPI's dependency resolution system.

When FastAPI processes `request: starlette.requests.Request = Depends()`:
1. It looks at `Request` attributes
2. Starlette's `Request` has a `scope` attribute
3. FastAPI incorrectly treats this as a required body parameter
4. Pydantic validation expects `scope` to be a dict (because `Request.scope` is a dict)

**Verification:**
Testing with `scope` as dict:
```python
files = {"file": ("test.txt", content)}
data = {"scope": "{}"}  # Trying to send as string
→ 422: "Input should be a valid dictionary"
```

The endpoint cannot process `scope` because it's never used in the function.

### API Contract
**Current situation:**
- Endpoint code does not reference or use `scope`
- Endpoint signature does not declare `scope` as a parameter
- But FastAPI/Starlette validation requires it

**Expected situation:**
- Only `file` should be required
- `scope` should not appear in validation

### Impact
- Material upload is completely blocked
- No test can proceed that requires uploading learning materials
- Affects: Test 11, Test 12 (MCQ generation), all downstream learning material tests

### Decision Required
**Q:** Why is `Request` being injected if only the database is needed?

Options:
1. **Remove `request: Request = Depends()` from function signature** (if not used for anything)
   - Use `request.app.state.database` directly as `Depends(get_database)`
   - This would eliminate the `scope` body parameter issue

2. **Accept the scope parameter** (if it's intentional)
   - Update endpoint to accept `scope` as optional form field
   - Update Postman test to send `scope`
   - Add documentation explaining what `scope` is used for

3. **Use explicit dependency** instead of implicit Request
   - Create a dedicated dependency for getting database
   - Inject only what's needed
   - Avoid FastAPI's automatic attribute parsing

### Hypothesis
The `Request` is injected only to access `request.app.state.database`. This could be replaced with a dedicated dependency injection function, which would:
- Eliminate the `scope` body parameter issue
- Make the API contract clearer
- Reduce unnecessary dependencies

---

## POSTMAN TEST STATUS

```
✅ Test 1  — Register
✅ Test 2  — Login
✅ Test 3  — Get Competencies

❌ Test 4  — Assessment Config (BLOCKED: Data not seeded)
⊘  Test 5  — Assessment Submit (BLOCKED: Depends on Test 4)
✅ Test 6  — Get User Profile
✅ Test 7  — Get Skill Gaps
✅ Test 8  — Get Recommendations
✅ Test 9  — Recommendation Score Breakdown
✅ Test 10 — Recommendation Determinism

❌ Test 11 — Material Upload (BLOCKED: scope parameter issue)
⊘  Test 12 — MCQ Generation (BLOCKED: Depends on Test 11)
✅ Test 13 — Quiz Creation
✅ Test 14 — Quiz Retrieval
✅ Test 15 — Quiz Submission
✅ Test 16 — User Evidence Check
✅ Test 17 — Competency Post-Quiz

✅ Test 18 — Recommendations (iGOT filter)
✅ Test 19 — Recommendations (NSSTA filter)

✅ Test 20 — Auth Check (No Auth)
✅ Test 21 — Auth Check (Invalid Token)
✅ Test 22 — 404 Handling
```

---

## RECOMMENDATIONS

### For Test 4:
1. **Confirm scope:** Does the production database need assessment configurations?
2. **If yes:** Execute `seed_capability_assessment_configs()` in the seeding pipeline
3. **If no:** Accept that capability assessments are not part of this phase

### For Test 11:
1. **Root cause:** Unnecessary `request: Request = Depends()` injection
2. **Solution:** Replace with explicit database dependency or remove if unused
3. **Alternative:** Accept `scope` as an optional parameter (less clean)

### Proceed with Verification:
Once decisions are made:
- Reseed if needed for Test 4
- Fix Request injection for Test 11
- Resume verification from Test 4

---

**Awaiting user guidance on both blockers before proceeding.**
