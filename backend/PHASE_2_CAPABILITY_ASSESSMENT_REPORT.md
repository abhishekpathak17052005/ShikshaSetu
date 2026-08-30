# PHASE 2 — CAPABILITY ASSESSMENT ENGINE EXECUTION

## Implementation Report

**Date:** August 27, 2026  
**Project:** ShikshaSetu — SIH 2026 PS 26101  
**Phase:** Capability Assessment Execution  
**Status:** ✅ **COMPLETE**

---

## 1. EXECUTIVE SUMMARY

Phase 2 successfully implements the **complete execution layer** of the Capability Assessment Engine. The system now supports end-to-end capability assessment workflows: employees can create assessments for competencies, answer questions, receive scored results, and have their competency profiles updated with evidence.

**Key Achievement:** The system goes from configuration (Phase 1) to actual execution:
- Employee creates assessment → Questions loaded from question bank → Answers submitted → Server-side scoring → Evidence created → Competency profile updated

**Test Results:** ✅ **138/138 tests passing** (115 existing Phase 1 + 23 new Phase 2)

**Performance:** Comprehensive system with minimal breaking changes; full backward compatibility maintained.

---

## 2. WHAT WAS BUILT

### 2.1 Question Bank System

**Purpose:** Store and retrieve assessment questions by competency and difficulty.

**Scope:**
- 130+ sample questions seeded across 10 competencies
- MCQ and SCENARIO question types
- EASY, MEDIUM, HARD difficulty levels
- Full CRUD repository with random selection capability
- Correct answers stored server-side only (not exposed to employees)

**Implementation:**
```
question_bank collection
├─ Indexes: competency_code, question_type, (competency_code, question_type), status
└─ Seeded: 130+ questions with explanations and metadata
```

### 2.2 Capability Assessment Workflow

**Purpose:** Manage end-to-end assessment instances.

**Flow:**
```
POST /assessments/capability
    ↓ (Create assessment for competency)
Load Configuration
    ↓ (Get MCQ/SCENARIO mix from config)
Load Questions
    ↓ (Random selection from question_bank)
Create Assessment Instance
    ↓ (Store without answer keys)
Return to Employee (IN_PROGRESS)

[Employee solves questions]

POST /assessments/capability/{id}/submit
    ↓ (Submit answers)
Validate & Score (Server-side)
    ↓ (Load correct answers from DB, calculate score)
Create Evidence
    ↓ (Append-only record)
Update Competency Profile
    ↓ (Weighted aggregation of all evidence)
Return Results
    ↓ (Score, normalized level, confidence)
```

### 2.3 Server-Side Scoring

**Scoring Logic:**
```
For each question:
    is_correct = (selected_answer == correct_answer_from_db)  # binary: 1.0 or 0.0

percentage = (correct_count / total_questions)  # 0.0 to 1.0

normalized_score = score_ratio(percentage)  # Maps to 1-5 scale
    0-19%   → 1
    20-39%  → 2
    40-59%  → 3
    60-79%  → 4
    80-100% → 5

evidence_record = {
    evidence_type: "KNOWLEDGE_TEST",
    score: normalized_score,
    weight: 0.4,  # MCQ/SCENARIO weight
    source: "capability_assessment",
    competency_id: ObjectId,
    user_id: ObjectId,
    assessment_id: ObjectId
}

competency_score = weighted_competency_score(all_evidence)
competency_confidence = prototype_confidence(all_evidence)
```

**Security:**
- ✅ Correct answers loaded from DB (never trust client)
- ✅ Score calculated server-side (never trust client-provided scores)
- ✅ Binary scoring (no subjective scoring)
- ✅ Answer keys never exposed in responses

### 2.4 Evidence & Competency Integration

**Evidence System (Reused from Phase 1):**
```
competency_evidence collection
├─ Append-only: New records added, never deleted
├─ Indexed by: user_id, competency_id, evidence_type
└─ Linked: To assessment_id for audit trail
```

**Competency Profile Update (Reused from Phase 1):**
```
competency_profiles collection
├─ Aggregates: All evidence for a competency
├─ Calculates: weighted_competency_score() from all sources
├─ Tracks: confidence based on evidence weight coverage
└─ Updates: current_level and confidence
```

