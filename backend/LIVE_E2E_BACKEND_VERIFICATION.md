# Live Backend E2E Verification — ShikshaSetu

**Date**: August 31, 2026  
**Auditor / Engineer**: Backend & AI Engineering (Abhishek)  
**Database**: `shikshasetu` (MongoDB Live Instance)  
**Verification Baseline**: 164 / 164 Pytest tests passing  
**Status**: Verification Complete — Exact Code Defects Identified

---

## 1. Environment

- **Operating System**: Windows (x86_64)
- **Runtime / Python**: Python 3.13.x Virtual Environment (`.venv`)
- **Web Framework**: FastAPI (Uvicorn ASGI)
- **Database Engine**: MongoDB Community Server (`localhost:27017`)
- **Primary Database**: `shikshasetu`
- **Test Isolation Database**: `shikshasetu_test`
- **LLM / Embedding Stack**: Google Gemini API Provider + Fallback Mock Provider

---

## 2. Baseline

- **42 Competencies** across 4 domains (`STATISTICAL`, `TECHNICAL`, `DIGITAL_GOVERNANCE`, `BEHAVIOURAL_MANAGERIAL`) with normalized canonical underscore codes.
- **1 Active Role**: `STATISTICAL_OFFICER` (`_id: 6a8fe8048524f6da8ebb9881`).
- **8 Role Requirements**: 100% mapped to active competency ObjectIds with required proficiency levels and priority weights.
- **10 Active Assessment Configurations**: Covering core technical, statistical, digital governance, and behavioural competencies.
- **122 Question Bank Questions**: Pre-authored, multi-difficulty (Easy, Medium, Hard), 0 duplicates.
- **148 Learning Resources**: 63 iGOT Karmayogi + 85 NSSTA modules.
- **114 Learning Resource Mappings**: 100% resolved foreign keys.
- **21 Users**: Preserved with active role assignments.
- **16 Competency Profiles & 72 Evidence Records**: 100% foreign key integrity.
- **`BEH_CHANGE_MANAGEMENT`**: Preserved as a legitimate data gap (0 configurations, 0 questions).

---

## 3. Authentication Workflow

- **Registration (`POST /api/v1/auth/register`)**: 🟢 **PASS**
  - Successfully registered test user with required fields (`email`, `password`, `full_name`, `role_id`, `designation`, `department`, `employee_id`).
  - Correctly validated active role existence.
  - Returned HTTP `201 Created` with sanitized `UserResponse`.
- **Login (`POST /api/v1/auth/login`)**: 🟢 **PASS**
  - Authenticated user credentials via bcrypt/PBKDF2 verification.
  - Returned HTTP `200 OK` with valid JWT bearer access token (`HS256`).
- **Get Current User (`GET /api/v1/auth/me`)**: 🟢 **PASS**
  - Validated JWT signature and returned authenticated employee profile.
- **Profile Update (`PUT /api/v1/users/me`)**: 🟢 **PASS**
  - Updated mutable fields (`designation`, `department`).
- **Security Rejections**: 🟢 **PASS**
  - Unauthenticated request returned `401 Unauthorized`.
  - Invalid / forged JWT token returned `401 Unauthorized`.

---

## 4. Competency Framework Workflow

- **List All Competencies (`GET /api/v1/competencies`)**: 🟢 **PASS**
  - Returned all 42 canonical competencies.
  - Verified domain enum serialization (`STATISTICAL`, `TECHNICAL`, `DIGITAL_GOVERNANCE`, `BEHAVIOURAL_MANAGERIAL`).
- **Get Single Competency (`GET /api/v1/competencies/{id}`)**: 🟢 **PASS**
  - Successfully retrieved `STAT_SAMPLING` by its active MongoDB `_id`.
- **List Roles (`GET /api/v1/roles`)**: 🟢 **PASS**
  - Returned active role catalog including `STATISTICAL_OFFICER`.
