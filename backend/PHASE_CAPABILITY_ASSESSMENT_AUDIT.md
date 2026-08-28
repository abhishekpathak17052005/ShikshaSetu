# PHASE 0 — TECHNICAL AUDIT

## CAPABILITY ASSESSMENT ENGINE IMPLEMENTATION

**Date:** August 27, 2026  
**Project:** ShikshaSetu — SIH 2026 PS 26101  
**Phase:** Capability Assessment Engine Backend (Post-Quiz Engine)  
**Audit Status:** ✅ COMPLETE

---

## 1. CURRENT TECHNOLOGY STACK

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Backend API | FastAPI | Latest | Active, production-quality |
| Language | Python | 3.13.14 | Windows; confirmed working |
| Database | MongoDB | Local/configured | PyMongo driver; local testing |
| Validation | Pydantic | v2.x | ConfigDict; field_validator patterns |
| Authentication | JWT | Native Python | hash_password + JWT tokens |
| Testing | pytest | 8.4.2 | 103/103 tests currently passing |
| AI/LLM | google-generativeai | Deprecated but working | Gemini 3.6 Flash (Phase 6) |
| Embeddings | Gemini Embeddings | 001 model | 3072-dim vectors (Phase 6) |
| PDF Processing | PyMuPDF (fitz) | Integrated | Document chunking working |
| Git | git | N/A | BACKEND_FOUNDATION_IMPLEMENTATION branch |

---

## 2. BACKEND ARCHITECTURE

### 2.1 Current Structure

```
app/
├── main.py                 # FastAPI app + lifespan + router registration
├── core/
│   ├── config.py          # Settings via pydantic BaseSettings
│   ├── database.py        # MongoDB connection (initialize_database, close_database)
│   └── framework_indexes.py # Index creation
├── auth/
│   ├── dependencies.py    # get_current_user (JWT)
│   ├── router.py          # POST /login, GET /me, etc.
│   ├── schemas.py         # LoginRequest, AccessRole enum
│   └── security.py        # hash_password, JWT create/verify
├── users/
│   ├── repository.py      # DB queries: get_user_by_email, insert_user
│   ├── router.py          # PUT /users/me
│   └── (no models.py)     # User data stored as MongoDB document dict
├── competencies/
│   ├── models.py          # Domain, EvidenceType (SELF_ASSESSMENT, KNOWLEDGE_TEST, SCENARIO_TEST, TRAINING, QUIZ)
│   ├── schemas.py         # CompetencyResponse, CompetencyProfile, CompetencyEvidence
│   ├── repository.py      # Competency CRUD
│   ├── service.py         # Competency logic
│   └── router.py          # GET /competencies, etc.
├── assessments/
│   ├── models.py          # (empty - no ORM models)
│   ├── schemas.py         # AssessmentType(INITIAL_COMPETENCY), QuestionType(SELF_RATING, MCQ, SCENARIO)
│   ├── repository.py      # get_assessment, insert_attempt, submit_attempt, upsert_profile, insert_evidence
│   ├── service.py         # start_assessment, submit_assessment, scoring logic
│   ├── scoring.py         # score_ratio, weighted_competency_score, prototype_confidence
│   ├── seed.py            # Seeded assessment: initial-competency-v1
│   └── router.py          # POST /assessments, POST /{attempt_id}/submit
├── quizzes/               # NEW (Phase 7) — DO NOT MODIFY
│   ├── models.py          # Quiz, QuizAttempt
│   ├── schemas.py         # QuizCreateRequest, QuizResponse
│   ├── repository.py      # Quiz CRUD
│   ├── service.py         # Quiz business logic
│   └── router.py          # POST /quizzes, GET /{id}, POST /{id}/submit
├── roles/
│   ├── repository.py      # Role CRUD
│   ├── router.py          # GET /roles
│   └── schemas.py         # RoleResponse
├── skill_gaps/
│   ├── engine.py          # calculate_gap, categorize_gap, build_gap_item
│   ├── repository.py      # get_role_requirements_with_competencies, get_user_competency_profiles
│   ├── service.py         # calculate_skill_gaps
│   ├── router.py          # GET /skill-gaps/me
│   └── schemas.py         # SkillGapCompetency, SkillGapResponse
├── ai/                    # Phase 6 AI/RAG
│   ├── providers/         # LLM providers (Mock, Gemini)
│   ├── embeddings/        # Embedding providers (Mock, Gemini)
│   ├── generation.py      # MCQGenerator class
│   ├── retrieval.py       # RetrieverService, VectorStore
│   ├── schemas.py         # GeneratedMCQ, GenerationRequest
│   ├── router.py          # POST /materials/upload, POST /{material_id}/generate-questions
│   └── (document processing)
└── api/
    └── health.py          # GET /health

tests/
├── test_assessment_api.py
├── test_assessment_scoring.py
├── test_auth.py
├── test_framework_api.py
├── test_health.py
├── test_skill_gaps_api.py
├── test_skill_gaps_engine.py
├── (+ more)
```