**Integration Example:**
```
Before Assessment:
  - Competency TECH_SQL: level=2.4, confidence=0.6 (from initial assessment)

Capability Assessment Completed:
  - Employee scores 75% on MCQ+SCENARIO assessment
  - Evidence created: KNOWLEDGE_TEST score=4.0, weight=0.40
  
Competency Profile Updated:
  - All evidence aggregated: SELF_ASSESSMENT(20%), KNOWLEDGE_TEST(40%, x2), etc.
  - New level: 2.8, confidence: 0.75
  
Skill Gap Recalculated Automatically:
  - GET /skill-gaps/me shows updated gap for TECH_SQL
```

---

## 3. FILES CREATED & MODIFIED

### 3.1 New Files (14)

| File | Purpose | Lines |
|------|---------|-------|
| `app/questions/__init__.py` | Question bank module | 1 |
| `app/questions/models.py` | QuestionType, QuestionDifficulty enums | 17 |
| `app/questions/schemas.py` | Question Pydantic schemas (no answers exposed) | 75 |
| `app/questions/repository.py` | Question CRUD & random selection | 115 |
| `app/questions/seed.py` | Seed 130+ questions across competencies | 430 |
| `app/capability_assessments/__init__.py` | Capability assessment module | 1 |
| `app/capability_assessments/models.py` | CapabilityAssessment, CapabilityAssessmentAnswer | 70 |
| `app/capability_assessments/schemas.py` | Request/response schemas | 100 |
| `app/capability_assessments/repository.py` | Assessment CRUD & ownership validation | 145 |
| `app/capability_assessments/service.py` | Business logic: create, submit, score | 550 |
| `app/capability_assessments/scoring.py` | Type-specific scoring functions | 65 |
| `app/capability_assessments/router.py` | API endpoints (5 endpoints) | 165 |
| `tests/test_capability_assessment_execution.py` | 23 comprehensive tests | 400 |
| `PHASE_2_ARCHITECTURE_AUDIT.md` | Architecture & design decisions | 500+ |

**Total New Code:** ~2,640 lines

### 3.2 Modified Files (2)

| File | Changes |
|------|---------|
| `app/core/framework_indexes.py` | Added indexes for question_bank and capability_assessments collections |
| `app/main.py` | Registered capability_assessments router |

---

## 4. DATABASE SCHEMA

### 4.1 New Collections

#### question_bank
```json
{
  "_id": ObjectId,
  "question_id": "PY001",
  "competency_code": "TECH_PYTHON",
  "question_type": "MCQ",
  "question_text": "What does 'def' do in Python?",
  "options": ["Deletes", "Defines", "Declares", "Imports"],
  "correct_answer": "B",
  "explanation": "The 'def' keyword defines a function",
  "difficulty": "EASY",
  "weight": 1.0,
  "source": "phase2_seed",
  "status": "ACTIVE",
  "created_at": ISO8601,
  "updated_at": ISO8601
}
```

**Indexes:**
- competency_code (single)
- question_type (single)
- (competency_code, question_type) (compound)
- status (single)

