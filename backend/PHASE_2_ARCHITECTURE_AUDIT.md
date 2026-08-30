# PHASE 2 — CAPABILITY ASSESSMENT EXECUTION AUDIT

## Architecture Design & Reusable Components

**Date:** August 27, 2026  
**Project:** ShikshaSetu — SIH 2026 PS 26101  
**Phase:** Capability Assessment Execution  
**Status:** Pre-Implementation Audit

---

## 1. WHAT WILL BE REUSED (NO CHANGES NEEDED)

### 1.1 Authentication & User Ownership

**Pattern:** `Depends(get_current_user)` in every endpoint

**File:** `app/auth/dependencies.py`

**Current Usage:**
```python
from app.auth.dependencies import get_current_user, CurrentUser

@router.get("/assessments/{id}")
def get_assessment(
    id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    # JWT validates user_id
    # Service validates resource ownership
```

**Reuse Strategy:** EXACT SAME PATTERN
- Phase 2 will use `Depends(get_current_user)` on all assessment endpoints
- Service layer validates user_id matches attempt creator
- No changes to auth/security.py needed

**Files:** `app/auth/dependencies.py`, `app/auth/security.py` (UNCHANGED)

---

### 1.2 Evidence System (Append-Only)

**Current Implementation:** `app/assessments/service.py` → `submit_assessment()`

**Pattern:**
```python
# Phase 1 (existing):
evidence_documents = []
for competency_id, components in grouped.items():
    for evidence_type, component_score in components.items():
        evidence_documents.append({
            "user_id": user_object_id,
            "competency_id": competency_object_id,
            "evidence_type": "KNOWLEDGE_TEST",
            "score": component_score,
            "weight": config_weight,
            "source": "initial_assessment",
            "assessment_id": assessment_id,
            "metadata": {...},
            "created_at": now,
        })
for evidence in evidence_documents:
    repository.insert_evidence(database, evidence)
```

**Reuse Strategy:** EXACT SAME PATTERN for Phase 2
- Create evidence records with source: "capability_assessment"
- Use repository.insert_evidence() (no changes)
- Evidence type: can reuse KNOWLEDGE_TEST for MCQ, SCENARIO_TEST for scenarios
- Append-only: no deletions, no overwrites
- Immutable for audit trail

**Key Files:** 
- `app/assessments/repository.py` → `insert_evidence()` (UNCHANGED)
- `app/competencies/models.py` → `EvidenceType` enum (EXTEND if needed)

**EvidenceType Values Available:**
```python
SELF_ASSESSMENT = "SELF_ASSESSMENT"
KNOWLEDGE_TEST = "KNOWLEDGE_TEST"          # ← Use for MCQ
SCENARIO_TEST = "SCENARIO_TEST"            # ← Use for SCENARIO
TRAINING = "TRAINING"
QUIZ = "QUIZ"                              # ← Already used by Phase 7
```

**Status:** No changes needed; use existing enum values

---

### 1.3 Competency Profile Management

**Current Implementation:** `app/assessments/repository.py` → `upsert_profile()`

**Pattern:**
```python
# Phase 1 (existing):
repository.upsert_profile(
    database,
    user_object_id,
    competency_object_id,
    {
        "current_level": score,          # 1-5 normalized
        "confidence": confidence,        # 0-1 based on evidence weights
        "last_assessed_at": now,
        "status": "active",
        "updated_at": now
    }
)
```

**Reuse Strategy:** EXACT SAME PATTERN for Phase 2
- Same competency profile schema
- Same upsert logic (creates if not exists; updates if exists)
- Same 1-5 scale and 0-1 confidence
- Aggregation logic: existing `weighted_competency_score()` in `scoring.py`

**Key Files:**
- `app/assessments/repository.py` → `upsert_profile()` (UNCHANGED)
- `app/assessments/scoring.py` → `weighted_competency_score()` (REUSE)
- `app/competencies/schemas.py` → `CompetencyProfile` model (UNCHANGED)

---

### 1.4 Scoring Infrastructure

**Current Implementation:** `app/assessments/scoring.py`

**Functions Available:**
```python
score_ratio(ratio: float) -> float
    # Maps percentage (0-1) to level (1-5)
    # 0-19%   → 1
    # 20-39%  → 2
    # 40-59%  → 3
    # 60-79%  → 4
    # 80-100% → 5

weighted_competency_score(components, config) -> float
    # Sums (score × weight) for available components
    # Renormalizes weights if some missing
    # Example: MCQ(40%)+SCENARIO(30%) = renorm to 57%+43%

prototype_confidence(components, config) -> float
    # Sum of weights for available evidence
    # Example: if MCQ+SCENARIO provided = 70% confidence
```

