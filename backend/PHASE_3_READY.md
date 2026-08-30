# PHASE 3: READY TO CODE

**Date:** August 27, 2026  
**Status:** ✅ All planning complete - implementation can begin immediately  
**Baseline:** 139/139 tests passing  
**Target:** 159+ tests passing (139 + 20 new)  

---

## WHAT YOU HAVE

### Data Files (5 canonical CSV sources)

```
✅ igot_courses_enriched.csv          (68 iGOT courses)
✅ nssta_training_programmes.csv      (80 NSSTA programmes)
✅ course_competency_mapping.csv      (68 iGOT → competency)
✅ nssta_competency_mapping.csv       (46 NSSTA → competency)
✅ competency_taxonomy.csv            (42 competencies)
```

### Architecture Decisions

```
✅ 5-component scoring formula (40% + 25% + 20% + 10% + 5%)
✅ Configurable weights (not hardcoded)
✅ Deterministic ranking (no LLM in selection)
✅ Provider abstraction (IGOT + NSSTA swappable)
✅ Multi-gap support (users with 2+ gaps)
✅ Deduplication logic (same resource, different gaps)
✅ NO invented metadata (use neutral 0.5 for unknown)
✅ NO engagement metrics (wait for real data)
```

### Implementation Plan

```
Week 1: Foundation
  - Seed scripts (CSV → MongoDB)
  - Create collections (learning_resources, learning_resource_mappings)
  - Load 148 resources + 114 mappings + 42 competencies
  - Create indexes
  - Verify data queryable

Week 2: Engine & API
  - Provider abstraction (PrototypeIGOT, PrototypeNSSTA)
  - Recommendation engine (5-component scoring)
  - API endpoints (3 routes)
  - Multi-gap support
  - Deduplication

Week 3: Tests & Verification
  - Unit tests (scoring formula)
  - Integration tests (engine)
  - E2E tests (API)
  - Regression tests (139 existing pass)
  - Example recommendations (Statistical Officer)
  - Final verification report
```

---

## IMMEDIATE NEXT STEPS

### 1. Create Seed Scripts (Week 1, Day 1-2)

Files to create:
```
app/scripts/seed_competencies.py
app/scripts/seed_learning_resources.py
app/scripts/seed_resource_mappings.py
```

Each script:
- Reads CSV (canonical source)
- Validates data
- Transforms to MongoDB schema
- Handles NULL/empty fields
- Creates indexes
- Returns count of inserted documents

### 2. Create Models & Schemas (Week 1, Day 2)

Files to create:
```
app/learning_resources/__init__.py
app/learning_resources/models.py
app/learning_resources/repository.py
```

Models:
- `LearningResource` (148 documents)
- `LearningResourceMapping` (114 documents)
- `CompetencyReference` (nested in resources)
- `ResourceMetadata`, `ResourceSource` (nested)

Repository:
- `get_resources_by_competency(competency_code, provider=None)`
- `get_resource_details(resource_id)`
- CRUD operations

### 3. Load Data (Week 1, Day 3)

Command:
```bash
cd backend
python -m app.scripts.seed_competencies
python -m app.scripts.seed_learning_resources
python -m app.scripts.seed_resource_mappings
```

Verify:
```bash
# Check MongoDB
db.learning_resources.count_documents()          # Should be 148
db.learning_resource_mappings.count_documents()  # Should be 114
db.competencies.count_documents()                # Should be 42
```

### 4. Create Provider Abstraction (Week 2, Day 1)

Files to create:
```
app/learning_resources/providers/__init__.py
app/learning_resources/providers/base.py
app/learning_resources/providers/igot_provider.py
app/learning_resources/providers/nssta_provider.py
app/learning_resources/providers/factory.py
```

### 5. Create Recommendation Engine (Week 2, Day 2)

Files to create:
```
app/recommendations/__init__.py
app/recommendations/engine.py
app/recommendations/schemas.py
app/recommendations/router.py
```

### 6. Create API Endpoints (Week 2, Day 3)

Routes:
```
GET /api/v1/recommendations/me
GET /api/v1/learning-resources
GET /api/v1/learning-resources/{resource_id}
```

### 7. Tests & Verification (Week 3)

Files to create:
```
tests/test_recommendations_engine.py
tests/test_recommendations_api.py
tests/test_provider_factory.py
```

---

## NUMBERS TO TRACK

### Data

| Item | Count | Source |
|------|-------|--------|
| iGOT courses | 68 | igot_courses_enriched.csv |
| NSSTA programmes | 80 | nssta_training_programmes.csv |
| Competencies | 42 | competency_taxonomy.csv |
| iGOT mappings | 68 | course_competency_mapping.csv |
| NSSTA mappings | 46 | nssta_competency_mapping.csv |
| **Total resources** | **148** | |
| **Total mappings** | **114** | |
| **Unmapped** | **40** | (NSSTA programmes, don't force-map) |

### Tests

| Checkpoint | Target | Status |
|---|---|---|
| After Week 1 | 139 passing (no new tests yet) | Not started |
| After Week 2 | 150+ passing (139 + engine tests) | Not started |
| After Week 3 | 159+ passing (139 + 20 new tests) | Not started |

---

## KEY IMPLEMENTATION RULES

### ✅ DO

- ✅ Use CSV files as canonical source (never modify)
- ✅ Build reusable seed scripts (for future dataset updates)
- ✅ Preserve all provenance fields (source_url, extraction_note, etc.)
- ✅ Mark NSSTA as TENTATIVE (calendar not confirmed)
- ✅ Create comprehensive indexes for performance
- ✅ Handle NULL/empty fields gracefully
- ✅ Use neutral values (0.5) for unknown metadata
- ✅ Test determinism (same input = same output always)

### ❌ DON'T

- ❌ Modify any CSV source files
- ❌ Mix seed_56 dataset with enriched_68
- ❌ Load both CSV and JSON formats
- ❌ Invent missing fields (descriptions, prerequisites, etc.)
- ❌ Fabricate completion rates or ratings
- ❌ Claim live availability (seats, enrollment)
- ❌ Force-map unmapped NSSTA programmes
- ❌ Use LLM to select recommendations (only explanation later)

---

## SUCCESS CRITERIA

### Week 1: Foundation
- ✅ 148 learning_resources in MongoDB
- ✅ 114 learning_resource_mappings in MongoDB
- ✅ All indexes created
- ✅ Resources queryable by competency
- ✅ Seed scripts reusable
- ✅ 139 existing tests still passing

### Week 2: Engine & API
- ✅ Provider abstraction working
- ✅ Recommendation engine scoring all 5 components
- ✅ API endpoints returning recommendations
- ✅ Multi-gap support verified
- ✅ Deduplication working
- ✅ 150+ tests passing

### Week 3: Verification
- ✅ 159+ tests passing
- ✅ Example recommendations for Statistical Officer
- ✅ Scoring breakdown documented
- ✅ Determinism verified (same user, 3 calls = identical output)
- ✅ No regressions (139 existing tests pass)
- ✅ Final verification report

---

## READY TO START DEVELOPMENT

All decisions finalized:
- ✅ Data integration strategy clear
- ✅ MongoDB schema defined
- ✅ Seed scripts designed
- ✅ API endpoints specified
- ✅ Recommendation formula locked
- ✅ Testing strategy outlined
- ✅ Week 1-3 breakdown complete

**Start with Week 1 Day 1:** Create `app/scripts/seed_competencies.py`