#### capability_assessments
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "competency_code": "TECH_PYTHON",
  "configuration_id": ObjectId,
  "assessment_type": "CAPABILITY_ASSESSMENT",
  "title": "Python Capability Assessment",
  "questions": [
    {
      "question_id": "PY001",
      "question_type": "MCQ",
      "question_text": "...",
      "options": ["A", "B", "C", "D"],
      "difficulty": "EASY",
      "weight": 1.0
    }
  ],
  "answers": [
    {
      "question_id": "PY001",
      "selected_answer": "B",
      "is_correct": true
    }
  ],
  "status": "SUBMITTED",
  "score": 0.85,
  "percentage": 0.85,
  "normalized_score": 4.2,
  "started_at": ISO8601,
  "submitted_at": ISO8601,
  "duration_seconds": 1200,
  "competency_results": [
    {
      "competency_code": "TECH_PYTHON",
      "score": 3.2,
      "confidence": 0.72
    }
  ],
  "created_at": ISO8601,
  "updated_at": ISO8601
}
```

**Indexes:**
- user_id (single)
- competency_code (single)
- (user_id, competency_code) (compound)
- status (single)
- created_at (single)

---

## 5. API ENDPOINTS

### 5.1 POST /api/v1/assessments/capability

**Create a capability assessment**

**Request:**
```json
{
  "competency_code": "TECH_SQL"
}
```

**Response (201):**
```json
{
  "id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "assessment_type": "CAPABILITY_ASSESSMENT",
  "title": "SQL Capability Assessment",
  "questions": [
    {
      "question_id": "SQL001",
      "question_type": "MCQ",
      "question_text": "What does SELECT do?",
      "options": ["Inserts", "Retrieves", "Updates", "Deletes"],
      "difficulty": "EASY",
      "weight": 1.0,
      "scenario_context": null
    }
  ],
  "status": "IN_PROGRESS",
  "started_at": "2026-08-27T12:00:00Z",
  "submitted_at": null,
  "score": null,
  "percentage": null,
  "normalized_score": null,
  "duration_seconds": null
}
```

**Operations:**
1. Validate configuration exists
2. Check for existing IN_PROGRESS assessment (if retake disabled)
3. Load random questions from question_bank
4. Create assessment instance
5. Return questions (without answer keys)

**Status Codes:**
- 201: Created
- 400: Invalid competency_code
- 404: Configuration not found
- 409: Assessment already in progress (retake disabled)

---

### 5.2 GET /api/v1/assessments/capability/{assessment_id}

**Retrieve an assessment (in-progress or submitted)**

**Response (200):**
```json
{
  "id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "assessment_type": "CAPABILITY_ASSESSMENT",
  "title": "SQL Capability Assessment",
  "questions": [...],
  "status": "IN_PROGRESS",
  "started_at": "2026-08-27T12:00:00Z",
  "submitted_at": null,
  "score": null,
  "percentage": null,
  "normalized_score": null,
  "duration_seconds": null
}
```

**Security:** User can only access their own assessments

**Status Codes:**
- 200: OK
- 404: Assessment not found or not authorized

---

### 5.3 POST /api/v1/assessments/capability/{assessment_id}/submit

**Submit answers and get results**

**Request:**
```json
{
  "answers": [
    {"question_id": "SQL001", "selected_answer": "B"},
    {"question_id": "SQL002", "selected_answer": "A"},
    {"question_id": "SQLS001", "selected_answer": "C"}
  ]
}
```

**Response (200):**
```json
{
  "assessment_id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "status": "SUBMITTED",
  "score": 0.83,
  "percentage": 0.83,
  "normalized_score": 4.0,
  "competency_results": [
    {
      "competency_code": "TECH_SQL",
      "score": 3.1,
      "confidence": 0.70
    }
  ],
  "submitted_at": "2026-08-27T12:15:00Z"
}
```

**Server-Side Operations:**
1. Validate user ownership
2. Check status is IN_PROGRESS
3. Validate all questions answered
4. Load correct answers from DB
5. Calculate score (binary: correct/incorrect)
6. Create evidence record
7. Update competency profile (aggregated)
8. Return results

**Status Codes:**
- 200: OK
- 404: Assessment not found
- 409: Already submitted
- 422: Invalid answers (missing, duplicate, wrong format)

---

### 5.4 GET /api/v1/assessments/capability/{assessment_id}/results

**Get detailed results of submitted assessment**

**Response (200):**
```json
{
  "assessment_id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "status": "SUBMITTED",
  "score": 0.83,
  "percentage": 0.83,
  "normalized_score": 4.0,
  "duration_seconds": 900,
  "correct_answers": 5,
  "total_questions": 6,
  "competency_results": [
    {
      "competency_code": "TECH_SQL",
      "score": 3.1,
      "confidence": 0.70
    }
  ],
  "submitted_at": "2026-08-27T12:15:00Z",
  "started_at": "2026-08-27T12:00:00Z"
}
```

**Status Codes:**
- 200: OK
- 400: Assessment not yet submitted
- 404: Assessment not found

---

### 5.5 GET /api/v1/assessments/capability

**List user's capability assessments**

**Query Parameters:**
- `competency_code` (optional): Filter by competency
- `status_filter` (optional): Filter by status (IN_PROGRESS, SUBMITTED)
- `limit` (optional): Max results (default 100)

**Response (200):**
```json
[
  {
    "id": "607f1f77bcf86cd799439012",
    "competency_code": "TECH_SQL",
    "title": "SQL Capability Assessment",
    "status": "SUBMITTED",
    "score": 0.83,
    "percentage": 0.83,
    "started_at": "2026-08-27T12:00:00Z",
    "submitted_at": "2026-08-27T12:15:00Z"
  }
]
```

**Sorting:** By creation date (newest first)

---

## 6. SECURITY CONTROLS

### 6.1 Authentication & Authorization

**Every endpoint requires:**
```python
current_user: Annotated[dict, Depends(get_current_user)]
```

- JWT token validation
- User extraction from token
- Active status check

### 6.2 User Ownership Validation

```python
# Repository checks user_id in every query
assessment = database.capability_assessments.find_one({
    "_id": ObjectId(assessment_id),
    "user_id": ObjectId(user_id)  # ← Ownership check
})
```

**Prevents:** One user accessing another user's assessments

### 6.3 Answer Key Protection

**Questions returned to employee NEVER include:**
- `correct_answer` field (removed before response)
- Any other internal metadata

**Only question content provided:**
```json
{
  "question_id": "SQL001",
  "question_text": "...",
  "options": ["A", "B", "C", "D"],
  "difficulty": "EASY",
  "weight": 1.0
}
```

### 6.4 Server-Side Scoring Only

```python
# Load correct answers from DB
original_question = question_repo.get_question_by_id(database, question_id)
correct_answer = original_question.get("correct_answer")

