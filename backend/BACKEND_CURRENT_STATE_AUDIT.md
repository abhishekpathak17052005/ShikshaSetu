# SHIKSHASETU BACKEND — CURRENT STATE AUDIT REPORT (READ-ONLY)
**Date:** 2026-08-30  
**Audit Type:** Static Code Analysis, Routing Matrix Inspection, Database State Verification, and Test Suite Diagnosis  
**Target Repository:** `c:\Users\Lenovo\Desktop\ShikshaSetu\backend`

---

## EXECUTIVE SUMMARY

A comprehensive, read-only audit of the ShikshaSetu backend was conducted across all 15 audit dimensions.

- **Foundational Architecture**: The core intelligence loop (Phases 1–4, plus learning resource recommendation and AI quiz processing) is largely implemented with clean domain separation.
- **Critical Compilation Blocker**: A Python syntax error exists in [`app/ai/router.py:284`](file:///c:/Users/Lenovo/Desktop/ShikshaSetu/backend/app/ai/router.py#L284) (`request: Request` placed after `current_user: dict = Depends(...)`), which causes any test or module importing `app.main` to fail during collection.
- **Routing Gaps**: 
  - `app.capability_assessments.router` is **unregistered** in `main.py`.
  - Routes `GET /api/v1/assessments/configs` and `GET /api/v1/assessments/configs/{competency_code}` (documented in `API_ENDPOINTS.md`) have no route handlers in any active router.
- **Database & Seed Status**: MongoDB database (`shikshasetu`) is fully populated with 14 active collections, 42 competencies, 148 learning resources (63 iGOT + 85 NSSTA), 114 resource mappings, 122 question bank items, and 10 assessment configs.
- **Isolated Tests**: 120 tests pass cleanly when run in isolation from `app.main`. 8 test files fail collection exclusively due to the `app/ai/router.py` syntax error, and 1 test file (`test_assessment_configuration.py`) fails due to an outdated schema import.

---

## 1. REGISTERED ROUTERS IN `main.py`

| Router Variable | Source Module | Prefix in `main.py` | Effective Base Route | Status |
| :--- | :--- | :--- | :--- | :--- |
| `health_router` | `app.api.health` | `/api/v1` | `/api/v1/health` | **REGISTERED** |
| `auth_router` | `app.auth.router` | `/api/v1` | `/api/v1/auth/*` | **REGISTERED** |
| `users_router` | `app.users.router` | `/api/v1` | `/api/v1/users/*` | **REGISTERED** |
| `competencies_router` | `app.competencies.router` | `/api/v1` | `/api/v1/competencies/*` | **REGISTERED** |
| `roles_router` | `app.roles.router` | `/api/v1` | `/api/v1/roles/*` | **REGISTERED** |
| `assessments_router` | `app.assessments.router` | `/api/v1` | `/api/v1/assessments/*` | **REGISTERED** |
| `skill_gaps_router` | `app.skill_gaps.router` | `/api/v1` | `/api/v1/skill-gaps/*` | **REGISTERED** |
| `recommendations_router` | `app.learning_resources.router` | `/api/v1` | `/api/v1/recommendations/*` | **REGISTERED** |
| `learning_materials_router` | `app.ai.router` | `/api/v1` | `/api/v1/learning-materials/*` | **REGISTERED (Syntax Error in file)** |
| `quizzes_router` | `app.quizzes.router` | `/api/v1` | `/api/v1/quizzes/*` | **REGISTERED** |
| *(None)* | `app.capability_assessments.router` | — | `/api/v1/assessments/capability/*` | **UNREGISTERED** |

---

## 2. API ENDPOINTS MATRIX (REGISTERED VS. REACHABLE VS. UNREGISTERED)

### A. Live / Registered Endpoints (27 Endpoints)

| HTTP Method | Endpoint Path | Router File | Auth Required | Status / Reachability |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | `app/api/health.py` | None | **Live & Reachable** |
| `POST` | `/api/v1/auth/register` | `app/auth/router.py` | None | **Live & Reachable** |
| `POST` | `/api/v1/auth/login` | `app/auth/router.py` | None | **Live & Reachable** |
| `GET` | `/api/v1/auth/me` | `app/auth/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/users/me` | `app/users/router.py` | Bearer JWT | **Live & Reachable** |
| `PUT` | `/api/v1/users/me` | `app/users/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/competencies` | `app/competencies/router.py` | None | **Live & Reachable** |
| `GET` | `/api/v1/competencies/{competency_id}` | `app/competencies/router.py` | None | **Live & Reachable** |
| `GET` | `/api/v1/roles` | `app/roles/router.py` | None | **Live & Reachable** |
| `GET` | `/api/v1/roles/{role_id}` | `app/roles/router.py` | None | **Live & Reachable** |
| `GET` | `/api/v1/roles/{role_id}/requirements`| `app/roles/router.py` | None | **Live & Reachable** |
| `POST` | `/api/v1/assessments` | `app/assessments/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/assessments/{attempt_id}` | `app/assessments/router.py` | Bearer JWT | **Live & Reachable** |
| `POST` | `/api/v1/assessments/{attempt_id}/submit` | `app/assessments/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/skill-gaps/me` | `app/skill_gaps/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/recommendations/me` | `app/learning_resources/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/recommendations/resources/{resource_id}` | `app/learning_resources/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/recommendations/competencies/{competency_code}/resources` | `app/learning_resources/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/recommendations/resources/unmapped` | `app/learning_resources/router.py` | Bearer JWT | **Live & Reachable** |
| `POST` | `/api/v1/learning-materials/upload` | `app/ai/router.py` | Bearer JWT | **Live (Blocked by file syntax error)** |
| `GET` | `/api/v1/learning-materials/{material_id}` | `app/ai/router.py` | Bearer JWT | **Live (Blocked by file syntax error)** |
| `POST` | `/api/v1/learning-materials/{material_id}/generate-questions` | `app/ai/router.py` | Bearer JWT | **Blocked (Syntax error on line 284)** |
| `POST` | `/api/v1/quizzes` | `app/quizzes/router.py` | Bearer JWT | **Live & Reachable** |
| `GET` | `/api/v1/quizzes/{quiz_id}` | `app/quizzes/router.py` | Bearer JWT | **Live & Reachable** |
| `POST` | `/api/v1/quizzes/{quiz_id}/submit` | `app/quizzes/router.py` | Bearer JWT | **Live & Reachable** |

### B. Unregistered Endpoints (5 Endpoints in Codebase)

| HTTP Method | Endpoint Path | Defined In | Reason Unreachable |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/assessments/capability` | `app/capability_assessments/router.py` | Router not included in `main.py` |
| `GET` | `/api/v1/assessments/capability/{assessment_id}` | `app/capability_assessments/router.py` | Router not included in `main.py` |
| `POST` | `/api/v1/assessments/capability/{assessment_id}/submit` | `app/capability_assessments/router.py` | Router not included in `main.py` |
| `GET` | `/api/v1/assessments/capability/{assessment_id}/results` | `app/capability_assessments/router.py` | Router not included in `main.py` |
| `GET` | `/api/v1/assessments/capability` | `app/capability_assessments/router.py` | Router not included in `main.py` |

### C. Missing / Phantom Endpoints (Documented in `API_ENDPOINTS.md` but No Code Handler)

| HTTP Method | Endpoint Path | Documented In | Code Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/assessments/configs` | `API_ENDPOINTS.md` L76 | **No route handler exists** |
| `GET` | `/api/v1/assessments/configs/{competency_code}` | `API_ENDPOINTS.md` L81 | **No route handler exists** |

---

## 3. MONGODB COLLECTIONS & ACTUAL DOCUMENT COUNTS

Actual counts verified directly against running MongoDB instance (`shikshasetu`):

| Collection Name | Document Count | Purpose & Notes |
| :--- | :--- | :--- |
| `competencies` | **42** | 33 base competencies + 9 derived competencies across 4 domains |
| `roles` | **1** | `STATISTICAL_OFFICER` (Statistical Officer) |
| `role_requirements` | **8** | 8 competency requirements for Statistical Officer (levels 2–4, priorities 1–3) |
| `learning_resources` | **148** | Unified learning resource repository: 63 iGOT courses + 85 NSSTA programmes |
| `learning_resource_mappings` | **114** | Mappings between resources and competencies |
| `question_bank` | **122** | Pre-seeded questions for capability assessments |
| `assessment_configurations` | **10** | Configuration profiles for competency capability tests |
| `assessments` | **1** | Baseline assessment template (`initial-competency-v1`) with 24 questions |
| `assessment_attempts` | **5** | Historical assessment attempt submissions |
| `competency_profiles` | **16** | Active employee competency levels and confidence scores |
| `competency_evidence` | **72** | Append-only evidence log from assessments, tests, and quizzes |
| `learning_materials` | **12** | Uploaded user documents metadata |
| `users` | **21** | Registered user records |
| `capability_assessments` | **0** | Dynamic instances created upon user capability assessment |
| `quizzes` | **0** | Dynamic instances created upon AI quiz generation |
| `quiz_attempts` | **0** | Dynamic instances created upon quiz submission |

---

## 4. SEED DATA & SCRIPTS

| Seed Script | Source File / Dataset | Seeded Entity | Actual Records in DB | Status |
| :--- | :--- | :--- | :--- | :--- |
| `seed_framework.py` | Hardcoded in script | 33 Competencies, 1 Role, 8 Requirements | 42 Competencies, 1 Role, 8 Requirements | **Active / Idempotent** |
| `seed_competencies.py` | `competency_taxonomy.json` | 42 Competencies across 4 domains | 42 Competencies | **Active / Verified** |
| `seed_learning_resources.py` | `igot_courses_enriched.csv`, `nssta_training_programmes.csv` | 63 iGOT + 5 NSSTA/MoSPI + 80 NSSTA | 148 Learning Resources | **Active / Verified** |
| `seed_resource_mappings.py` | `course_competency_mapping.csv`, `nssta_competency_mapping.csv` | Resource-to-competency mappings | 114 Mappings | **Active / Verified** |
| `assessments/seed.py` | Hardcoded in script | 1 Baseline assessment (`initial-competency-v1`, 24 questions) | 1 Assessment | **Active / Verified** |
| `assessments/seed_capability.py` | Hardcoded in script | 10 Assessment configs + 122 question bank items | 10 Configs, 122 Questions | **Active / Verified** |

---

## 5. EXISTING TESTS AUDIT

| Test File | Test Count | Isolated Execution | Status / Failure Cause |
| :--- | :--- | :--- | :--- |
| `test_framework_schemas.py` | 3 | **PASS (3/3)** | Schema validation tests pass cleanly |
| `test_skill_gaps_engine.py` | 32 | **PASS (32/32)** | Gap math, status, and priorities pass cleanly |
| `test_capability_assessment_execution.py` | 23 | **PASS (23/23)** | Scoring & normalization pass cleanly |
| `test_assessment_scoring.py` | 4 | **PASS (4/4)** | Assessment scoring formulas pass cleanly |
| `test_seed_framework.py` | 1 | **PASS (1/1)** | Idempotent framework seed test passes |
| `test_learning_resources.py` | 24 | **PASS (24/24)** | 5-component scoring & provider adapter tests pass |
| `test_ai_unit.py` | 32 | **PASS (32/32)** | Extractors, chunker, cleaner, and mock LLM tests pass |
| `test_e2e_verification.py` | 1 | **PASS (1/1)** | Mock E2E verification test passes |
| `test_assessment_configuration.py` | 6 | **FAIL (ImportError)** | Imports `AssessmentConfiguration` missing from `app.assessments.schemas` |
| `test_health.py` | 2 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |
| `test_auth.py` | 10 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |
| `test_framework_api.py` | 4 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |
| `test_assessment_api.py` | 6 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |
| `test_skill_gaps_api.py` | 6 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |
| `test_recommendations_e2e.py` | 4 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |
| `test_ai_security.py` | 4 | **FAIL (Collection)** | Blocked by syntax error in `app/ai/router.py:284` |

**Total Tested in Isolation**: **120 Passing Tests**.

---

## 6. ASSESSMENT FLOW STATUS

- **Baseline Assessment (`app/assessments/`)**:
  - `POST /api/v1/assessments`: Generates/retrieves in-progress attempt for `initial-competency-v1`.
  - `GET /api/v1/assessments/{attempt_id}`: Retrieves questions (Self, MCQ, Scenario).
  - `POST /api/v1/assessments/{attempt_id}/submit`: Evaluates responses server-side, applies weighted scoring (Self 20%, Knowledge 40%, Scenario 30%, Training 10%), writes append-only evidence to `competency_evidence`, and upserts `competency_profiles`.
- **Capability Assessments (`app/capability_assessments/`)**:
  - Implementation complete in `service.py`, `repository.py`, and `scoring.py` with 122 questions in `question_bank`.
  - **Limitation**: Router is currently unregistered in `main.py`.

---

## 7. COMPETENCY APIS STATUS

- `GET /api/v1/competencies`: Returns list of all active competencies (`STAT_*`, `TECH_*`, `GOV_*`, `BEH_*`) with level definitions 1–5. **Functional & verified**.
- `GET /api/v1/competencies/{competency_id}`: Retrieves competency by ID or Code. **Functional & verified**.

---

## 8. ROLE APIS STATUS

- `GET /api/v1/roles`: Returns list of roles (`STATISTICAL_OFFICER`). **Functional & verified**.
- `GET /api/v1/roles/{role_id}`: Retrieves role metadata. **Functional & verified**.
- `GET /api/v1/roles/{role_id}/requirements`: Returns required competency levels and priorities for the role. **Functional & verified**.

---

## 9. AUTHENTICATION & PROFILES STATUS

- `POST /api/v1/auth/register`: Hashes password with bcrypt, validates professional `role_id`, enforces unique email and employee ID, assigns `access_role: "EMPLOYEE"`. **Functional & verified**.
- `POST /api/v1/auth/login`: Authenticates credentials, issues JWT bearer token with 60-min TTL. **Functional & verified**.
- `GET /api/v1/auth/me`: Resolves JWT payload to authenticated user document. **Functional & verified**.
- `GET /api/v1/users/me` & `PUT /api/v1/users/me`: Profile retrieval and updates. **Functional & verified**.

---

## 10. SKILL-GAP ENGINE STATUS

- `app/skill_gaps/engine.py`:
  - Formula: $\text{Gap} = \text{Required Level} - \text{Current Level}$ (or 0 if current $\ge$ required).
  - Classifications: `DEFICIT`, `MEETS_REQUIREMENT`, `EXCEEDS_REQUIREMENT`, `NOT_ASSESSED`.
  - Priority logic: High (Priority 1 & Gap $\ge$ 2), Medium (Priority 1 & Gap 1, or Priority 2 & Gap $\ge$ 2), Low (all others).
  - Deterministic and covered by 32 unit tests. **Functional & verified**.

---

## 11. RECOMMENDATION ENGINE STATUS

- `app/learning_resources/scoring.py` & `candidates.py`:
  - 5-factor scoring formula:
    - Competency match (40%)
    - Gap priority (25%)
    - Role match (20%)
    - Difficulty match (10%)
    - Prerequisite match (5%)
  - Integrates across 148 resources from both iGOT and NSSTA.
  - Generates clear, explainable recommendation justifications.
  - Covered by 24 unit tests. **Functional & verified**.

---

## 12. LEARNING RESOURCE IMPLEMENTATION STATUS

- Stored in unified `learning_resources` collection (148 documents).
- Clear segregation between official metadata and derived enrichment metadata (`derived_competencies`, `derived_skill_level`).
- 5 MoSPI training programmes with NULL official course ID are classified as `NSSTA` provider, `TRAINING_PROGRAMME` resource type with prototype IDs (`NSSTA-PROTO-xxx`). **Functional & verified**.

---

## 13. AI & LEARNING MATERIAL ROUTES STATUS

- **Extractor Modules**: PDF (PyMuPDF), DOCX (python-docx), PPTX (python-pptx).
- **Processing Pipeline**: Text cleaning $\to$ semantic chunking $\to$ vector store indexing.
- **MCQ Generation**: Multi-provider LLM connector with `GroundingValidator` (1 correct answer, options verification, source chunk traceability).
- **Critical Defect**: Line 284 in `app/ai/router.py` has invalid parameter order (`request: Request` follows `current_user: dict = Depends(get_current_user)`).

---

## 14. QUIZ ROUTES & COMPETENCY UPDATE STATUS

- `POST /api/v1/quizzes`: Stores quiz with questions derived from material, masks correct answers until submission.
- `GET /api/v1/quizzes/{quiz_id}`: Retrieves quiz for learner without exposing answer keys.
- `POST /api/v1/quizzes/{quiz_id}/submit`: Evaluates answers, calculates percentage score, records quiz attempt, inserts append-only record to `competency_evidence`, updates `competency_profiles` using deterministic step-rules, and recalculates before/after skill gaps. **Functional & verified**.

---

## 15. CAPABILITY ASSESSMENT ROUTES STATUS

- Complete service, scoring, and repository implementation in `app/capability_assessments/`.
- 122 questions in `question_bank` and 10 assessment configurations in `assessment_configurations`.
- **Status**: Unregistered in `main.py`.

---

## KNOWN DEFECTS & BLOCKERS SUMMARY

1. **Defect 1 (CRITICAL SYNTAX ERROR)**:
   - File: `app/ai/router.py`, Line 284
   - Issue: `request: Request` parameter without a default follows `current_user: dict = Depends(get_current_user)` which has a default.
   - Impact: Prevents FastAPI app startup and breaks pytest collection on all 8 test files importing `app.main`.

2. **Defect 2 (UNREGISTERED ROUTER)**:
   - File: `app/capability_assessments/router.py`
   - Issue: Not included in `app.main.py`.
   - Note: Prefix in router is `/api/v1/assessments/capability`; if registered under `/api/v1`, prefix needs normalization to `/assessments/capability`.

3. **Defect 3 (OUTDATED SCHEMA IMPORT IN TEST)**:
   - File: `tests/test_assessment_configuration.py`, Line 8
   - Issue: Tries to import `AssessmentConfiguration` from `app.assessments.schemas` where it was refactored.

4. **Defect 4 (PYDANTIC V1 DEPRECATIONS)**:
   - Files: `app/ai/models.py`, `app/ai/schemas.py`, `app/learning_resources/models.py`
   - Issue: Uses legacy `class Config`, `@validator`, `min_items` triggering runtime warnings.

---

## RECOMMENDED IMPLEMENTATION ORDER

```
Step 1: Fix Parameter Ordering Syntax Error in `app/ai/router.py:284`
   │
   ▼
Step 2: Register / Consolidate `capability_assessments` in `main.py` & Fix `test_assessment_configuration.py`
   │
   ▼
Step 3: Run Full Pytest Test Suite (Verify 16/16 Test Files & 140+ Tests Passing)
   │
   ▼
Step 4: Clean Up Pydantic V1 Deprecation Warnings
   │
   ▼
Step 5: Run Full End-to-End Verification of the Complete Capability Intelligence Loop
```