- **Get Role Requirements (`GET /api/v1/roles/{role_id}/requirements`)**: 🟢 **PASS**
  - Returned all 8 requirements for Statistical Officer with required levels, priorities (P1, P2, P3), and importance weights (1.0, 0.75, 0.50).

---

## 5. Initial Assessment Workflow

- **Start Assessment (`POST /api/v1/assessments`)**: 🟢 **PASS**
  - Payload: `{"assessment_key": "initial-competency-v1"}`.
  - Created new in-progress assessment attempt record. Returned HTTP `201 Created` with unique `attempt_id`.
- **Retrieve Questions (`GET /api/v1/assessments/{attempt_id}`)**: 🟢 **PASS**
  - Retrieved all 24 questions across the 8 Statistical Officer competencies.
  - Verified question types: `SELF_RATING` (8), `MCQ` (8), `SCENARIO` (8).
- **Submit Assessment (`POST /api/v1/assessments/{attempt_id}/submit`)**: 🟢 **PASS**
  - Submitted `self_ratings`, `answers`, and `training_evidence`.
  - Executed server-side 4-component weighted scoring algorithm:
    $$\text{Score} = (0.20 \times \text{Self}) + (0.40 \times \text{Knowledge}) + (0.30 \times \text{Scenario}) + (0.10 \times \text{Training})$$
  - Upserted 8 `competency_profiles` records and logged 24 append-only audit records in `competency_evidence`.
- **Duplicate Submission Rejection**: 🟢 **PASS**
  - Re-submitting the same attempt returned HTTP `400 Bad Request` ("Assessment has already been submitted").

---

## 6. Skill Gap Workflow

- **Calculate Skill Gaps (`GET /api/v1/skill-gaps/me`)**: 🟢 **PASS**
  - Evaluated current proficiency levels against role requirements for all 8 competencies.
  - Mathematical integrity verified:
    $$\text{Gap} = \max(0.0, \text{Required Level} - \text{Current Level})$$
  - Verified priority ordering ($P_1 \to P_2 \to P_3$).
  - Correctly categorized gap severities (`CRITICAL_GAP`, `MODERATE_GAP`, `MEETS_REQUIREMENT`).

---

## 7. Recommendation Workflow

- **Ranked Recommendations (`GET /api/v1/recommendations/me`)**: 🟢 **PASS**
  - Matched courses from 148-course iGOT/NSSTA catalog to employee's active skill gaps.
  - Deterministic 5-factor weighted formula evaluated:
    $$\text{Score} = (0.30 \times \text{Domain}) + (0.25 \times \text{Gap Severity}) + (0.20 \times \text{Level Match}) + (0.15 \times \text{Duration}) + (0.10 \times \text{Provider})$$
  - Generated human-readable explanation strings citing gap severity and role priority.
- **Competency Course Filtering (`GET /api/v1/recommendations/competencies/{code}/resources`)**: 🟢 **PASS**
  - Retrieved all catalog courses mapped to specific competency (e.g. `TECH_SQL`).

---

## 8. Capability Assessment Workflow

- **Create Capability Assessment (`POST /api/v1/assessments/capability`)**: 🔴 **FAIL (Code Defect)**
  - **Endpoint**: `POST /api/v1/assessments/capability`
  - **Payload**: `{"competency_code": "TECH_PYTHON"}`
  - **HTTP Status**: `500 Internal Server Error` (FastAPI `ResponseValidationError`)
  - **Response Traceback**:
    ```
    fastapi.exceptions.ResponseValidationError: 1 validation error:
    {'type': 'missing', 'loc': ('response', '_id'), 'msg': 'Field required',
     'input': {'id': '6a94791aa5f00e93c0cdc4e6', 'competency_code': 'TECH_PYTHON', ...}}
    ```
  - **Expected Behavior**: Returns `201 Created` with serialized `CapabilityAssessmentResponse` containing assessment ID, title, competency code, and questions with answer keys stripped.
  - **Actual Behavior**: The database document is successfully created, but response serialization throws `ResponseValidationError`.
  - **Exact Root Cause**: In `backend/app/capability_assessments/schemas.py:31`, `CapabilityAssessmentResponse` defines `id: str = Field(alias="_id")` and `model_config = ConfigDict(from_attributes=True)` without `populate_by_name=True`. When the service returns a dictionary containing `"id"`, Pydantic v2 strictly rejects it because the alias `_id` is not present in the dictionary.
  - **Classification**: **CODE DEFECT** (Pydantic v2 Response Schema Configuration).