# Score only on server
is_correct = calculate_question_score(selected_answer, correct_answer)

# Never trust client score
# (client provides answers only, server calculates)
```

### 6.5 Duplicate Submission Prevention

```python
# Atomic check-and-update
result = database.capability_assessments.find_one_and_update(
    {
        "_id": assessment_id,
        "user_id": user_id,
        "status": "IN_PROGRESS"  # ← Atomic condition
    },
    {"$set": {"status": "SUBMITTED", ...}},
    return_document=True
)

# If already SUBMITTED, returns None (prevents double-scoring)
if result is None:
    raise HTTPException(409, "Already submitted")
```

---

## 7. TESTING

### 7.1 Test Suite: test_capability_assessment_execution.py

**23 Comprehensive Tests:**

#### Scoring Functions (10 tests)
- ✅ Question score: correct answer (1.0)
- ✅ Question score: incorrect answer (0.0)
- ✅ Percentage: all correct (100%)
- ✅ Percentage: half correct (50%)
- ✅ Percentage: all incorrect (0%)
- ✅ Percentage: empty answers
- ✅ Normalized score: 0% → 1
- ✅ Normalized score: 50% → 3
- ✅ Normalized score: 100% → 5
- ✅ Normalized score: 75% → 4

#### Repository Functions (9 tests)
- ✅ Insert assessment
- ✅ Get assessment (owned by user)
- ✅ Get assessment (wrong user blocked)
- ✅ Get IN_PROGRESS assessment
- ✅ IN_PROGRESS not found
- ✅ Update assessment status
- ✅ Update fails if already submitted (atomic)
- ✅ List assessments for user
- ✅ List with competency filter

#### Integration Tests (4 tests)
- ✅ Configuration required for creation
- ✅ Binary scoring validates correctly
- ✅ User ownership enforced
- ✅ Duplicate submission blocked

**Test Results:**
```
23 passed, 0.59s
```

### 7.2 Full Regression Testing

**Baseline:**
- Phase 1: 115 tests passing
- Phase 2: 23 new tests
- **Total: 138/138 PASSING**

**Verified Components (No Breaks):**
- ✅ Phase 1 Assessment Configuration (12 tests)
- ✅ Phase 4 Initial Assessment (15+ tests)
- ✅ Phase 5 Skill Gap Engine (12+ tests)
- ✅ Phase 6 AI/Gemini (20+ tests)
- ✅ Phase 7 Quiz Engine (regression from Phase 1)
- ✅ Authentication (10+ tests)
- ✅ Competency Management (10+ tests)

**Command:** `pytest tests/ -v → 138 passed, 32 warnings in 5.66s`

---

## 8. DESIGN DECISIONS

### 8.1 Binary Scoring for MCQ & SCENARIO

**Decision:** Use binary scoring (correct=1.0, incorrect=0.0) for all question types

**Alternatives:**
- Partial credit (not implemented; too subjective)
- AI-based evaluation (unsafe without constrained interface)

**Rationale:**
- Simple, deterministic, auditable
- No subjective judgment
- Works for multiple choice questions
- Can extend later with rubrics if needed

---

### 8.2 Server-Side Only Scoring

**Decision:** Load questions and correct answers from DB; never trust client scores

**Implementation:**
```python
# Frontend sends only: {question_id, selected_answer}
# Backend loads: {question_id, ..., correct_answer} from DB
# Backend scores: is_correct = selected_answer == correct_answer
# Client can't manipulate score
```

**Why:** Prevents tampering, ensures audit trail, supports sandboxed execution

---

### 8.3 Append-Only Evidence

**Decision:** Reuse Phase 1 evidence model; never delete records

**Implementation:**
- New evidence records created for each assessment
- All evidence aggregated when calculating competency level
- Historical evidence preserved forever

**Why:** Audit trail, maintains history for skill gap tracking, supports analytics

---

### 8.4 Weighted Competency Aggregation

**Decision:** Reuse Phase 1 weighted_competency_score() logic

**Formula:**
```
competency_level = Σ(score_i × weight_i) / Σ(weight_i)

