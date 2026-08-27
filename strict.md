# SHIKSHASETU — ROUND 1

## STRICT BACKEND + AI IMPLEMENTATION INSTRUCTIONS

You are working on **ShikshaSetu**, the SIH 2026 solution developed by **Team Kinetics** for **Problem Statement 26101 — MoSPI / DIID**.

You have been provided with the project's master specification/brief. That specification is the **primary source of truth** for the product requirements and architecture.

Your responsibility is to implement the **backend + AI layer for Round 1**.

---

# 1. DEVELOPER OWNERSHIP

For Round 1:

**Abhishek**

* Backend
* Database
* APIs
* Authentication
* Competency engine
* Skill-gap engine
* Recommendation engine
* iGOT/NSSTA integration layer
* AI/LLM integration
* RAG/document processing
* AI MCQ generation
* Quiz evaluation
* Competency update logic
* Backend testing
* Integration

**Sanika**

* Works independently on UI/frontend
* PPT/presentation
* Only coordinate with backend when API contracts/data structures are required.

Do NOT assign backend implementation tasks to other team members.

---

# 2. MOST IMPORTANT RULE

## DO NOT START CODING IMMEDIATELY.

First inspect the existing repository completely.

You MUST determine:

* Current technology stack
* Frontend architecture
* Backend architecture
* Database
* Existing models
* Existing APIs/routes
* Authentication
* Existing services
* Existing dashboards
* Existing AI functionality
* Existing iGOT functionality
* Existing NSSTA functionality
* Existing reusable components
* Existing seed data
* Existing deployment configuration
* Existing environment configuration

Do not assume that something is missing until you inspect the repository.

---

# 3. NO DUPLICATION

This is a strict rule.

If functionality already exists:

**REUSE IT.**

Do NOT:

* create duplicate authentication
* create duplicate user models
* create duplicate dashboards
* create duplicate APIs
* create duplicate database connections
* create duplicate services
* create duplicate components
* replace working implementations unnecessarily

If an existing implementation is weak but reusable, modify it rather than rebuilding the entire system.

Before creating any new major module, explicitly determine whether an existing module can be extended.

---

# 4. NO MAJOR REWRITE

Do NOT rewrite the project from scratch.

Do NOT replace the existing framework simply because you prefer another framework.

Do NOT migrate databases unless there is a genuine technical blocker.

Do NOT replace working architecture without a strong reason.

If the existing architecture is acceptable:

**BUILD ON TOP OF IT.**

If the architecture has a serious problem:

1. Explain the problem.
2. Explain the impact.
3. Propose the smallest practical correction.
4. Wait for approval before destructive architectural changes.

---

# 5. ROUND 1 OBJECTIVE

The goal is NOT to build the complete production platform.

The goal is to create a reliable Round 1 prototype demonstrating the core intelligence loop:

```text
Employee
↓
Profile
↓
Competency Assessment
↓
Current Competency
↓
Required Competency
↓
Skill Gap
↓
iGOT + NSSTA Recommendations
↓
Learning
↓
AI Quiz
↓
Assessment
↓
Competency Update
↓
Updated Recommendation
```

This workflow has the highest priority.

---

# 6. BACKEND PRIORITY

Build the backend around these capabilities:

## Authentication

* Login
* User roles
* Authorization
* Password hashing
* Secure authentication/session/JWT according to the existing architecture

Do not rebuild authentication if it already exists.

---

## Employee Profile

Support:

* Name
* Designation
* Department
* Current assignment
* Education
* Experience
* Previous training
* Skills
* Role

---

# 7. COMPETENCY FRAMEWORK

Use the competency framework defined in the master specification.

Domains:

### Statistical

* Survey Design
* Sampling
* National Accounts
* Price Statistics
* Labour Statistics
* Agricultural Statistics
* Industrial Statistics
* SDG Indicators
* Metadata Standards
* Data Quality Frameworks

### Technical

* Python
* R
* SQL
* Stata
* SPSS
* SAS
* GIS
* Data Visualization
* AI/ML
* Cloud Computing
* APIs
* Open Data