**Reuse Strategy:** EXACT SAME LOGIC for Phase 2
- For MCQ question: binary (correct=1.0, incorrect=0.0) → score_ratio() → 1-5
- For SCENARIO: binary (correct=1.0, incorrect=0.0) → score_ratio() → 1-5
- Use `weighted_competency_score()` with components: {KNOWLEDGE_TEST, SCENARIO_TEST}
- Use `prototype_confidence()` with weights: {40%, 30%, 30% remaining}

**Status:** No changes needed; reuse directly

---

### 1.5 Database Connection & Operations

**Pattern:** Established in `app/core/database.py`

**Reuse Strategy:** EXACT SAME PATTERN
- All repository functions take `database: Database` parameter
- MongoDB operations: `find_one()`, `find()`, `insert_one()`, `update_one()`
- ObjectId handling: existing `object_id()` helper in repository

**Files:** `app/core/database.py` (UNCHANGED)

---

### 1.6 Existing Assessment Model Structure

**Current Assessment Document:**
```json
{
  "_id": ObjectId,
  "assessment_key": "initial-competency-v1",
  "assessment_type": "INITIAL_COMPETENCY",
  "title": "Initial Competency Assessment",
  "questions": [
    {
      "question_id": "q1",
      "competency_id": ObjectId,
      "question_type": "MCQ",
      "question_text": "...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "B",
      "difficulty": "MEDIUM",
      "weight": 1.0
    }
  ],
  "status": "active",
  "version": 1
}
```

**Reuse Strategy:** NEW "assessments" collection will follow SAME structure
- Same question fields for MCQ/SCENARIO
- Same competency_id linkage
- Same difficulty levels
- Same weight mechanism

**Status:** No changes; Phase 2 will use this pattern

---

### 1.7 Router Registration Pattern

**Current Implementation:** `app/main.py`

**Pattern:**
```python
# In app/main.py lifespan or startup:
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(assessments_router)       # ← Will be extended
app.include_router(competencies_router)
app.include_router(quizzes_router)
# ... etc
```

**Reuse Strategy:** EXTEND existing `assessments_router`
- Add new endpoints to `app/assessments/router.py`
- No new router file needed
- Register once in main.py (already done)

**Status:** No changes to main.py registration

---

### 1.8 Error Handling Pattern

**Current Pattern:**
```python
from fastapi import HTTPException, status

# Validation error
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Assessment attempt not found"
)

# Authorization error
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not authorized to access this assessment"
)

# Conflict error
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Assessment already submitted"
)
```

**Reuse Strategy:** EXACT SAME PATTERN for Phase 2

**Status:** No changes needed

---

## 2. WHAT NEEDS TO BE ADDED (NEW CODE)

### 2.1 Question Bank System

**New Collection:** `question_bank`

**Schema:**
```json
{
  "_id": ObjectId,
  "question_id": "Q001",
  "competency_code": "TECH_SQL",
  "question_type": "MCQ",
  "question_text": "What does SQL SELECT do?",
  "options": ["Deletes rows", "Retrieves rows", "Updates rows", "Inserts rows"],
  "correct_answer": "B",
  "explanation": "SELECT retrieves data from a database",
  "difficulty": "EASY",
  "weight": 1.0,
  "source": "phase2_seed",
  "status": "ACTIVE",
  "created_at": ISO8601,
  "updated_at": ISO8601
}
```

**For SCENARIO type:**
```json
{
  "_id": ObjectId,
  "question_id": "S001",
  "competency_code": "TECH_SQL",
  "question_type": "SCENARIO",
  "scenario_context": "You are given a database with customer and orders tables...",
  "question_text": "What query would retrieve all customers with orders over $1000?",
  "options": ["SELECT * FROM customers...", "SELECT COUNT(*)...", ...],
  "correct_answer": "A",
  "explanation": "The correct query joins the tables and filters appropriately",
  "difficulty": "HARD",
  "weight": 1.5,
  "source": "phase2_seed",
  "status": "ACTIVE",
  "created_at": ISO8601,
  "updated_at": ISO8601
}
```

**Indexes:**
- `competency_code` (single)
- `question_type` (single)
- `(competency_code, question_type)` (compound)
- `status` (single)

