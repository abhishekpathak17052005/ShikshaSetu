# ShikshaSetu — 22-Test Postman Verification Suite

**Status:** AUTHORITATIVE SPECIFICATION (reconstructed from backend code)  
**Backend Version:** 0.3.0  
**API Prefix:** `/api/v1`  
**Server:** `http://127.0.0.1:8001`  
**Database State:** 42 competencies, 148 resources, 114 mappings, 10 assessment configs

---

## Test Execution Rules

- **Execute tests in order** (tests 1-3 establish auth session)
- **Stop at first genuine failure** — report exact status code and response
- **Preserve all original test payloads** — no modifications to make tests pass
- **BEH_CHANGE_MANAGEMENT request unchanged** — document 404 as data gap if returned
- **Upload test without `scope` parameter** — expect 200 OK
- **Classification:** Classify failures by root cause (missing data, API defect, etc.)

---

## 22-Test Sequence

### PHASE 1: Authentication & Setup (Tests 1-3)

#### Test 1: Health Check
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/health`
- **Auth:** None
- **Expected Status:** 200
- **Expected Response:** `{ "status": "ok", "service": "ShikshaSetu Backend", "database": "connected" }`
- **Purpose:** Verify backend is running

#### Test 2: Register Test User
- **Method:** POST
- **URL:** `http://127.0.0.1:8001/api/v1/auth/register`
- **Auth:** None
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "email": "postman_test_user@example.com",
    "password": "TestPassword123!",
    "full_name": "Postman Test Employee",
    "role_id": "6a8fe8048524f6da8ebb9881",
    "designation": "Test Officer",
    "department": "Testing",
    "employee_id": "POSTMAN001"
  }
  ```
- **Expected Status:** 201
- **Store:** `user_id` from response for subsequent tests
- **Purpose:** Create test user

#### Test 3: Login & Get JWT Token
- **Method:** POST
- **URL:** `http://127.0.0.1:8001/api/v1/auth/login`
- **Auth:** None
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "email": "postman_test_user@example.com",
    "password": "TestPassword123!"
  }
  ```
- **Expected Status:** 200
- **Store:** `access_token` from response for all subsequent authenticated requests
- **Purpose:** Obtain JWT token

---

### PHASE 2: Core Data Verification (Tests 4-10)

#### Test 4: Get Assessment Configuration for BEH_CHANGE_MANAGEMENT ⚠️
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/assessments/configs/BEH_CHANGE_MANAGEMENT`
- **Auth:** Bearer token (from Test 3)
- **Expected Status:** 200 OR 404 (data gap)
- **Classification if 404:** Data Gap — BEH_CHANGE_MANAGEMENT competency exists but no assessment config seeded
- **Purpose:** Test assessment configuration endpoint with original competency code (do NOT substitute)

#### Test 5: List All Assessment Configurations
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/assessments/configs`
- **Auth:** None
- **Expected Status:** 200
- **Expected Response:** Array of 10 assessment configurations (excluding BEH_CHANGE_MANAGEMENT)
- **Purpose:** Verify assessment configuration seeding

#### Test 6: Get All Competencies
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/competencies`
- **Auth:** None
- **Expected Status:** 200
- **Expected Response:** Array of 42 competencies
- **Purpose:** Verify expanded competency dataset

#### Test 7: Get Specific Competency
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/competencies/{competency_id}`
- **Auth:** None
- **Path Parameters:** Use first competency ID from Test 6
- **Expected Status:** 200
- **Purpose:** Verify competency detail endpoint

#### Test 8: Get Roles
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/roles`
- **Auth:** None
- **Expected Status:** 200
- **Expected Response:** Array with 1 role (STATISTICAL_OFFICER)
- **Purpose:** Verify role data

#### Test 9: Get Role Requirements
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/roles/{role_id}`
- **Auth:** None
- **Path Parameters:** Use role ID from Test 8
- **Expected Status:** 200
- **Purpose:** Verify role detail endpoint

#### Test 10: Get Skill Gaps (Authenticated)
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/skill-gaps/me`
- **Auth:** Bearer token (from Test 3)
- **Expected Status:** 200 or 404 (if no role requirements)
- **Purpose:** Test skill gap calculation for authenticated user

---

### PHASE 3: Document Upload & Processing (Tests 11-15)

#### Test 11: Upload PDF Document ✅
- **Method:** POST
- **URL:** `http://127.0.0.1:8001/api/v1/learning-materials/upload`
- **Auth:** Bearer token (from Test 3)
- **Content-Type:** `multipart/form-data`
- **Request:** Upload a valid PDF file (e.g., test.pdf)
- **IMPORTANT:** NO `scope` parameter in request body
- **Expected Status:** 200 or 201
- **Store:** `material_id` from response
- **Purpose:** Test upload endpoint without unwanted `scope` parameter (this was the authorized fix)