### Digital Governance

* Cybersecurity
* Data Privacy
* Digital Signatures
* Government Cloud
* Digital Public Infrastructure

### Behavioural / Managerial

* Leadership
* Communication
* Project Management
* Ethics
* Decision Making
* Change Management

Do not create an unnecessarily huge taxonomy.

---

# 8. COMPETENCY LEVELS

Use the prototype scale:

```text
1 = Awareness
2 = Basic
3 = Intermediate
4 = Advanced
5 = Expert
```

IMPORTANT:

This is a **ShikshaSetu prototype scale**.

Never describe it as an official MoSPI/iGOT competency scale unless official evidence exists.

Store appropriate metadata such as:

```text
framework_status = "prototype"
```

---

# 9. COMPETENCY ASSESSMENT

Do NOT rely only on self-assessment.

Support evidence from:

```text
Self Assessment
Knowledge MCQs
Scenario-based Questions
Previous Training Evidence
```

Prototype weighting:

```text
Self Assessment       20%
Knowledge Test        40%
Scenario Assessment   30%
Training Evidence     10%
```

Make the weights configurable.

Do not hardcode them throughout the codebase.

The backend should calculate:

```text
Final Competency
+
Confidence
+
Evidence
```

The calculation must be:

* deterministic
* explainable
* testable
* configurable

---

# 10. SKILL GAP ENGINE

Basic formula:

```text
Gap = Required Competency - Current Competency
```

For each competency return:

```text
competency
current_level
required_level
gap
priority
```

Prioritize using:

* gap size
* role importance
* competency priority

Do not use an LLM to calculate the fundamental competency gap.

---

# 11. ROLE REQUIREMENTS

Roles must have required competency levels.

Example:

```text
Statistical Officer

Sampling = 4
Survey Design = 4
Data Quality = 4
Python = 3
SQL = 3
Data Visualization = 3
GIS = 2
AI/ML = 2
```

The role requirements should be stored in the database/configuration layer rather than scattered through code.

---

# 12. LEARNING RESOURCE ARCHITECTURE

This is extremely important.

Do NOT create completely separate recommendation engines for iGOT and NSSTA.

Use a common abstraction:

```text
LearningResource

provider:
    IGOT
    NSSTA

resource_type:
    COURSE
    TRAINING_PROGRAMME
```

The recommendation engine should operate on both.

Conceptually:

```text
LearningResource
├── IGOT Course
└── NSSTA Training Programme
```

---

# 13. iGOT DATA

The project currently has an initial 56+ course dataset.

Use it for the Round 1 prototype.

Preserve official metadata where available.

When metadata is missing, derived metadata may be generated.

But NEVER mix official and derived metadata.

Use a clear separation such as:

```text
official_metadata
derived_metadata
```

or equivalent schema.

Derived fields may include:

```text
derived_description
derived_domain
derived_competencies
derived_subskills
derived_keywords
derived_target_roles
derived_learning_outcomes
derived_prerequisites
derived_skill_level
derived_skill_level_confidence
derivation_basis
derivation_confidence
```

Never claim derived information is official iGOT metadata.

---

# 14. NSSTA / TPAC

Round 1 does NOT require a live NSSTA API.

Use structured prototype data based on verified official publications where available.

Support fields such as:

```text
programme_id
programme_name
topic
description
duration
target_participants
batch_size
venue
training_year
start_date
end_date
recommended_by_tpac
source_url
source_document
last_verified_at
status
```

If no official programme ID exists:

```text
NSSTA-PROT-001
```

and:

```text
id_type = INTERNAL_PROTOTYPE
```

Never pretend this is an official NSSTA ID.

Never create fake live information such as:

* available seats
* live enrollment
* live completion
* next batch

unless an actual official live source exists.

---

# 15. PROVIDER / ADAPTER ARCHITECTURE

Implement provider abstraction.

Prototype:

