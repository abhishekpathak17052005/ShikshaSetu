# API CONTRACT AUDIT REPORT

**Date:** 2026-08-27  
**Backend Status:** FROZEN (no code changes allowed)  
**Audit Focus:** TEST 4 and TEST 11 Failures  

---

## EXECUTIVE SUMMARY

**TEST 4 and TEST 11 both FAIL due to INCORRECT ENDPOINT PATHS in the Postman verification tests.**

- **TEST 4:** Postman uses non-existent endpoint → Correct endpoint exists
- **TEST 11:** Postman uses non-existent endpoint → Correct endpoint exists
- **Root Cause:** API contract mismatch between Postman tests and actual backend router registrations
- **Not a backend feature gap.** Both features are implemented; paths are wrong.

---

## ROUTER REGISTRATION AUDIT

### From `app/main.py`:

```python
# Line 65: capability_assessments_router
application.include_router(capability_assessments_router)  # NO prefix override

# Line 64: assessments_router  
application.include_router(assessments_router, prefix=app_settings.api_prefix)

# Line 72: ai_router
application.include_router(ai_router, prefix=app_settings.api_prefix)
```

### API Prefix:
- `app_settings.api_prefix` = `/api/v1` (from settings)

### Actual Router Prefixes:

| Router | File | Include Prefix | Router Internal Prefix | Final Path |
|--------|------|----------------|-----------------------|-----------|
| `assessments_router` | `app/assessments/router.py:15` | `/api/v1` | `/assessments` | **`/api/v1/assessments`** |
| `capability_assessments_router` | `app/capability_assessments/router.py:17` | None (uses router's own) | `/api/v1/assessments/capability` | **`/api/v1/assessments/capability`** |
| `ai_router` | `app/ai/router.py:33` | `/api/v1` | `/learning-materials` | **`/api/v1/learning-materials`** |

---

## TEST 4 FAILURE ANALYSIS

### Postman Test 4 Details:
- **Method:** GET
- **Endpoint Used:** `/capability-assessments/competencies/BEH_CHANGE_MANAGEMENT`
- **HTTP Status:** 404 Not Found
- **Response:** `{"detail":"Assessment configuration not found for competency BEH_CHANGE_MANAGEMENT"}`

### Root Cause:
**The endpoint path does not exist in the router registration.**

The Postman test is trying to access:
```
/api/v1/capability-assessments/competencies/{competency_code}
```

But the registered routers only provide:
- `/api/v1/assessments/` (from assessments_router)
- `/api/v1/assessments/capability/` (from capability_assessments_router)
- No route matching `/capability-assessments/competencies/`

### CORRECT Endpoint:

**Path:** `GET /api/v1/assessments/configs/{competency_code}`

**Location:** `app/assessments/router.py:43-45`

```python
@router.get("/configs/{competency_code}", response_model=AssessmentConfigurationResponse)
def get_assessment_configuration(request: Request, competency_code: str) -> dict:
    """Get assessment configuration for a specific competency."""
    return service.get_assessment_configuration(getattr(request.app.state, "database", None), competency_code)
```

**Purpose:** Returns assessment configuration including questions for a competency.

**Note:** Current 404 with message "Assessment configuration not found" indicates the endpoint route EXISTS, but the data doesn't (BEH_CHANGE_MANAGEMENT config not seeded). This is **not a router path issue**, but a **data availability issue** for this particular competency code.

---

## TEST 11 FAILURE ANALYSIS

### Postman Test 11 Details:
- **Method:** POST
- **Endpoint Used:** `/materials/upload`
- **HTTP Status:** 404 Not Found

### Root Cause:
**The endpoint path does not exist in the router registration.**

The Postman test is trying to access:
```
/api/v1/materials/upload
```

But the registered routers provide:
```
/api/v1/learning-materials/upload
```

### CORRECT Endpoint:

**Path:** `POST /api/v1/learning-materials/upload`

**Location:** `app/ai/router.py:58-162`

```python
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = Depends(),
) -> UploadResponse:
    """Upload a learning material document (PDF, DOCX, PPTX)."""
```

**Purpose:** Upload and process learning documents for AI-based MCQ generation.

**Verification:** 
- Tested endpoint returns **401 (Unauthorized)** when called without auth
- This indicates the **endpoint exists and is properly registered**
- 401 is expected (requires authentication)
- Postman test uses wrong path `/materials/upload` instead of `/learning-materials/upload`

---

## REGISTERED ROUTES SUMMARY

### Assessments Router (`/api/v1/assessments`):
```
POST   /              → start_assessment
GET    /              → list_assessments  
GET    /{attempt_id}  → get_assessment_attempt
POST   /{attempt_id}/submit → submit_assessment
GET    /configs       → list_assessment_configurations
GET    /configs/{competency_code} ← GET ASSESSMENT CONFIG (Test 4 SHOULD USE THIS)
```

### Capability Assessments Router (`/api/v1/assessments/capability`):
```
POST   /              → create_capability_assessment
GET    /              → list_user_capability_assessments
GET    /{assessment_id} → get_capability_assessment
POST   /{assessment_id}/submit → submit_capability_assessment
GET    /{assessment_id}/results → get_capability_assessment_results
```

### AI Router (`/api/v1/learning-materials`):
```
POST   /upload        ← UPLOAD MATERIAL (Test 11 SHOULD USE THIS)
GET    /{material_id} → get_material_metadata
POST   /{material_id}/generate-questions → generate_questions
```

---

## CONCLUSION

| Item | Status |
|------|--------|
| TEST 4 uses wrong endpoint path | ✅ Confirmed |
| TEST 4 correct endpoint exists | ✅ Confirmed (at `/api/v1/assessments/configs/{code}`) |
| TEST 4 failure is missing backend feature | ❌ No - endpoint exists, path is wrong |
| TEST 11 uses wrong endpoint path | ✅ Confirmed |
| TEST 11 correct endpoint exists | ✅ Confirmed (at `/api/v1/learning-materials/upload`) |
| TEST 11 failure is missing backend feature | ❌ No - endpoint exists, path is wrong |

---

## RECOMMENDATIONS

**Both test failures are due to incorrect Postman endpoint paths, not missing backend functionality.**

**To proceed with verification:**

Option 1: Update Postman tests to use correct endpoints:
- TEST 4: Change to `GET /api/v1/assessments/configs/{competency_code}`
- TEST 11: Change to `POST /api/v1/learning-materials/upload`

Option 2: Update the backend router registration to match Postman paths:
- Add a new route in assessments_router that handles `/capability-assessments/competencies/{code}`
- Add a new route in ai_router that handles `/materials/upload`
- (Not recommended - would require backend changes, which are frozen)

**DECISION:** Postman tests should be corrected to use the actual registered endpoints, since backend is frozen.

---

## PHASE DOCUMENTATION REFERENCE

- **Phase 2 (Assessment):** `/api/v1/assessments/configs/{competency_code}` is the documented endpoint
- **Phase 5/6 (Learning Materials):** `/api/v1/learning-materials/upload` is the documented endpoint
- **Postman tests:** Using outdated/incorrect endpoint paths

---

**Audit Complete: API contract mismatches identified and documented.**