### 2.2 Router Registration

`app/main.py` currently registers:
- health_router
- auth_router
- assessments_router
- competencies_router
- **quizzes_router** (Phase 7 - newly added)
- roles_router
- skill_gaps_router
- users_router
- ai_router

---

## 3. DATABASE STRUCTURE

### 3.1 Collections

| Collection | Purpose | Indexed Fields | Status |
|-----------|---------|----------------|--------|
| `users` | Employee profiles | `_id`, `email` | Active |
| `roles` | Role taxonomy | `_id`, `role_code` | Active |
| `competencies` | Competency taxonomy | `_id`, `code` | Active |
| `competency_frameworks` | Role→Competency requirements | `role_id`, `competency_id` | Active |
| `competency_profiles` | User's current competency levels | `user_id`, `competency_id` | Active |
| `competency_evidence` | Append-only evidence records | `user_id`, `competency_id`, `evidence_type` | Active |
| `assessments` | Assessment templates | `assessment_key` | Active (seed: initial-competency-v1) |
| `assessment_attempts` | User assessment submissions | `user_id`, `assessment_id` | Active |
| `quizzes` | Quiz instances (Phase 7) | `user_id`, `material_id` | **NEW** |
| `quiz_attempts` | Quiz submissions (Phase 7) | `quiz_id`, `user_id` | **NEW** |
| `learning_materials` | Uploaded documents | `user_id` | Active |
| `document_chunks` | Chunked document text | `material_id` | Active |
| `chunk_embeddings` | Vector embeddings | `material_id` | Active |

### 3.2 Key Documents

#### Competency Profile
```typescript
{
  _id: ObjectId,
  user_id: ObjectId,
  competency_id: ObjectId,
  current_level: 1-5,          // 1=Awareness...5=Expert
  confidence: 0-1,             // Evidence weight coverage
  last_assessed_at: Date,
  status: "active",
  created_at: Date,
  updated_at: Date
}
```

#### Evidence Record
```typescript
{
  _id: ObjectId,
  user_id: ObjectId,
  competency_id: ObjectId,
  evidence_type: "SELF_ASSESSMENT" | "KNOWLEDGE_TEST" | "SCENARIO_TEST" | "TRAINING" | "QUIZ",
  score: 0-5,                  // Numeric competency level
  weight: 0-1,                 // Importance in aggregation
  source: "initial_assessment" | "AI_QUIZ" | "training",
  assessment_id: ObjectId,     // Links to assessment
  metadata: { ... },
  created_at: Date
}
```

#### Assessment (Seed Data)
```typescript
{
  _id: ObjectId,
  assessment_key: "initial-competency-v1",
  assessment_type: "INITIAL_COMPETENCY",
  title: "Initial Competency Assessment",
  questions: [
    {
      question_id: "...",
      competency_id: ObjectId,
      question_type: "SELF_RATING" | "MCQ" | "SCENARIO",
      question_text: "...",
      options: ["..."],
      correct_answer: "A",
      scenario_context: "...",
      difficulty: "EASY" | "MEDIUM" | "HARD",
      weight: 1.0
    }
  ],
  status: "active",
  version: 1
}
```