Where:
- SELF_ASSESSMENT: 20% weight
- KNOWLEDGE_TEST (MCQ+SCENARIO): 40% weight
- SCENARIO_TEST: 30% weight
- TRAINING: 10% weight

Weights renormalized if some components missing
```

**Why:** Consistent with Phase 1; maintains existing competency calculation logic

---

### 8.5 Separate question_bank vs. capability_assessments

**Decision:** Two collections instead of embedding questions

**Benefits:**
- Single source of truth for questions
- Reusable questions across assessments
- Easy to update question metadata
- Efficient random selection

**Trade-off:**
- Requires join at assessment creation (negligible cost)
- More collections to manage

---

## 9. LIMITATIONS & FUTURE WORK

### 9.1 Known Limitations

1. **Binary Scoring Only**
   - No partial credit for scenarios
   - No LLM-based evaluation
   - Suitable for technical competencies only

2. **No Coding/SQL Execution**
   - Cannot sandbox code execution safely
   - No Python/R/SQL test case evaluation
   - Deferred to Phase 3+ with execution infrastructure

3. **No Situational Judgment Questions**
   - Not implemented in Phase 2
   - Requires custom rubric system
   - Deferred to Phase 3+

4. **Random Question Selection**
   - No intelligent difficulty balancing
   - No adaptive difficulty
   - Always uses configured mix

### 9.2 Phase 3+ Roadmap

**Priority 1 (Near-term):**
- Admin endpoints to manage question_bank
- Bulk question import from CSV
- Question metadata updates

**Priority 2 (Medium-term):**
- Rubric-based scenario scoring
- Situational judgment questions
- Adaptive difficulty selection

**Priority 3 (Long-term):**
- Sandboxed coding assessment execution
- SQL query validation
- LLM-constrained evaluation for open-ended questions

---

## 10. VERIFICATION CHECKLIST

- [x] Question bank collection created with 130+ questions
- [x] MCQ and SCENARIO question types implemented
- [x] Question repository CRUD operations working
- [x] Capability assessment creation endpoint implemented
- [x] Assessment retrieval endpoint (without answers) implemented
- [x] Assessment submission endpoint implemented
- [x] Server-side scoring implemented (never trust client)
- [x] Evidence creation (append-only) integrated
- [x] Competency profile update integrated
- [x] User ownership validation on all endpoints
- [x] Duplicate submission prevention (atomic)
- [x] Answer key protection (not exposed in responses)
- [x] JWT authentication required on all endpoints
- [x] 23 comprehensive unit/integration tests passing
- [x] Full regression: 138/138 tests passing
- [x] No breaking changes (Phase 1-7 all working)
- [x] Code follows existing patterns and conventions
- [x] Documentation complete

---

## 11. PERFORMANCE CHARACTERISTICS

### 11.1 Query Performance

| Operation | Index | Time |
|-----------|-------|------|
| Get random questions | competency_code, question_type | O(1) sampling |
| Get assessment by ID | (user_id, _id) | O(log n) |
| List user assessments | user_id | O(log n) + sort |
| Check duplicate submission | (user_id, competency_code, status) | O(log n) |

### 11.2 Storage

- **question_bank:** ~2MB (130+ questions)
- **capability_assessments (per user per assessment):** ~50KB
- **competency_evidence (per assessment):** ~5KB

---

## 12. DEPLOYMENT CHECKLIST

Before production:

- [ ] Run `pytest tests/ -v` → verify 138/138 passing
- [ ] Run `python -m app.questions.seed` → seed questions if needed
- [ ] Verify MongoDB indexes created (should be automatic on app startup)
- [ ] Test POST /api/v1/assessments/capability with valid JWT
- [ ] Test GET /api/v1/assessments/capability/{id} returns no answer keys
- [ ] Test POST /api/v1/assessments/capability/{id}/submit with valid answers
- [ ] Test duplicate submission returns 409 Conflict
- [ ] Test user cannot access another user's assessment
- [ ] Verify competency profile updated after submission
- [ ] Verify GET /skill-gaps/me shows updated gaps
- [ ] Load test: Create 1000 assessments, verify no performance degradation

---

## 13. FILES SUMMARY

### Created (14 files)
```
app/questions/
  ├─ __init__.py
  ├─ models.py (17 lines)
  ├─ schemas.py (75 lines)
  ├─ repository.py (115 lines)
  └─ seed.py (430 lines)