```text
PrototypeIGOTProvider
PrototypeNSSTAProvider
```

Future:

```text
RealIGOTProvider
RealNSSTAProvider
```

The recommendation engine must NOT need to change when switching providers.

Do not claim live API integration if no live API access exists.

---

# 16. RECOMMENDATION ENGINE

This is a core backend module.

Do NOT send the complete employee profile to an LLM and ask it to select courses.

Correct architecture:

```text
Employee
↓
Competency Engine
↓
Skill Gap
↓
Candidate Learning Resources
↓
Deterministic Ranking
↓
Top Recommendations
↓
Optional LLM Explanation
```

Ranking should consider:

* competency match
* role match
* gap priority
* current competency level
* difficulty/level match
* prerequisites
* learning history
* TPAC relevance

The ranking algorithm should be deterministic and testable.

The LLM may explain the recommendation but should not independently make the core recommendation decision.

---

# 17. RECOMMENDATION EXPLANATION

Every recommendation should be explainable.

Example:

> Recommended because your Sampling competency is 2.2/5 while your Statistical Officer role requires 4/5, and this learning resource directly addresses Sampling.

Do not generate explanations containing unsupported claims.

---

# 18. AI ARCHITECTURE

DO NOT TRAIN A NEW LLM.

Use an existing LLM/API or suitable open-source model.

LLM responsibilities:

```text
Course metadata enrichment
Semantic competency mapping
Document understanding
MCQ generation
Explanations
Learner assistant if required
```

Backend/deterministic responsibilities:

```text
Competency scoring
Skill-gap calculation
Role requirements
Recommendation ranking
Permissions
Progress
Database operations
```

The LLM must not control every important decision.

---

# 19. DOCUMENT → AI QUIZ PIPELINE

Support:

* PDF
* PPT/PPTX
* DOC/DOCX

Pipeline:

```text
Upload
↓
Text Extraction
↓
Cleaning
↓
Chunking
↓
Retrieval / RAG
↓
LLM
↓
MCQ Generation
↓
Validation
↓
Quiz
↓
Evaluation
```

Generated question structure should contain:

```text
question
options
correct_answer
explanation
difficulty
competency
source_reference
```

Where possible:

```text
source_chunk_id
source_page
```

must be retained.

---

# 20. AI QUESTION VALIDATION

Do not blindly trust the LLM.

Validate:

* exactly one correct answer
* required number of options
* no missing fields
* answer exists in options
* competency belongs to approved taxonomy
* difficulty is valid
* source reference exists where expected
* question is grounded in retrieved content

If validation fails, reject/regenerate the question.

---

# 21. QUIZ → COMPETENCY UPDATE

This is a critical feature.

Example:

```text
Before:

Sampling = 2.2
```

User completes:

```text
Quiz = 8/10
```

Backend processes the new evidence.

Then:

```text
Sampling = 2.9
```

The exact update formula must be deterministic and documented.

Do NOT simply do:

```text
8/10 = Sampling 4/5
```

unless that mapping is explicitly justified.

The quiz result should become one piece of competency evidence.

After updating competency:

```text
Recalculate Skill Gap
↓
Recalculate Recommendations
```

---

# 22. DATABASE DESIGN

Use the existing database if already present.

Extend it rather than replacing it.

The conceptual data model should support:

```text
users
roles
competencies
role_competencies
user_competencies
competency_evidence

learning_resources
igot_courses
nssta_programmes

course_competencies
programme_competencies

assessments
questions
assessment_attempts

learning_materials
document_chunks

quiz_attempts

learning_progress
recommendations
```

Do not create unnecessary collections/tables.

If the existing schema already provides equivalent functionality, reuse it.

---

# 23. API DESIGN

Create clean API contracts.

Potential endpoints include:

```text
POST /auth/login

GET /users/me
PUT /users/me

GET /competencies
GET /competencies/me

POST /assessments
GET /assessments/:id
POST /assessments/:id/submit

GET /skill-gaps/me

GET /learning-resources
GET /recommendations/me

GET /igot/courses
GET /nssta/programmes

POST /learning-materials/upload

POST /quizzes/generate
GET /quizzes/:id
POST /quizzes/:id/submit

GET /dashboard/employee
GET /dashboard/admin
```