---

## 4. AUTHENTICATION

### 4.1 Current Implementation

**Location:** `app/auth/`

**Flow:**
```
POST /api/v1/auth/login
  ├─ Validate email/password
  ├─ Hash check
  ├─ Create JWT (HS256)
  └─ Return access_token

GET /api/v1/auth/me
  ├─ JWT decode (get_current_user dependency)
  └─ Return user info
```

**JWT Payload:**
```json
{
  "sub": "user_id",
  "aud": "ShikshaSetu",
  "exp": ...,
  "iat": ...
}
```

**Environment:** JWT_SECRET, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES

### 4.2 Authorization

**Pattern:** `Depends(get_current_user)` extracts user_id from JWT, then validates resource ownership at the repository/service layer.

**Example:** Can't retrieve another user's quiz; can't submit another user's assessment.

---

## 5. EXISTING ASSESSMENT SYSTEM

### 5.1 Initial Competency Assessment

**Status:** Fully implemented and tested (Phase 4)

**Current Flow:**
```
POST /api/v1/assessments
  → Start assessment attempt
  → Load seeded questions
  → Return (without answers)

GET /api/v1/assessments/{attempt_id}
  → Retrieve attempt (answers hidden)

POST /api/v1/assessments/{attempt_id}/submit
  → Validate answers
  → Score: self-rating + MCQ + scenario
  → Calculate competency (weighted)
  → Create evidence records (append-only)
  → Upsert competency profile
  → Return results
```

**Scoring Config:**
- Self Assessment: 20%
- Knowledge Test (MCQ): 40%
- Scenario Test: 30%
- Training Evidence: 10%

**Formula (see `scoring.py`):**
```python
score_ratio(percentage) → maps 0-1 to 1-5 level
  0-19%   → 1
  20-39%  → 2
  40-59%  → 3
  60-79%  → 4
  80-100% → 5

weighted_competency_score(components, config)
  → Sums (score × weight) for available components
  → Renormalizes weights if some components missing

prototype_confidence(components, config)
  → Sum of weights for available evidence
```

**Evidence Creation:**
```python
For each competency:
  For each component (self_assessment, knowledge_test, etc.):
    Insert into competency_evidence collection
    → evidence_type: maps component to enum
    → score: normalized 1-5 value
    → weight: config weight
    → source: "initial_assessment"
```

**Competency Profile Update:**
```python
upsert_profile(user_id, competency_id, update_dict)
  → MongoDB upsert (creates if not exists)
  → Sets current_level, confidence, last_assessed_at
```

### 5.2 Seeded Assessment Data

**File:** `app/assessments/seed.py`

**Competencies Covered:** 8 prototype competencies
- TECH_SQL
- TECH_PYTHON
- TECH_R
- STAT_SAMPLING
- STAT_SURVEY
- and others

**Questions:**
- SELF_RATING questions (employee self-assesses 1-5)
- MCQ questions (multiple choice with correct answer)
- SCENARIO questions (text-based scenario with multiple choice)

---

## 6. SKILL GAP ENGINE

### 6.1 Current Implementation

**Location:** `app/skill_gaps/`

**Flow:**
```
GET /api/v1/skill-gaps/me
  ├─ Get user's role
  ├─ Get role's required competencies
  ├─ Get user's current competency profiles
  ├─ For each role requirement:
  │   ├─ required_level = from framework
  │   ├─ current_level = from profile (or default 2.5)
  │   ├─ gap = max(0, required - current)
  │   ├─ priority = compute from gap + importance
  │   └─ Return SkillGapCompetency
  └─ Return sorted by priority
```