---

## 9. Learning Material / RAG Workflow

- **Upload Learning Document (`POST /api/v1/learning-materials/upload`)**: 🟢 **PASS**
  - Accepted valid PDF document.
  - Validated file extension, created `learning_materials` database record, and saved binary payload to storage.
  - Returned HTTP `200 OK` with `material_id`.
- **RAG MCQ Generation (`POST /api/v1/learning-materials/{id}/generate-questions`)**: 🟣 **ENVIRONMENT GAP**
  - When external Google Gemini API credentials are unconfigured or rate-limited, system returns descriptive HTTP status.
  - The offline mock provider functions cleanly for deterministic unit/integration testing.

---

## 10. Quiz Workflow

- **Create Quiz (`POST /api/v1/quizzes`)**: 🔴 **FAIL (Code Defect)**
  - **Endpoint**: `POST /api/v1/quizzes`
  - **Payload**: `{"material_id": "<material_id>", "competency_code": "TECH_PYTHON", "questions": [...]}`
  - **HTTP Status**: `400 Bad Request` (`{"detail": "Material not found or does not belong to user"}`)
  - **Expected Behavior**: Validates that the uploaded material belongs to the requesting user and creates the quiz document.
  - **Actual Behavior**: `learning_materials` stores `user_id` as a string (`"6a94795078620ea83ebb0746"`), while `app/quizzes/service.py:52` performs a strict MongoDB query using `ObjectId(user_id)`: `find_one({"_id": material_oid, "user_id": user_oid})`. Because MongoDB queries are type-sensitive (BSON ObjectId $\neq$ string), the lookup fails to match the owner.
  - **Exact Root Cause**: Type mismatch in `app/quizzes/service.py:52-54` — `learning_materials.user_id` string vs `ObjectId` lookup.
  - **Classification**: **CODE DEFECT** (Data Type Mismatch in Ownership Lookup).

---

## 11. Security & Ownership Isolation Workflow

- **Cross-User Isolation**: 🟢 **PASS**
  - Verified User B cannot access User A's initial assessment attempt (`404 / 403`).
- **Immutable Fields Protection**: 🟢 **PASS**
  - Attempting to modify `email`, `role_id`, or `access_role` via `PUT /api/v1/users/me` was strictly ignored/blocked; user identity remained immutable.
- **Token Security**: 🟢 **PASS**
  - Expired, forged, and missing tokens are strictly rejected with `401 Unauthorized`.

---

## 12. Database Integrity After Execution

- **Orphan Records**: **0** orphaned competency ObjectIds in `role_requirements`, `competency_profiles`, and `competency_evidence`.
- **Foreign Key Validity**: **100%** resolution across all database collections.
- **Collection Growth**: Only expected runtime records created (new test user accounts, assessment attempts, evidence records, learning materials).

---

## 13. Complete Learning Loop Status

```
[1] Document Ingestion (POST /learning-materials/upload) ─────────────► 🟢 WORKING
[2] Text Extraction & Chunking ──────────────────────────────────────► 🟢 WORKING
[3] RAG Question Generation (POST /generate-questions) ──────────────► 🟣 ENV GAP (Requires Gemini Key)
[4] Quiz Creation (POST /quizzes) ───────────────────────────────────► 🔴 BLOCKED (user_id type mismatch)
[5] Quiz Attempt & Submission (POST /quizzes/{id}/submit) ───────────► 🟢 CODE READY
[6] Server-side Scoring & Evidence Logging ──────────────────────────► 🟢 WORKING
[7] Competency Profile Level Update ─────────────────────────────────► 🟢 WORKING
[8] Skill Gap Recalculation (GET /skill-gaps/me) ────────────────────► 🟢 WORKING
[9] Ranked Course Recommendations (GET /recommendations/me) ─────────► 🟢 WORKING
```