#### Test 12: Get Upload Material Metadata
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/learning-materials/{material_id}`
- **Auth:** Bearer token
- **Path Parameters:** Use `material_id` from Test 11
- **Expected Status:** 200
- **Purpose:** Verify uploaded material metadata

#### Test 13: Get Learning Recommendations
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/recommendations/me`
- **Auth:** Bearer token
- **Expected Status:** 200 or 404
- **Purpose:** Test recommendation engine

#### Test 14: Get Recommendations for Specific Competency
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/recommendations/competencies/STAT_SAMPLING/resources`
- **Auth:** Bearer token
- **Query Parameters:** `provider=IGOT` (optional)
- **Expected Status:** 200 or 404
- **Purpose:** Test competency-specific resource retrieval

#### Test 15: Get Resource Details
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/recommendations/resources/{resource_id}`
- **Auth:** Bearer token
- **Path Parameters:** Use a resource ID from Test 14 or known resource
- **Expected Status:** 200 or 404
- **Purpose:** Test resource detail endpoint

---

### PHASE 4: Capability Assessment (Tests 16-19)

#### Test 16: Create Capability Assessment
- **Method:** POST
- **URL:** `http://127.0.0.1:8001/api/v1/assessments/capability`
- **Auth:** Bearer token
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "competency_code": "TECH_PYTHON"
  }
  ```
- **Expected Status:** 201 or 400 (if no questions available)
- **Store:** `assessment_id` from response
- **Purpose:** Create capability assessment for tech competency

#### Test 17: Get Capability Assessment
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/assessments/capability/{assessment_id}`
- **Auth:** Bearer token
- **Path Parameters:** Use `assessment_id` from Test 16
- **Expected Status:** 200 or 404
- **Purpose:** Retrieve created assessment

#### Test 18: List User's Capability Assessments
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/assessments/capability`
- **Auth:** Bearer token
- **Query Parameters:** `limit=10` (optional)
- **Expected Status:** 200
- **Purpose:** List all assessments for user

#### Test 19: Submit Capability Assessment (if assessment exists)
- **Method:** POST
- **URL:** `http://127.0.0.1:8001/api/v1/assessments/capability/{assessment_id}/submit`
- **Auth:** Bearer token
- **Path Parameters:** Use `assessment_id` from Test 16 (if available)
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "answers": {
      "q1": "option_a",
      "q2": "option_b"
    }
  }
  ```
- **Expected Status:** 200 or 400 (if validation fails)
- **Purpose:** Submit assessment answers

---

### PHASE 5: Authorization & Security (Tests 20-22)

#### Test 20: Unauthenticated Request to Protected Endpoint
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/skill-gaps/me`
- **Auth:** None (intentionally omit authorization)
- **Expected Status:** 401
- **Expected Response:** `{ "detail": "Could not validate credentials" }`
- **Purpose:** Verify authentication enforcement

#### Test 21: Invalid Token
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/skill-gaps/me`
- **Auth:** Bearer `invalid_token_12345`
- **Expected Status:** 401
- **Purpose:** Verify JWT validation

#### Test 22: Get Current User Profile
- **Method:** GET
- **URL:** `http://127.0.0.1:8001/api/v1/users/me`
- **Auth:** Bearer token (from Test 3)
- **Expected Status:** 200
- **Purpose:** Verify authenticated user profile retrieval

---

## Test Dependency Graph

```
Test 1 (Health)
    ↓
Test 2 (Register) → Test 3 (Login) → [All authenticated tests: 4, 10-22]
    ↓                                  ↓
Test 5-9 (Public data)           Test 11 (Upload) → Test 12, 13, 14, 15
                                      ↓
                                 Test 16 (Assessment) → Test 17, 18, 19
                                      ↓
                                 Test 20, 21, 22 (Security)
```

---

## Known Data Gaps (By Design)

| Gap | Expected | Actual | Classification |
|-----|----------|--------|-----------------|
| BEH_CHANGE_MANAGEMENT config | Exists | Does NOT exist | Data Gap (not backend defect) |
| Assessment questions | Available | May be 0 | Data Gap (depends on question bank seeding) |

---

## Failure Classification

When a test fails, classify by root cause:

- **API Defect:** Endpoint returns unexpected status or response structure
- **Data Gap:** Endpoint exists but required data missing (e.g., BEH_CHANGE_MANAGEMENT config)
- **Authentication Issue:** JWT or authorization problem
- **Validation Error:** Invalid request payload
- **Configuration Issue:** LLM provider, database, or environment configuration

---

## Execution Instructions

1. **Update server URL** if not `http://127.0.0.1:8001`
2. **Execute tests in order** (1 → 22)
3. **Store tokens** from Test 3 for all authenticated requests
4. **Stop on first genuine failure** — do not skip or modify tests
5. **Report exact HTTP status, request body, response body** for every failure
6. **Classify** each failure by root cause

---

**End of Specification**