**Priority Calculation (see `engine.py`):**
```python
priority_score = (gap² × importance) + (base_priority / required_level)
```

**Categorization:**
```
gap ≤ 0.5   → "No Gap"
gap ≤ 1.5   → "Low Priority"
gap ≤ 2.5   → "Medium Priority"
gap > 2.5   → "High Priority"
```

---

## 7. EXISTING AI/GEMINI (PHASE 6)

### 7.1 LLM Provider

**Status:** Live Gemini verified (not mocked)

**Location:** `app/ai/providers/gemini_provider.py`

**Configuration:**
```python
- API Key: from .env (GEMINI_API_KEY)
- Model: models/gemini-3.6-flash
- Methods:
  - generate(prompt, max_tokens, temperature) → text
  - generate_json(prompt) → dict (if available)
```

**Factory Pattern:**
```python
get_llm_provider() → GeminiProvider or MockProvider
```

### 7.2 Embedding Provider

**Status:** Live Gemini verified

**Location:** `app/ai/embeddings/gemini_provider.py`

**Configuration:**
```python
- Model: models/gemini-embedding-001
- Dimensionality: 3072
- Methods:
  - embed_text(text) → Vector[3072]
```

### 7.3 MCQ Generation

**Location:** `app/ai/generation.py`

**Class:** MCQGenerator

**Process:**
```
Retrieve chunks (vector similarity)
  ↓
Format context
  ↓
Prompt LLM for MCQs
  ↓
Parse JSON response
  ↓
Validate (Pydantic GeneratedMCQ)
  ↓
Return grounded questions
```

**GeneratedMCQ Schema:**
```typescript
{
  question: string,
  options: [string, string, string, string],
  correct_answer: "A" | "B" | "C" | "D",
  explanation: string,
  difficulty: "EASY" | "MEDIUM" | "HARD",
  source_chunks: [string]  // Chunk IDs for traceability
}
```

---

## 8. QUIZ ENGINE (PHASE 7)

### 8.1 Status: Implemented ✅

**Location:** `app/quizzes/`

**Current Endpoints:**
- `POST /api/v1/quizzes` → Create quiz from MCQs
- `GET /api/v1/quizzes/{quiz_id}` → Retrieve (answers hidden)
- `POST /api/v1/quizzes/{quiz_id}/submit` → Submit & score

**Scoring:** Server-side deterministic (client score ignored)

**Competency Update (Quiz):** Deterministic formula (80%+ → level 4.5 with confidence 0.9)

**Evidence:** Creates append-only QUIZ evidence, linked to attempt

**Test Status:** 103/103 regression passing

---

## 9. TESTING

### 9.1 Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Auth | 10+ | ✅ PASSING |
| Assessments | 15+ | ✅ PASSING |
| Competencies | 10+ | ✅ PASSING |
| Skill Gaps | 12+ | ✅ PASSING |
| AI/Gemini | 20+ | ✅ PASSING |
| Quiz Engine | (Regression) | ✅ 103/103 PASSING |

**Command:** `pytest tests/ -v`

**Baseline:** 103/103 tests passing

---

## 10. EXISTING PROBLEMS / GAPS

### 10.1 Known Limitations

1. **No Configurable Assessment Types**
   - Current: Hard-coded INITIAL_COMPETENCY assessment
   - Missing: Ability to define MCQ-only, CODING, SQL, SCENARIO-only assessments per competency
   - Impact: Cannot build competency-specific assessments

2. **No Assessment Configuration Per Competency**
   - All competencies use the same assessment template
   - Missing: Mapping like "Python should have MCQ + CODING", "SQL should have MCQ + SQL"
   - Impact: Cannot offer targeted assessments

3. **No Coding Execution Infrastructure**
   - Missing: Sandboxed Python/R/SQL execution
   - Risk: Cannot evaluate coding questions safely
   - Current state: No coding assessment type defined

4. **No SQL Execution Sandbox**
   - Missing: Safe SQL query evaluation
   - Risk: Would need sandboxed database copy or SELECT-only API
   - Current state: Not implemented