**NEW FILES:**
- `app/questions/__init__.py`
- `app/questions/models.py`
- `app/questions/schemas.py`
- `app/questions/repository.py`
- `app/questions/seed.py`

---

### 2.2 Capability Assessment Flow

**New Collection:** `capability_assessments`

**Schema (Assessment Instance):**
```json
{
  "_id": ObjectId,
  "user_id": ObjectId,
  "competency_code": "TECH_SQL",
  "configuration_id": ObjectId,
  "assessment_type": "CAPABILITY_ASSESSMENT",
  "title": "SQL Capability Assessment",
  "questions": [
    {
      "question_id": "Q001",
      "competency_code": "TECH_SQL",
      "question_type": "MCQ",
      "question_text": "...",
      "options": ["A", "B", "C", "D"],
      "difficulty": "EASY",
      "weight": 1.0
    }
  ],
  "answers": [
    {
      "question_id": "Q001",
      "selected_answer": "B",
      "is_correct": true
    }
  ],
  "status": "SUBMITTED",
  "score": 85.0,
  "percentage": 0.85,
  "normalized_score": 4.2,
  "started_at": ISO8601,
  "submitted_at": ISO8601,
  "duration_seconds": 1200,
  "competency_results": [
    {
      "competency_code": "TECH_SQL",
      "score": 4.2,
      "confidence": 0.75
    }
  ]
}
```

**Indexes:**
- `user_id` (single)
- `competency_code` (single)
- `(user_id, competency_code)` (compound)
- `status` (single)
- `created_at` (single)

**Statuses:**
- `IN_PROGRESS` - Started but not submitted
- `SUBMITTED` - Answers received, scored, evidence created
- `COMPLETED` - Evidence linked to competency profile

**NEW FILES:**
- `app/capability_assessments/__init__.py`
- `app/capability_assessments/models.py`
- `app/capability_assessments/schemas.py`
- `app/capability_assessments/repository.py`
- `app/capability_assessments/service.py`
- `app/capability_assessments/router.py` (add to existing assessments router)

---

### 2.3 Scoring Engine (Type-Specific)

**New Functions Needed:**

```python
# app/capability_assessments/scoring.py

def calculate_mcq_score(answer: str, correct_answer: str) -> float:
    """Calculate MCQ score (binary: 1.0 or 0.0)"""
    return 1.0 if answer == correct_answer else 0.0

def calculate_scenario_score(answer: str, correct_answer: str) -> float:
    """Calculate scenario score (binary: 1.0 or 0.0)"""
    return 1.0 if answer == correct_answer else 0.0

def calculate_assessment_percentage(answers: list[dict]) -> float:
    """Calculate percentage correct from answers"""
    if not answers:
        return 0.0
    correct_count = sum(1 for a in answers if a.get("is_correct"))
    return correct_count / len(answers)

def calculate_normalized_score(percentage: float) -> float:
    """Map percentage (0-1) to 1-5 scale"""
    # Reuse existing score_ratio logic
    return score_ratio(percentage)
```

**Reuse Existing Functions:**
- `score_ratio()` - percentage to 1-5 scale
- `weighted_competency_score()` - aggregate evidence
- `prototype_confidence()` - calculate confidence

**NEW FILE:**
- `app/capability_assessments/scoring.py`

---

## 3. MODIFIED FILES (MINIMAL CHANGES)

### 3.1 `app/assessments/router.py`

**Current:**
```python
# POST /api/v1/assessments
# POST /api/v1/assessments/{attempt_id}/submit
# GET /api/v1/assessments/configs
# GET /api/v1/assessments/configs/{competency_code}
```

**NEW CAPABILITY ASSESSMENT ENDPOINTS (add to same router):**
```python
# POST /api/v1/assessments (EXTEND - support both types)
# GET /api/v1/assessments/{assessment_id}
# POST /api/v1/assessments/{assessment_id}/submit
# GET /api/v1/assessments/results/{assessment_id}
```

**Change:** Extend existing router to handle type-based routing
- Check request.body for `assessment_type` or `competency_code`
- Route to appropriate handler: INITIAL_COMPETENCY vs CAPABILITY_ASSESSMENT
- OR: Create new routes under `/api/v1/assessments/capability` prefix (CLEANER)

**Recommendation:** Use `/api/v1/assessments/capability/` prefix to separate concerns

**MODIFIED:** `app/assessments/router.py` (+50 lines)

---

