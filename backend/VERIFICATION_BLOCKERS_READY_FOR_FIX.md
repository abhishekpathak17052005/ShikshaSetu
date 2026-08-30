# VERIFICATION BLOCKERS - READY FOR FIX

**Status:** Diagnosis Complete | Awaiting Authorization  
**Backend:** FROZEN (no changes without explicit approval)  
**Current Test Status:** 3 PASS, 2 BLOCKED, 17 PENDING

---

## BLOCKER 1: TEST 4 - ASSESSMENT CONFIGURATION DATA

### Current State
```
GET /api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT
→ 404 Not Found
→ "Assessment configuration not found for competency BEH_CHANGE_MANAGEMENT"
```

### Root Cause (Confirmed)
Assessment configuration data is not seeded into production database.

### Evidence
- **Endpoint exists:** ✅ `app/assessments/router.py:43-45`
- **Service works:** ✅ `app/assessments/service.py:172-180`
- **Database query:** ✅ `app/assessments/repository.py:15-20`
- **Seeding function exists:** ✅ `app/assessments/seed_capability.py:8-190`
- **Seeding is called:** ❌ NOT in `execute_seeding.py`
- **Assessment config collection:** 0 documents

### Minimal Fix
**File:** `backend/execute_seeding.py:38-42`

**Current:**
```python
scripts = [
    ("seed_competencies.py", "Competencies"),
    ("seed_learning_resources.py", "Learning Resources"),
    ("seed_resource_mappings.py", "Resource Mappings"),
]
```

**Change to:**
```python
scripts = [
    ("seed_competencies.py", "Competencies"),
    ("seed_learning_resources.py", "Learning Resources"),
    ("seed_resource_mappings.py", "Resource Mappings"),
    ("seed_capability_assessment_configs", "Assessment Configurations"),  # ADD THIS
]
```

Wait—the script name needs verification. Let me check if it's invokable as a module.

### Verification Needed
- Can `seed_capability_assessment_configs` be invoked via `subprocess` like the others?
- Or does it need a different pattern?

### Impact if Fixed
- ✅ Test 4 will pass (endpoint returns 200 with config data)
- ✅ Test 5 can proceed (assessment submission)
- ✅ Unblocks workflow 1 downstream

---

## BLOCKER 2: TEST 11 - REQUEST DEPENDENCY SCOPE PARAMETER

### Current State
```
POST /api/v1/learning-materials/upload
Content-Type: multipart/form-data
file: <binary>

→ 422 Unprocessable Entity
→ "Field required: scope"
→ location: ["body", "scope"]
```

### Root Cause (Confirmed at Dependency Graph Level)

**Endpoint declaration:**
```python
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = Depends(),  ← PROBLEM LINE
) -> UploadResponse:
```

**FastAPI's dependency graph analysis:**
```
Route: /learning-materials/upload
├─ Route body_params: ['file']  ✅
└─ Dependencies:
   ├─ current_user (get_current_user): (no body_params)  ✅
   └─ request (Request): body_params = ['scope']  ❌ UNWANTED
       └─ From: Request.scope attribute
           └─ Type: MutableMapping[str, Any]
               └─ FastAPI treats as: required body parameter
```

### Why This Happens
When FastAPI processes `request: Request = Depends()`:
1. It sees a dependency on `Request`
2. It introspects the `Request` class
3. It finds `scope` is a public attribute of `Request`
4. It treats `scope` as a required body parameter
5. Pydantic validation fails if `scope` is not provided as a dict

### Minimal Fix

**File:** `backend/app/ai/router.py:57-63`

**Current:**
```python
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = Depends(),
) -> UploadResponse:
    database = request.app.state.database
```

**Option A (Cleanest - remove unnecessary dependency):**
```python
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(lambda request: request.app.state.database),
) -> UploadResponse:
    database = db  # Use directly, no request object needed
```

**Option B (Minimal - remove = Depends()):**
```python
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request,  # Remove = Depends() to prevent introspection
) -> UploadResponse:
    database = request.app.state.database
```

**Option C (Most explicit):**
```python
# Add this import at top
from typing import Annotated

# Then use:
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Annotated[Request, Depends()],
) -> UploadResponse:
    database = request.app.state.database
```

### Recommended Fix
**Option B is minimal and least invasive:**
- Single line change
- Preserves all functionality
- Normal FastAPI pattern (most routes use `request: Request` without `Depends()`)
- Removes the introspection trigger

### Impact if Fixed
- ✅ Test 11 will pass (endpoint accepts multipart/form-data with just file)
- ✅ Test 12 can proceed (MCQ generation)
- ✅ Unblocks workflow 2 downstream

---

## EXECUTION PLAN (AWAITING AUTHORIZATION)

### Step 1: Fix Assessment Seeding
1. Modify `execute_seeding.py` to include assessment configuration seeder
2. Run `execute_seeding.py` to seed assessment configs
3. Verify: `GET /api/v1/assessments/configs` returns non-empty list
4. Run Test 4 → Should pass ✅

### Step 2: Fix Upload Dependency
1. Modify `app/ai/router.py:60` from `request: Request = Depends()` to `request: Request`
2. Verify no other code change needed (only usage is `request.app.state.database`)
3. Restart FastAPI server (if needed)
4. Run Test 11 → Should pass ✅

### Step 3: Resume Verification
1. Run Tests 1-22 from start
2. Collect results
3. Report any NEW failures

### Step 4: Final Status
- ✅ All 22 tests pass or
- ❌ New failure identified (stopped per protocol)

---

## CHANGES REQUIRED

### Fix A: Assessment Seeding (1 file, minimal change)
**File:** `backend/execute_seeding.py`  
**Lines:** 38-42 (add 1 item to list)  
**Risk:** Low (just adds existing seeder to orchestrator)  
**Reversible:** Yes (remove from list to revert)

### Fix B: Upload Dependency (1 file, 1-line change)
**File:** `backend/app/ai/router.py`  
**Line:** 60  
**Change:** `request: Request = Depends()` → `request: Request`  
**Risk:** Very low (standard FastAPI pattern)  
**Reversible:** Yes (one line change)

### No Other Changes
- ✅ No recommendation logic changes
- ✅ No API contract changes
- ✅ No database schema changes
- ✅ No test file modifications

---

## VERIFICATION

After fixes are applied, verify with:

```bash
# Test 4
curl -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8001/api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT

# Expected: 200 OK (config data)

# Test 11
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.pdf" \
  http://127.0.0.1:8001/api/v1/learning-materials/upload

# Expected: 200 OK (upload response with material_id)
```

---

## AUTHORIZATION REQUIRED

✋ **STOP - Awaiting User Authorization**

Please confirm:

1. **Assessment Seeding:** Should I add assessment configuration seeding to the orchestrator?
   - [ ] YES - Add to execute_seeding.py and reseed
   - [ ] NO - Skip Tests 4-5

2. **Upload Dependency:** Should I fix the Request dependency?
   - [ ] YES - Change `request: Request = Depends()` to `request: Request`
   - [ ] NO - Accept the scope parameter issue (not recommended)

Once authorized, I will apply ONLY these minimal fixes and resume verification.

---

**Evidence-backed root causes. Minimal fixes defined. Ready for authorization.**