5. **No iGOT/NSSTA Integration**
   - Missing: Resource mapping, live APIs
   - Current state: Not in scope for Capability Assessment phase

6. **No Recommendation Engine**
   - Missing: Skill gap → Learning resource matching
   - Current state: Not in scope for Capability Assessment phase

---

## 11. WHAT CAN BE REUSED

### 11.1 Existing Infrastructure (DO NOT DUPLICATE)

| Component | Reuse Strategy |
|-----------|----------------|
| Authentication | Reuse get_current_user dependency; user_id extraction |
| Database | Reuse MongoDB connection, repository patterns |
| Evidence system | Extend: add new EvidenceType values; use existing insert_evidence |
| Competency models | Reuse: Domain enum, EvidenceType enum, CompetencyProfile schema |
| Assessment patterns | Extend: assessment creation, questions, attempt tracking |
| Scoring | Can adapt weighted_competency_score formula |
| Skill gap engine | Unchanged — depends on competency profiles |
| Error handling | Follow existing HTTPException patterns |
| Routers | Follow existing router structure: Annotated[dict, Depends()] patterns |

---

## 12. WHAT NEEDS TO BE EXTENDED

### 12.1 Capability Assessment Enhancements

| Item | Current | Needed |
|------|---------|--------|
| Assessment Types | 1 (INITIAL_COMPETENCY) | N (MCQ, CODING, SQL, SCENARIO, SITUATIONAL) |
| Question Types | 3 (SELF_RATING, MCQ, SCENARIO) | Extended: CODING, SQL, SITUATIONAL_JUDGEMENT |
| Assessment Config | Hard-coded | Per-competency configuration |
| Scoring Rules | Weighted (existing) | Question type-specific (MCQ=binary, CODING=rubric) |
| Evidence Types | 5 (existing) | No new types needed; extend usage |
| Competency Update | Simple upsert | Keep simple; extend evidence→profile logic |

---

## 13. PROPOSED ARCHITECTURE

### 13.1 High-Level Design

```
Capability Assessment Engine
├─ Assessment Configuration Service
│  └─ Manages: which question types per competency
├─ Assessment Generation Service
│  └─ Creates: assessment instances for employee + competency
├─ Question Management
│  ├─ Question Types: MCQ, CODING, SQL, SCENARIO, SITUATIONAL
│  └─ Question Storage: MongoDB
├─ Scoring Engine
│  ├─ MCQ: Binary (correct/incorrect)
│  ├─ CODING: Rubric-based evaluation
│  ├─ SQL: Query validation + rubric
│  ├─ SCENARIO: Rubric-based
│  └─ SITUATIONAL: Predefined rubric
├─ Competency Calculation
│  └─ Evidence aggregation (reuse existing weights)
└─ Evidence & Traceability
   └─ Append-only (reuse existing)
```

### 13.2 Data Model Additions

**AssessmentConfiguration Collection:**
```typescript
{
  _id: ObjectId,
  competency_id: ObjectId,
  assessment_types: ["MCQ", "SCENARIO"],    // New field
  number_of_questions: 10,
  difficulty: "MIXED",
  passing_threshold: 60,
  scoring_method: "percentage",             // New field
  created_at: Date
}
```

**New Question Types:**
```typescript
CODING {
  programming_language: "Python" | "R",
  test_cases: [{input, expected_output}],
  rubric: [{criterion, points}]
}

SQL {
  query_template: string,
  test_data: [{setup SQL}],
  expected_results: [[rows]],
  rubric: [{criterion, points}]
}

SITUATIONAL_JUDGEMENT {
  situation: string,
  response_options: [{option, score_delta}]
}
```

---

## 14. DATABASE CHANGES NEEDED

### 14.1 New Collections

```
assessment_configurations
├─ competency_id
├─ assessment_types
├─ difficulty
├─ scoring_method
└─ metadata

question_bank
├─ question_type
├─ competency_id
├─ content (MCQ, CODING, SQL, SCENARIO, SITUATIONAL)
└─ metadata
```