### 3.2 `app/assessments/schemas.py`

**Additions:**
```python
# New schema for capability assessment request
class CapabilityAssessmentCreateRequest(BaseModel):
    competency_code: str

# New schema for answer submission
class CapabilityAssessmentAnswerRequest(BaseModel):
    question_id: str
    selected_answer: str

class CapabilityAssessmentSubmitRequest(BaseModel):
    answers: list[CapabilityAssessmentAnswerRequest]

# Response schemas
class CapabilityAssessmentResponse(BaseModel):
    id: str
    competency_code: str
    assessment_type: AssessmentType
    questions: list[dict]
    status: str
    started_at: datetime
    submitted_at: datetime | None = None
    score: float | None = None
    percentage: float | None = None
```

**MODIFIED:** `app/assessments/schemas.py` (+40 lines)

---

### 3.3 `app/core/framework_indexes.py`

**Add indexes for new collections:**
```python
def create_question_bank_indexes(database):
    database.question_bank.create_index([("competency_code", 1)])
    database.question_bank.create_index([("question_type", 1)])
    database.question_bank.create_index([("competency_code", 1), ("question_type", 1)])
    database.question_bank.create_index([("status", 1)])

def create_capability_assessment_indexes(database):
    database.capability_assessments.create_index([("user_id", 1)])
    database.capability_assessments.create_index([("competency_code", 1)])
    database.capability_assessments.create_index([("user_id", 1), ("competency_code", 1)])
    database.capability_assessments.create_index([("status", 1)])
    database.capability_assessments.create_index([("created_at", -1)])
```

**MODIFIED:** `app/core/framework_indexes.py` (+15 lines)

---

### 3.4 `app/main.py` (Optional)

**Option 1 (Recommended):** Keep single assessments router
- Extend existing router with capability assessment endpoints
- No changes to main.py needed

**Option 2:** Create separate router
- Create `app/capability_assessments/router.py`
- Add `include_router(capability_assessments_router)` to main.py

**Current Status:** No changes needed if using Option 1

---

## 4. NEW DIRECTORY STRUCTURE

```
app/
├── assessments/               # EXISTING (extend)
│   ├── schemas.py             # MODIFY: add CapabilityAssessmentRequest schemas
│   ├── router.py              # MODIFY: add capability endpoints
│   └── ... (existing files)
│
├── questions/                 # NEW
│   ├── __init__.py
│   ├── models.py              # Question structure (MCQ, SCENARIO)
│   ├── schemas.py             # Pydantic: QuestionResponse, etc.
│   ├── repository.py          # CRUD: get_question, list_questions, etc.
│   ├── seed.py                # Seed 50-100 sample questions
│   └── __pycache__/
│
├── capability_assessments/    # NEW (OR extend assessments/)
│   ├── __init__.py
│   ├── models.py              # CapabilityAssessment document
│   ├── schemas.py             # Pydantic: CapabilityAssessmentResponse, etc.
│   ├── repository.py          # CRUD: insert, get, update status
│   ├── service.py             # Business logic: create_assessment, submit_answers, score
│   ├── scoring.py             # Type-specific scoring functions
│   ├── router.py              # Endpoints (can be integrated into assessments/router.py)
│   └── __pycache__/
│
└── core/
    └── framework_indexes.py   # MODIFY: add indexes for new collections
```

**Recommendation:** Keep assessments/ flat; add capability functions inline

---

## 5. API ENDPOINTS (PHASE 2)

### 5.1 Create Capability Assessment

**Endpoint:** `POST /api/v1/assessments/capability`

**Request:**
```json
{
  "competency_code": "TECH_SQL"
}
```

**Response (200):**
```json
{
  "id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "assessment_type": "CAPABILITY_ASSESSMENT",
  "title": "SQL Capability Assessment",
  "questions": [
    {
      "question_id": "Q001",
      "question_type": "MCQ",
      "question_text": "What does SQL SELECT do?",
      "options": ["Deletes", "Retrieves", "Updates", "Inserts"],
      "difficulty": "EASY",
      "weight": 1.0
    }
  ],
  "status": "IN_PROGRESS",
  "started_at": "2026-08-27T12:00:00Z",
  "submitted_at": null,
  "score": null,
  "percentage": null
}
```

**Security:** Requires JWT (get_current_user)

**Errors:**
- 404: Configuration not found for competency
- 400: Invalid competency_code
- 409: User already has IN_PROGRESS assessment for this competency (if not allow_retake)