---

## 14. Identified Failures & Exact Root Causes

### Failure 1: Capability Assessment Response Serialization
- **Workflow**: Workflow 6 (Capability Assessment)
- **Endpoint**: `POST /api/v1/assessments/capability`
- **HTTP Status**: `500 Internal Server Error`
- **Request**: `POST /api/v1/assessments/capability` with `{"competency_code": "TECH_PYTHON"}`
- **Response**: `ResponseValidationError` (`Field required: _id`)
- **Expected**: `201 Created` with serialized `CapabilityAssessmentResponse`
- **Actual**: `500 ResponseValidationError`
- **Exact Root Cause**: `app/capability_assessments/schemas.py:31` lacks `populate_by_name=True` in `ConfigDict`.
- **Classification**: 🔴 **CODE DEFECT**

### Failure 2: Quiz Ownership Material ID Type Mismatch
- **Workflow**: Workflow 8 (Quiz)
- **Endpoint**: `POST /api/v1/quizzes`
- **HTTP Status**: `400 Bad Request`
- **Request**: `POST /api/v1/quizzes` with valid `material_id` and questions
- **Response**: `{"detail": "Material not found or does not belong to user"}`
- **Expected**: `201 Created` with `QuizResponse`
- **Actual**: `400 Bad Request`
- **Exact Root Cause**: `app/quizzes/service.py:52-54` queries `learning_materials` with `ObjectId(user_id)` whereas `learning_materials` stores `user_id` as `str`.
- **Classification**: 🔴 **CODE DEFECT**

---

## 15. Data Gaps

- 🔵 **BEH_CHANGE_MANAGEMENT**: Preserved in taxonomy; intentionally has 0 assessment configurations and 0 authored questions.

---

## 16. Environment Gaps

- 🟣 **Live Gemini API Credentials**: Ingestion and RAG question generation require active `GEMINI_API_KEY` in environment for live document AI demonstrations.

---

## 17. Production Readiness Matrix

| Workflow | Status | Blocker Summary |
| :--- | :---: | :--- |
| **1. Authentication** | 🟢 **PASS** | Fully operational. |
| **2. Competency Framework** | 🟢 **PASS** | 42 competencies, roles, and requirements fully operational. |
| **3. Initial Assessment** | 🟢 **PASS** | 4-component weighted scoring & evidence logging fully operational. |
| **4. Skill Gap Engine** | 🟢 **PASS** | Deterministic mathematical gap calculation operational. |
| **5. Recommendation Engine** | 🟢 **PASS** | Deterministic 5-factor course ranking operational. |
| **6. Capability Assessment** | 🔴 **FAIL** | Blocked by Pydantic v2 `ConfigDict` missing `populate_by_name=True`. |
| **7. Learning Material / RAG** | 🟣 **ENV GAP** | Upload works; LLM generation requires live API key. |
| **8. Quiz Workflow** | 🔴 **FAIL** | Blocked by string vs ObjectId `user_id` lookup in `quizzes/service.py`. |
| **9. Security & Isolation** | 🟢 **PASS** | Cross-user isolation and token validation fully operational. |
| **10. Data Integrity** | 🟢 **PASS** | 0 orphaned foreign keys. |

---

## 18. Test Baseline Verification

- **`python -m compileall -q app tests`**: **PASS** (Exit code 0).
- **`python -m pytest -q`**: **164 PASSED, 4 SKIPPED, 0 FAILURES**.

---

**VERIFICATION COMPLETE. NO APPLICATION CODE MODIFIED. BACKEND REMAINS FROZEN AT 164/164 TESTS PASSING.**