### 14.2 Indexes

```
assessment_configurations:
  - competency_id

question_bank:
  - competency_id
  - question_type
  - (competency_id, question_type)
```

---

## 15. API ENDPOINTS PROPOSED

### 15.1 Capability Assessment Endpoints

```
POST   /api/v1/assessments
       Create assessment for competency
       Body: {competency_code, assessment_type?}

GET    /api/v1/assessments/{assessment_id}
       Retrieve assessment (answers hidden)

POST   /api/v1/assessments/{assessment_id}/start
       Start/resume assessment attempt

POST   /api/v1/assessments/{assessment_id}/submit
       Submit answers, score, update competency

GET    /api/v1/assessments/{assessment_id}/results
       Get results after submission
```

### 15.2 Configuration Endpoints (Admin/Backend)

```
POST   /api/v1/admin/assessment-configs
       Define which assessment types per competency

GET    /api/v1/admin/assessment-configs/{competency_id}
       Retrieve config for competency
```

---

## 16. SECURITY CONSIDERATIONS

### 16.1 Inherited Security (No Changes Needed)

- JWT authentication: Reuse existing `get_current_user`
- User ownership validation: Already in patterns
- Input validation: Use Pydantic schemas

### 16.2 New Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| Answer key protection | Repository/service layer; don't expose via API |
| Coding execution sandbox | Use restricted execution environment (not implemented here) |
| SQL execution sandbox | Use read-only DB connection or query validator |
| Duplicate submission prevention | Check attempt status before scoring |
| Tamper-proof scoring | Server-side only (no client scores) |

---

## 17. TESTING STRATEGY

### 17.1 Test Categories

**Unit Tests:**
- Assessment creation
- Question validation
- Scoring calculations
- Evidence generation
- Competency update

**Integration Tests:**
- End-to-end assessment flow
- Database interactions
- JWT authentication
- Competency profile updates

**Regression Tests:**
- All 103 existing tests must still pass
- No breaking changes to existing APIs

---

## 18. RISK ASSESSMENT

### 18.1 High Risk Items

| Risk | Mitigation |
|------|-----------|
| Breaking existing assessment API | Extend carefully; preserve existing endpoints |
| Unsafe code execution | Don't implement without isolated sandbox |
| Evidence corruption | Append-only; no deletions |
| Competency overwrite | Use same upsert pattern; preserve history |

### 18.2 Medium Risk Items

| Risk | Mitigation |
|------|-----------|
| Complexity explosion | Start with MCQ + SCENARIO only; add others later |
| Configuration explosion | Minimal config per competency; sensible defaults |

---

## 19. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (2-3 hours)
- [ ] Create assessment_configuration collection + indexes
- [ ] Create assessment configuration schemas (Pydantic)
- [ ] Create configuration repository CRUD
- [ ] Create configuration service

### Phase 2: Question Bank (2 hours)
- [ ] Extend question types (enums + schemas)
- [ ] Create question_bank collection
- [ ] Create question repository CRUD

### Phase 3: Assessment Flow (3 hours)
- [ ] Extend assessment creation to use configurations
- [ ] Implement assessment selection per competency
- [ ] Implement question loading per assessment type

### Phase 4: Scoring (2-3 hours)
- [ ] Implement type-specific scoring (MCQ, SCENARIO, etc.)
- [ ] Extend weighted_competency_score for new evidence types
- [ ] Evidence creation per question type

### Phase 5: APIs (2 hours)
- [ ] Create assessment endpoints
- [ ] Create configuration endpoints (admin)
- [ ] Add error handling

### Phase 6: Testing (2 hours)
- [ ] Write unit tests for each component
- [ ] Write integration tests
- [ ] Verify regression: 103/103 must still pass

### Phase 7: Documentation (1 hour)
- [ ] API contract documentation
- [ ] Database schema documentation
- [ ] Configuration guide