---

### 5.2 Get Assessment (In Progress or Submitted)

**Endpoint:** `GET /api/v1/assessments/capability/{assessment_id}`

**Response (200):**
```json
{
  "id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "assessment_type": "CAPABILITY_ASSESSMENT",
  "questions": [
    {
      "question_id": "Q001",
      "question_type": "MCQ",
      "question_text": "...",
      "options": ["A", "B", "C", "D"],
      "difficulty": "EASY"
    }
  ],
  "status": "IN_PROGRESS",
  "started_at": "2026-08-27T12:00:00Z"
}
```

**Security:** JWT required; user can only access their own assessments

**Errors:**
- 404: Assessment not found
- 403: Not authorized

---

### 5.3 Submit Assessment Answers

**Endpoint:** `POST /api/v1/assessments/capability/{assessment_id}/submit`

**Request:**
```json
{
  "answers": [
    {
      "question_id": "Q001",
      "selected_answer": "B"
    },
    {
      "question_id": "S001",
      "selected_answer": "A"
    }
  ]
}
```

**Response (200):**
```json
{
  "assessment_id": "607f1f77bcf86cd799439012",
  "status": "SUBMITTED",
  "score": 85.0,
  "percentage": 0.85,
  "normalized_score": 4.2,
  "competency_code": "TECH_SQL",
  "competency_results": [
    {
      "competency_code": "TECH_SQL",
      "score": 4.2,
      "confidence": 0.75
    }
  ]
}
```

**Server-Side Operations:**
1. Validate JWT & user ownership
2. Validate all questions answered
3. Check no duplicate submission
4. Calculate MCQ/SCENARIO scores (binary)
5. Calculate percentage and normalized score
6. Create evidence records (append-only)
7. Update competency profile
8. Return results

**Security:** JWT required; user can only submit their own assessments

**Errors:**
- 404: Assessment not found
- 409: Already submitted
- 422: Invalid answer format, missing answers, duplicate answers

---

### 5.4 Get Results

**Endpoint:** `GET /api/v1/assessments/capability/{assessment_id}/results`

**Response (200):**
```json
{
  "assessment_id": "607f1f77bcf86cd799439012",
  "competency_code": "TECH_SQL",
  "status": "SUBMITTED",
  "score": 85.0,
  "percentage": 0.85,
  "normalized_score": 4.2,
  "duration_seconds": 1200,
  "competency_before": 2.4,
  "competency_after": 2.8,
  "confidence_after": 0.75,
  "evidence_type": "KNOWLEDGE_TEST",
  "correct_answers": 17,
  "total_questions": 20,
  "submitted_at": "2026-08-27T12:20:00Z"
}
```

**Security:** JWT required; user can only view their own results

**Errors:**
- 404: Assessment not found
- 400: Assessment not yet submitted

---

## 6. SECURITY CONTROLS

### 6.1 User Ownership Validation

**Pattern:**
```python
# In repository:
def get_capability_assessment(database, assessment_id: str, user_id: str):
    return database.capability_assessments.find_one({
        "_id": ObjectId(assessment_id),
        "user_id": ObjectId(user_id)  # ← Owner check
    })

# In service:
assessment = repository.get_capability_assessment(db, assessment_id, current_user["_id"])
if assessment is None:
    raise HTTPException(403, "Not authorized")
```

**Applies To:**
- GET /assessments/capability/{id}
- POST /assessments/capability/{id}/submit
- GET /assessments/capability/{id}/results

---

### 6.2 Answer Key Protection

**Implementation:**
```python
# In service.py when returning assessment to employee:
def public_assessment(assessment: dict) -> dict:
    """Remove sensitive data before returning to user"""
    return {
        "id": str(assessment["_id"]),
        "questions": [
            {
                "question_id": q["question_id"],
                "question_text": q["question_text"],
                "options": q["options"],
                "difficulty": q["difficulty"],
                # NOTE: correct_answer NOT included
            }
            for q in assessment["questions"]
        ],
        "status": assessment["status"],
        # ... other public fields
    }
```

**Applied To:** GET /assessments/capability/{id} (IN_PROGRESS state)

**Note:** After submission, can optionally show correct answers if config allows

---

### 6.3 Server-Side Scoring Only