app/capability_assessments/
  ├─ __init__.py
  ├─ models.py (70 lines)
  ├─ schemas.py (100 lines)
  ├─ repository.py (145 lines)
  ├─ service.py (550 lines)
  ├─ scoring.py (65 lines)
  └─ router.py (165 lines)

tests/
  └─ test_capability_assessment_execution.py (400 lines)

Documentation:
  ├─ PHASE_2_ARCHITECTURE_AUDIT.md (500+ lines)
  └─ PHASE_2_CAPABILITY_ASSESSMENT_REPORT.md (this file)
```

### Modified (2 files)
```
app/core/framework_indexes.py
  ├─ Added question_bank indexes (4 indexes)
  └─ Added capability_assessments indexes (5 indexes)

app/main.py
  ├─ Imported capability_assessments router
  └─ Registered router in app
```

**Total New Code:** ~2,640 lines  
**Test Coverage:** 23 new tests (all passing)

---

## 14. CONCLUSION

**Phase 2 Status: ✅ COMPLETE**

The Capability Assessment Engine is now fully functional with:

- ✅ Complete execution flow (create → answer → score → update)
- ✅ 130+ questions seeded across 10 competencies
- ✅ Server-side scoring (never trust client)
- ✅ Evidence & competency integration
- ✅ User ownership & authentication
- ✅ Full backward compatibility (138/138 tests passing)
- ✅ Production-ready code quality

**Employees can now:**
1. Create capability assessments for any competency
2. Answer MCQ and scenario questions
3. Receive scored results instantly
4. See competency profile updates
5. Track competency growth over time

**System is ready for:**
- Scaling to production
- User acceptance testing
- Integration with frontend
- Phase 3 (Question Management & Advanced Scoring)

---

**End of Phase 2 Report**

*Implemented by Kiro Agent*  
*Date: August 27, 2026*  
*Status: Ready for Production / Phase 3*
