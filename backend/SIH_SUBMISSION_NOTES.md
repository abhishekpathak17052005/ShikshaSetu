# ShikshaSetu - SIH Round 1 Submission Notes

## Project Status: Prototype-Ready ✅

This backend demonstrates the **core recommendation engine for PS 26101**: Employee skills assessment, gap identification, and personalized learning recommendations.

---

## What Works (Verified)

### Loop 1: Skill Intelligence
```
Employee Registration
    ↓
Capability Assessment (MCQ)
    ↓
Competency Profile Updated
    ↓
Skill Gap Calculation
    ↓
Learning Recommendation (38 recommendations)
```
✅ **Verified with real HTTP testing**

### Loop 2: Learning Path
```
Upload Learning Material
    ↓
AI-Generated MCQ (Gemini)
    ↓
Quiz Submission
    ↓
Evidence Creation
    ↓
Competency Update
    ↓
Skill Gap Recalculation
```
✅ **Unit tests passing (164/164)**

### Recommendation Engine
- ✅ **Deterministic 5-component scoring:** competency_match (40%) + gap_priority (25%) + role_match (20%) + difficulty_match (10%) + prerequisite_match (5%)
- ✅ **Real resource ranking:** 38 recommendations from 148 seeded resources
- ✅ **Provider separation:** iGOT (63) and NSSTA (85) resources properly classified
- ✅ **Security enforced:** JWT authentication required, unauthenticated requests rejected

---

## Data & Limitations (Transparent)

### Competency Framework
- **Active:** 33 competencies across 4 domains
- **Limitation:** Original taxonomy had 42 items; 9 are sub-competencies (Phase 2 enhancement)
- **Example:** "Machine Learning Fundamentals" is treated as a learning objective within "AI/ML" competency

### Learning Resources
- **Seeded:** 148 resources
  - iGOT: 63 courses
  - NSSTA: 85 training programmes
- **NULL course_id:** 5 NSSTA resources (proto-competencies without firm enrollment links)

### Mappings
- **Active:** 88 resource-to-competency mappings
  - iGOT: 42 (26 skipped due to sub-competencies)
  - NSSTA: 46 (100% coverage)
- **Limitation:** Sub-competency mappings (e.g., TECH-AIML-ML) require competency framework extension

---

## Key Metrics (Actual)

| Metric | Value | Notes |
|--------|-------|-------|
| Competencies | 33 | Simplified framework for prototype |
| Resources | 148 | 100% seeded and indexed |
| Active Mappings | 88 | 42 iGOT + 46 NSSTA |
| Test Recommendations | 38 | Generated for single test user |
| Top Score | 0.645 | Deterministically calculated |
| Unit Tests | 164/164 | ✅ All passing |
| HTTP E2E Tests | 8/8 | ✅ All passing |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Service │  │ Assessment   │  │  Competency  │      │
│  │  (JWT)       │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Skill Gap   │  │Recommendation│  │ Learning     │      │
│  │   Engine     │  │   Engine     │  │  Resources   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    MongoDB                                   │
│  (Users, Competencies, Resources, Mappings, Evidence)      │
└─────────────────────────────────────────────────────────────┘
```

### Core Technologies
- **Framework:** FastAPI (Python)
- **Database:** MongoDB
- **AI/LLM:** Gemini (for MCQ generation)
- **Auth:** JWT
- **Scoring:** Deterministic algorithm (no LLM-based scoring)

---

## Real API Response Example

### GET /api/v1/recommendations/me
```json
{
  "user_id": "6a906491890e6cc43263937e",
  "role": "STATISTICAL_OFFICER",
  "total_recommendations": 38,
  "recommendations": [
    {
      "rank": 1,
      "resource": {
        "resource_id": "NSSTA-NSSTA-PROT-033",
        "title": "Data Ethics, Governance, and Quality in a Changing Data Ecosystem",
        "provider": "NSSTA",
        "resource_type": "TRAINING_PROGRAMME"
      },
      "provider": "NSSTA",
      "competency_code": "STAT_DATA_QUALITY_FRAMEWORKS",
      "score": 0.645,
      "explanation": {
        "summary": "Your STAT_DATA_QUALITY_FRAMEWORKS competency is 0.0/5.0 while your role requires 4.0/5.0...",
        "score_breakdown": [
          {"name": "competency_match", "weight": 0.4, "score": 0.85, "value": 0.34},
          {"name": "gap_priority", "weight": 0.25, "score": 0.8, "value": 0.2},
          {"name": "role_match", "weight": 0.2, "score": 0.9, "value": 0.18},
          {"name": "difficulty_match", "weight": 0.1, "score": 0.75, "value": 0.075},
          {"name": "prerequisite_match", "weight": 0.05, "score": 0.5, "value": 0.025}
        ]
      }
    }
  ]
}
```

---

## Testing & Verification

### Automated Tests
```bash
pytest -v
# Result: 164 passed, 4 skipped, 35 warnings
```

### Manual E2E Testing (Postman Style)
```
1. Register user          ✅ HTTP 201
2. Login                  ✅ HTTP 200 (JWT)
3. Get competencies       ✅ HTTP 200 (33 items)
4. Calculate skill gaps   ✅ HTTP 200 (8 gaps)
5. Get recommendations    ✅ HTTP 200 (38 items)
6. Verify MongoDB data    ✅ Resource exists
7. Test determinism       ✅ Identical results
8. Security (no auth)     ✅ HTTP 401 rejected
```

### Determinism Verification
Called `/recommendations/me` twice with unchanged data:
- **Result:** Identical resource order, identical scores ✅

---

## What's NOT Included (Honest Gaps)

### Not in This Phase
- ❌ Live iGOT API integration (Phase 4)
- ❌ Live NSSTA API integration (Phase 4)
- ❌ Government SSO (not scope)
- ❌ Production deployment architecture
- ❌ Enterprise security hardening
- ❌ Sub-competency framework
- ❌ Multi-language support

### For Future Enhancement
- 📋 Complete 42-item competency taxonomy
- 📋 Sub-competency relationships
- 📋 Real-time provider data sync
- 📋 Advanced prerequisite tracking
- 📋 Adaptive difficulty adjustment

---

## How to Run

### Start Backend
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### Seed Data
```bash
python -m app.scripts.seed_framework
python -m app.scripts.seed_learning_resources
python -m app.scripts.seed_resource_mappings
```

### Run Tests
```bash
pytest -v
```

### Manual Testing (Postman)
1. POST /api/v1/auth/register
2. POST /api/v1/auth/login
3. GET /api/v1/competencies
4. GET /api/v1/skill-gaps/me
5. GET /api/v1/recommendations/me

---

## Key Achievements

✅ **Functional recommendation engine** with 38 real recommendations from seeded data
✅ **Deterministic scoring** proven across multiple API calls
✅ **Security controls** working (JWT required)
✅ **Integration ready** - APIs can be called from frontend
✅ **Well-tested** - 164/164 unit tests passing
✅ **Transparent limitations** - Data gaps clearly documented

---

## For SIH Judges

**This prototype demonstrates:**
1. ✅ Core skill gap detection algorithm
2. ✅ Personalized learning recommendation system
3. ✅ Integration with real iGOT and NSSTA resource catalogs (seeded)
4. ✅ Deterministic, reproducible scoring
5. ✅ RESTful API suitable for frontend integration

**Not claimed:**
- ❌ Production readiness
- ❌ Real-time API integration
- ❌ Complete 42-competency framework
- ❌ Enterprise deployment

---

**Submission Date:** August 2026
**Status:** Prototype-Ready for SIH Round 1
**Team:** ShikshaSetu Backend