**Implementation:**
```python
# In service.py:
def submit_assessment(db, user_id, assessment_id, answers):
    # 1. Load assessment from DB
    assessment = get_assessment(db, assessment_id, user_id)
    
    # 2. Load original questions from question_bank
    # (don't trust questions in attempt)
    questions = load_questions_from_db(db, assessment.question_ids)
    
    # 3. Calculate scores using DB truth
    scores = []
    for answer in answers:
        question = find_question(questions, answer.question_id)
        if answer.selected_answer == question.correct_answer:
            score = 1.0
        else:
            score = 0.0
        scores.append({"question_id": answer.question_id, "is_correct": score == 1.0})
    
    # 4. Calculate final score server-side only
    final_score = calculate_score(scores)
    
    # 5. Never trust client-provided score
    # Always recalculate from answers
```

**Key:** Questions stored in DB; client cannot modify them; scoring happens server-side

---

### 6.4 Duplicate Submission Prevention

**Pattern:**
```python
def submit_assessment(db, user_id, assessment_id, answers):
    # Check status BEFORE scoring
    assessment = get_assessment(db, assessment_id, user_id)
    
    if assessment["status"] == "SUBMITTED":
        raise HTTPException(409, "Assessment already submitted")
    
    # Continue with scoring...
```

**Atomicity:** Use MongoDB `$set` with status check to prevent race conditions

---

## 7. DATA FLOW DIAGRAM

```
User (Employee)
    ↓
[JWT Token + competency_code]
    ↓
POST /assessments/capability
    ↓
get_current_user() → user_id
    ↓
Load Config: assessment_configurations[competency_code]
    ↓
Select Questions:
    - From question_bank[competency_code]
    - random selection based on config
    - Include MCQ + SCENARIO types as per config
    ↓
Create Assessment Document:
    - Store questions (no answers exposed)
    - Store user_id for ownership
    - status: IN_PROGRESS
    - Return to frontend (no answer keys)
    ↓
--- User solves questions ---
    ↓
POST /assessments/capability/{id}/submit
    ↓
[user_id, answers[{question_id, selected_answer}]]
    ↓
Validate:
    - User ownership (user_id matches)
    - Status is IN_PROGRESS (not already submitted)
    - All questions answered
    - No duplicate question_ids in answers
    ↓
Score (Server-Side):
    - Load original questions from DB
    - For each answer:
        - is_correct = answer == question.correct_answer
    - Calculate percentage
    - Convert to 1-5 scale (score_ratio)
    ↓
Create Evidence (Append-Only):
    - For each component (MCQ, SCENARIO):
        - Insert into competency_evidence
        - evidence_type: KNOWLEDGE_TEST or SCENARIO_TEST
        - source: "capability_assessment"
        - score: normalized 1-5
        - weight: from config
        - assessment_id: link to assessment
    ↓
Update Competency Profile:
    - Aggregate all evidence for competency
    - weighted_competency_score()
    - prototype_confidence()
    - upsert_profile() with new level + confidence
    ↓
Return Result:
    - assessment_id
    - status: SUBMITTED
    - score, percentage, normalized_score
    - competency_results: [{competency_code, score, confidence}]
    - Evidence linked for future reference
```

---

## 8. QUESTION BANK SEEDING STRATEGY

### 8.1 Sample Data

**MCQ Questions (TECH_SQL competency):**
```
Q001: EASY - "What does SELECT do?"
Q002: MEDIUM - "Write a JOIN query..."
Q003: HARD - "Optimize this slow query..."

S001: EASY - "You need to find all customers with orders..."
S002: MEDIUM - "Design a schema for..."
S003: HARD - "Handle this complex scenario..."
```

**Sources:**
- TECH_PYTHON: 10 MCQ + 5 SCENARIO (total 15)
- TECH_SQL: 10 MCQ + 5 SCENARIO (total 15)
- TECH_R: 8 MCQ + 3 SCENARIO (total 11)
- STAT_SAMPLING: 8 MCQ + 2 SCENARIO (total 10)
- STAT_SURVEY_DESIGN: 8 MCQ + 2 SCENARIO (total 10)
- DIGOV_CYBERSECURITY: 10 MCQ + 3 SCENARIO (total 13)
- DIGOV_DATA_PRIVACY: 10 MCQ + 3 SCENARIO (total 13)
- BEH_LEADERSHIP: 8 MCQ + 5 SCENARIO (total 13)
- BEH_COMMUNICATION: 8 MCQ + 3 SCENARIO (total 11)
- BEH_PROJECT_MANAGEMENT: 8 MCQ + 3 SCENARIO (total 11)

**Total:** ~130 questions across all competencies