These are examples.

Do NOT create them blindly.

First inspect existing routes and architecture and adapt them.

---

# 24. SECURITY

Implement appropriate Round 1 security:

* password hashing
* authentication
* authorization
* RBAC
* input validation
* file validation
* file size restrictions
* secure environment variables
* API authorization
* user data isolation
* basic audit logging
* no API keys in frontend

Do not spend the majority of Round 1 building full government-grade infrastructure without actual requirements/access.

---

# 25. AI FAILURE HANDLING

The system must gracefully handle:

* LLM timeout
* LLM unavailable
* malformed LLM output
* invalid JSON
* empty document
* unsupported file
* oversized file
* no relevant content
* no matching competency
* no matching course
* database failure

Never let an AI failure crash the entire backend.

---

# 26. TESTING REQUIREMENT

Every important backend module must have tests.

At minimum test:

### Competency

```text
weighted score
confidence
evidence
```

### Skill gap

```text
required
current
gap
priority
```

### Recommendations

```text
matching
ranking
provider
explanation
```

### Quiz

```text
generation
validation
submission
scoring
```

### Competency update

```text
before
quiz evidence
after
```

### Security

```text
unauthorized access
cross-user access
invalid token
```

---

# 27. DEVELOPMENT PROCESS

Work ONE logical module at a time.

For every module:

1. Inspect existing implementation.
2. Explain what already exists.
3. Identify what can be reused.
4. Identify what is missing.
5. Explain the proposed change.
6. Implement the smallest correct change.
7. Run tests.
8. Verify the result.
9. Report exactly what changed.
10. Only then move to the next module.

Do NOT dump hundreds of lines of unrelated code.

---

# 28. CHANGE CONTROL

Before making a major change, state:

```text
WHY:
WHAT:
FILES AFFECTED:
RISK:
ALTERNATIVES:
```

Avoid unnecessary changes.

Do not modify unrelated files.

Do not rename large parts of the project without reason.

Do not delete existing functionality unless explicitly justified.

---

# 29. DEFINITION OF DONE

A module is NOT complete because the code compiles.

It is complete only when:

```text
Implementation
+
Integration
+
Testing
+
Verification
```

are complete.

---

# 30. ROUND 1 PRIORITY ORDER

Follow this order unless the repository audit shows a strong reason otherwise:

```text
PHASE 0
Repository Audit

PHASE 1
Architecture + Database

PHASE 2
Competency Taxonomy + Role Requirements

PHASE 3
Authentication + Profiles

PHASE 4
Competency Assessment

PHASE 5
Skill Gap Engine

PHASE 6
iGOT + NSSTA Resources

PHASE 7
Recommendation Engine

PHASE 8
AI Document → Quiz

PHASE 9
Quiz → Competency Update

PHASE 10
Frontend Integration

PHASE 11
Testing

PHASE 12
SIH Demo Hardening
```

---

# 31. DO NOT OVERBUILD

Do NOT prioritize:

* training our own LLM
* full iGOT clone
* full NSSTA clone
* fake live APIs
* blockchain
* 3D avatars
* unnecessary AI agents
* huge predictive analytics
* massive dashboards
* complete government SSO without access
* thousands of courses
* unnecessary microservices

If a feature does not improve the core intelligence loop, question whether it belongs in Round 1.

---

# 32. CORE PRODUCT TEST

Before implementing any feature, ask:

> Does this help ShikshaSetu understand what the employee's role requires, assess what they currently know, identify competency gaps, recommend appropriate iGOT/NSSTA learning, measure learning, and update competency?

If NO:

**Deprioritize it unless it is necessary infrastructure.**

---

# 33. FIRST TASK — MANDATORY

Your FIRST response after inspecting the repository must NOT contain major implementation code.

Instead produce:

# PHASE 0 — TECHNICAL AUDIT

Include:

1. Current technology stack
2. Current architecture
3. Frontend structure
4. Backend structure
5. Database structure
6. Authentication
7. Existing APIs
8. Existing AI functionality
9. Existing iGOT functionality
10. Existing NSSTA functionality
11. Existing dashboards
12. Reusable components
13. Existing problems/bugs
14. Missing modules
15. Technical risks
16. Duplicate functionality
17. Recommended architecture
18. Proposed database changes
19. Recommended API structure
20. Exact implementation roadmap

For every recommendation, distinguish:

```text
EXISTING
REUSE
MODIFY
NEW
REMOVE
```

Do not start major coding until this audit is complete.

---

# FINAL RULE

The objective is NOT to make the codebase look technologically impressive.

The objective is to make **ShikshaSetu work reliably in an SIH Round 1 demonstration**.

Prioritize:

```text
Correctness
>
Core Problem Solving
>
Reliability
>
Demonstrability
>
Technical Quality
>
Development Speed
>
Scalability
>
Fancy Features
```

Be direct.

If an approach is bad, say:

**"This is a bad approach because..."**

Then provide the better alternative.

If something is unnecessary:

**"Do not build this for Round 1."**

If something requires unavailable government access:

**"This cannot be implemented as a real integration without official access. We will use a legitimate prototype adapter instead."**

Never hide technical limitations just to make the project sound impressive.


Yes. Then we should **standardize the backend + AI stack around Python**. I would update the strict agent instruction accordingly.

### ShikshaSetu Round 1 — Python Stack

I recommend:

| Layer                 | Technology                                                                             |
| --------------------- | -------------------------------------------------------------------------------------- |
| Backend API           | **FastAPI**                                                                            |
| Language              | **Python 3.12+**                                                                       |
| Database              | **MongoDB** if your existing project already uses it; otherwise we decide during audit |
| ODM/DB Driver         | **PyMongo / Motor depending on current compatibility needs**                           |
| Validation            | **Pydantic**                                                                           |
| Authentication        | **JWT + password hashing**                                                             |
| AI/LLM                | Python LLM SDK/API                                                                     |
| RAG                   | **FAISS or Chroma** for prototype                                                      |
| Embeddings            | Appropriate embedding model/API                                                        |
| PDF processing        | PyMuPDF                                                                                |
| DOCX                  | python-docx                                                                            |
| PPTX                  | python-pptx                                                                            |
| Background processing | Start simple; don't introduce Celery/Redis unless actually needed                      |
| Testing               | **pytest**                                                                             |
| API documentation     | FastAPI/OpenAPI                                                                        |

### Architecture

```text
                    SHIKSHASETU
                         │
                    FastAPI API
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     Core Logic       AI Layer         Data Layer
        │                │                │
   ┌────┴────┐      ┌────┴────┐       MongoDB
   │         │      │         │
Competency  Gap    RAG       LLM
   │         │      │         │
Assessment  │      │      MCQ Generator
             │     │
             │  Documents
             │
       Recommendation
             │
       iGOT + NSSTA
```

### One important decision

**Don't let the AI agent choose the backend framework.**

Tell it explicitly:

> **Python + FastAPI is the required backend stack for ShikshaSetu Round 1. Do not migrate the backend to Node.js, Express, Django, Flask, Java, or another backend framework unless the existing repository contains a critical dependency that makes FastAPI impractical.**

If an existing backend is already substantial, the agent should **audit it first** and tell us whether migration is justified. We should not rewrite a working backend merely because we're standardizing on Python.

For the AI portion, Python is actually a good choice because our document processing, RAG, embeddings, evaluation, and LLM orchestration can all stay in the same ecosystem.

So our working principle is:

> **FastAPI for the application/backend + Python AI pipeline + MongoDB/data layer + a simple vector store for Round 1.**

And I would keep the agent's first task as **Phase 0 audit**, not implementation. The project specification explicitly requires auditing the existing repository before major changes. 