**Estimated Total:** 14-16 hours

---

## 20. DECISION POINTS FOR DISCUSSION

### 20.1 Scope Questions

1. **For Round 1, which assessment types to implement?**
   - Minimal: MCQ + SCENARIO (build on existing)
   - Mid: + CODING (requires execution sandbox)
   - Full: + SQL + SITUATIONAL

2. **Coding Execution:**
   - Do we have a Python/R sandbox available? (Answer: NO)
   - Should we defer coding assessments? (Recommended: YES for Round 1)

3. **SQL Execution:**
   - Do we have a test database? (Answer: Unclear)
   - Can we use read-only queries? (Recommend: YES)
   - Or defer SQL assessments? (Recommended: YES for Round 1)

4. **Assessment Configuration:**
   - Hard-code per competency? (Simple but inflexible)
   - Admin API to configure? (More flexible but more code)
   - Seed data approach? (Balanced; recommend: START HERE)

### 20.2 Integration Questions

1. **Competency Update:**
   - Same formula as current assessment? (Recommend: YES)
   - Or different per assessment type? (NO for Round 1)

2. **Evidence Aggregation:**
   - INITIAL_COMPETENCY evidence + CAPABILITY_ASSESSMENT evidence together? (YES)
   - Same weights? (Recommend: YES for Round 1)

3. **Skill Gap Recalculation:**
   - Automatic after competency update? (YES, Phase 5 engine does it)
   - No changes needed to Phase 5? (Correct)

4. **Quiz Engine Integration:**
   - Should Quiz Evidence be different from Capability Assessment Evidence? (YES—already is via evidence_type)
   - Should they use same competency update logic? (NO—each has own formula)

---

## 21. FINAL RECOMMENDATION

### 21.1 Approach

**START SIMPLE:**

1. **Extend** the existing assessment system to support **assessment_configurations**
2. Implement **MCQ + SCENARIO** question types per competency (build on existing)
3. **DEFER** CODING, SQL, SITUATIONAL_JUDGEMENT to later phases
4. Use **seed data** or simple **admin endpoints** to define configurations
5. **Reuse** all existing patterns: evidence, competency, skill gaps

### 21.2 Why This Works

- ✅ Minimal new code (extend, don't rebuild)
- ✅ No breaking changes (preserve Phase 4 & 7 assessments)
- ✅ Builds on proven patterns
- ✅ Can assess most competencies adequately with MCQ + scenario
- ✅ Leaves room for advanced types in future phases
- ✅ Meets Round 1 goal: "Assess what employee knows"

### 21.3 Out of Scope for Capability Assessment Phase

- Coding execution / CODING question type
- SQL execution / SQL question type  
- Situational Judgement type (deferrable)
- Recommendation engine (Phase 7)
- iGOT/NSSTA integration (Phase 7)
- Frontend (Sanika owns)

---

## 22. MIGRATION PATH IF DISCOVERED ISSUES

If during implementation we discover:

1. **Coding execution is unsafe** → Document limitation, skip CODING type
2. **Existing assessment conflicts** → Extend carefully, preserve backward compatibility
3. **Configuration complexity grows** → Implement admin API incrementally
4. **Competency aggregation formula needs change** → Propose formula with justification

---

## CONCLUSION

### ✅ Recommended Action

Proceed with **Phase 1 implementation** using:

1. **Extend** existing assessment system
2. **Implement** MCQ + SCENARIO capability assessments
3. **Reuse** authentication, database, evidence, competency patterns
4. **Maintain** 103/103 regression passing
5. **Document** APIs and configuration

**No architectural change required** — this is an extension of Phase 4 assessment system, not a replacement.

Next step: **PHASE 1 IMPLEMENTATION** (Assessment Configuration Foundation)

---

**End of Audit**

*Prepared by Kiro Agent*  
*Date: August 27, 2026*  
*Status: Ready for Phase 1 Implementation*