---

### 8.2 Seeding File

**File:** `app/questions/seed.py`

**Function:**
```python
def seed_questions(database: Database) -> dict[str, int]:
    """Seed question bank with sample MCQ and SCENARIO questions"""
    # Load all competency codes from competencies collection
    # For each competency, create 10-15 questions
    # 60-70% MCQ, 30-40% SCENARIO
    # Mix of EASY, MEDIUM, HARD difficulties
    # Insert into question_bank collection
    # Return counts
```

---

## 9. TESTING STRATEGY

### 9.1 Unit Tests

**Module:** `tests/test_capability_assessment_execution.py`

**Coverage:**
```
Question Bank:
  - Seed questions
  - Get questions by competency
  - Get random questions for assessment
  - Difficulty levels
  
Assessment Creation:
  - Load configuration
  - Select questions based on config
  - Create attempt document
  - No answer keys exposed
  
Answer Validation:
  - All required questions answered
  - No duplicate questions
  - Valid options selected
  
Scoring:
  - MCQ binary scoring (1.0 or 0.0)
  - SCENARIO binary scoring (1.0 or 0.0)
  - Percentage calculation
  - Normalized score (1-5 scale)
  - Edge cases: 0% → 1, 100% → 5
  
Evidence Creation:
  - Evidence records created for each component
  - Append-only (no overwrites)
  - Correct evidence_type mapping
  - Timestamps correct
  
Competency Update:
  - Profile created if not exists
  - Profile updated if exists
  - Score and confidence recalculated
  - History preserved
  
Authentication:
  - JWT validation required
  - User ownership enforced
  - Cannot access other user's assessment
  
Duplicate Submission:
  - First submission succeeds
  - Second submission fails (409 Conflict)
  - Status prevents resubmission
```

**Minimum:** 25+ test cases

---

### 9.2 Integration Tests

**Flow:**
```
1. Create Assessment
   - Call POST /assessments/capability
   - Verify assessment created
   - Verify no answer keys
   
2. Submit Answers
   - Call POST /assessments/capability/{id}/submit
   - Verify scoring correct
   - Verify evidence created
   - Verify competency updated
   
3. Check Results
   - Call GET /assessments/capability/{id}/results
   - Verify score displayed
   - Verify before/after competency shown
   
4. Verify Ownership
   - Try to access with different user
   - Verify 403 Forbidden
   
5. Verify No Retake
   - Submit again
   - Verify 409 Conflict
```

---

### 9.3 Regression Testing

**Baseline:** 115/115 tests passing (Phase 1 + existing)

**Requirement:** All 115 must still pass after Phase 2

**Command:** `pytest tests/ -v`

**Critical Tests to Verify:**
- Initial Competency Assessment (Phase 4) still works
- Quiz Engine (Phase 7) still works
- Competency profiles still updatable
- Skill gaps still calculated correctly
- Evidence still append-only

---

## 10. ARCHITECTURAL DECISIONS

### 10.1 Where to Store Capability Assessments

**Option A:** In `assessments` collection (existing)
- ✓ Simpler: one collection for all assessment types
- ✗ May become large; schema must accommodate all types

**Option B:** In separate `capability_assessments` collection
- ✓ Cleaner: separate concerns
- ✓ Easier to scale
- ✓ Clear index strategy per collection
- ✗ Requires joins conceptually (but MongoDB doesn't)

**Decision:** **OPTION B** - Separate collection
- Assessment type separation is cleaner
- Query performance better (targeted indexes)
- Future phases can add other assessment types independently

---

### 10.2 Question Storage: Separate Collection vs. Embedded

**Option A:** Store full question text in assessment (embedded)
- ✓ Assessment is self-contained
- ✗ Duplication; space waste
- ✗ Hard to update question bank later

**Option B:** Store question_id only; load from question_bank at runtime
- ✓ Single source of truth
- ✓ No duplication
- ✗ Requires join (negligible cost)

**Option C:** Store question_id + denormalized fields (id, text, options) in assessment
- ✓ Self-contained + no duplication of correct_answer
- ✓ Fast retrieval

**Decision:** **OPTION C** - Denormalize non-sensitive fields only
- Store: question_id, question_text, options, difficulty, question_type
- Do NOT store: correct_answer (server-side only)
- At submission: load question by question_id to get correct_answer for comparison

---

### 10.3 Evidence Aggregation

**Question:** When user submits capability assessment, should evidence aggregate with INITIAL_COMPETENCY evidence?

**Option A:** No - keep separate (evidence_source distinguishes them)
- ✓ Simpler
- ✗ Competency score doesn't reflect capability assessment

**Option B:** Yes - aggregate together
- ✓ True reflection of competency
- ✓ Skill gaps recalculate automatically
- ✓ Matches existing pattern (Phase 4 + Phase 7 both update same profile)

**Decision:** **OPTION B** - Aggregate together
- Use weighted_competency_score() with all evidence
- Competency profile reflects ALL assessments user has completed
- Evidence table tracks source for audit trail

---

## 11. BACKWARD COMPATIBILITY

### 11.1 What Must NOT Change

| Component | Requirement | Verification |
|-----------|-------------|--------------|
| Initial Competency Assessment | Must still work | POST /assessments still works |
| Quiz Engine | Must still work | POST /quizzes still works |
| Competency Profiles | Must still exist | GET /competencies/me returns profile |
| Evidence Table | Append-only | New records added, old ones unchanged |
| Skill Gap Calculation | Still accurate | GET /skill-gaps/me returns correct gaps |

### 11.2 Test Suite Requirements

**115 Existing Tests:** All must still pass

**New Tests:** 25+ for Phase 2

**Regression Command:** `pytest tests/ -v → (115 + 25) PASSED`

---

## 12. SUMMARY: WHAT EACH FILE DOES

| File | Purpose | Status |
|------|---------|--------|
| `app/questions/models.py` | Question structure (MCQ, SCENARIO) | NEW |
| `app/questions/schemas.py` | Pydantic: Question validation | NEW |
| `app/questions/repository.py` | Question CRUD (get, list by competency, random) | NEW |
| `app/questions/seed.py` | Seed 130+ questions | NEW |
| `app/capability_assessments/models.py` | CapabilityAssessment document structure | NEW |
| `app/capability_assessments/schemas.py` | Pydantic: Requests/Responses | NEW |
| `app/capability_assessments/repository.py` | CRUD: create, get, update status | NEW |
| `app/capability_assessments/service.py` | Business logic: create, submit, score, evidence | NEW |
| `app/capability_assessments/scoring.py` | Type-specific scoring (MCQ, SCENARIO) | NEW |
| `app/capability_assessments/router.py` | Endpoints (or extend assessments/router.py) | NEW |
| `app/assessments/router.py` | MODIFY: Add /capability endpoints | EXTEND |
| `app/assessments/schemas.py` | MODIFY: Add CapabilityAssessmentRequest schemas | EXTEND |
| `app/core/framework_indexes.py` | MODIFY: Add indexes for new collections | EXTEND |
| `tests/test_capability_assessment_execution.py` | 25+ comprehensive tests | NEW |

---

## 13. RECOMMENDATIONS

### 13.1 Implementation Order

1. **Task #2:** Create question_bank collection + indexes
2. **Task #3:** Create Question schemas
3. **Task #4:** Seed 130+ questions
4. **Task #5:** Implement question repository CRUD
5. **Task #6:** Create CapabilityAssessment model
6. **Task #7:** Implement capability assessment repository
7. **Task #8-10:** Implement endpoints (POST create, GET retrieve, POST submit)
8. **Task #11:** Implement server-side scoring
9. **Task #12:** Implement evidence + competency update
10. **Task #13-17:** Write comprehensive tests
11. **Task #18:** Regression testing
12. **Task #19-20:** Documentation

---

### 13.2 Risk Mitigation

**Risk:** Breaking existing assessments

**Mitigation:**
- Don't modify existing assessment routes; add new /capability prefix
- Don't change evidence table schema; just add new records
- Don't change competency profile schema; just update values
- Test existing routes after each change

**Risk:** Score calculation errors

**Mitigation:**
- All scoring server-side only
- Don't trust client scores
- Unit test all scoring functions
- Load correct_answer from DB, don't trust client

**Risk:** User accessing another user's assessment

**Mitigation:**
- Every repository function checks user_id
- Every service function validates ownership
- Test user ownership with multiple users

---

## 14. NEXT STEPS

1. ✅ **This Audit** - Document what to build
2. ⏳ **Task #2-20** - Implement Phase 2
3. ⏳ **Task #18** - Verify 115+ tests passing
4. ⏳ **Task #20** - Document API contract

---

**End of Phase 2 Architecture Audit**

*Date: August 27, 2026*  
*Status: Ready for Implementation*
