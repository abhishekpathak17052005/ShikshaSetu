# PHASE 3: COMPLETE INDEX

**Status:** ✅ WEEK 1 READY TO EXECUTE  
**Date:** August 27, 2026  
**Baseline:** 139/139 tests passing  
**Target:** 159+ tests passing  

---

## QUICK START

### For Immediate Execution (Week 1 Day 3)

Start here: **[PHASE_3_EXECUTION_GUIDE.md](PHASE_3_EXECUTION_GUIDE.md)**

```powershell
cd backend
python -m app.scripts.seed_competencies
python -m app.scripts.seed_learning_resources
python -m app.scripts.seed_resource_mappings
pytest tests/ -v  # Verify 139/139 passing
```

### For Architecture Review

Start here: **[PHASE_3_FINAL_ARCHITECTURE.md](PHASE_3_FINAL_ARCHITECTURE.md)**

Covers:
- 5-component scoring formula (40% + 25% + 20% + 10% + 5%)
- Provider abstraction (IGOT, NSSTA, Factory)
- API endpoints (3 routes)
- Multi-gap support
- Deduplication logic
- Deterministic ranking

### For Implementation Details

Start here: **[PHASE_3_IMPLEMENTATION_PLAN.md](PHASE_3_IMPLEMENTATION_PLAN.md)**

Covers:
- Week 1-3 breakdown
- Seed script pseudocode
- Task breakdown
- Success criteria

---

## DOCUMENTATION FILES

### Planning & Status

| File | Purpose | Read Time |
|------|---------|-----------|
| **PHASE_3_WEEK1_STATUS.md** | Week 1 completion report | 5 min |
| **PHASE_3_READY.md** | Quick reference guide | 3 min |
| **PHASE_3_QUICK_SUMMARY.md** | One-page overview | 2 min |

### Architecture & Design

| File | Purpose | Read Time |
|------|---------|-----------|
| **PHASE_3_FINAL_ARCHITECTURE.md** | Complete architecture (5-component) | 15 min |
| **PHASE_3_RECOMMENDATION_ENGINE_AUDIT.md** | Detailed engine audit | 20 min |
| **PHASE_3_DATA_AUDIT.md** | Data analysis & validation | 15 min |

### Implementation

| File | Purpose | Read Time |
|------|---------|-----------|
| **PHASE_3_EXECUTION_GUIDE.md** | Step-by-step execution | 10 min |
| **PHASE_3_IMPLEMENTATION_PLAN.md** | Week 1-3 plan with pseudocode | 20 min |
| **PHASE_3_IMPLEMENTATION_TASKS.md** | Specific task breakdowns | 15 min |

---

## SEED SCRIPTS (Ready to Execute)

### 1. seed_competencies.py

**Location:** `backend/app/scripts/seed_competencies.py`  
**Size:** 6.7 KB  
**Executes:** Loads `competency_taxonomy.csv` → `competencies` collection

**What it does:**
- Reads 42 competencies from CSV
- Transforms to MongoDB schema
- Creates 3 indexes (code, domain, framework_status)
- Handles NULL/empty values
- Returns count of inserted documents

**Run:**
```powershell
python -m app.scripts.seed_competencies
```

**Expected output:**
```
✅ Competencies seeded successfully!
📊 Summary:
  Total competencies: 42
  Top-level: 30
  Subskills: 12
  Domains: (breakdown by domain)
```

---

### 2. seed_learning_resources.py

**Location:** `backend/app/scripts/seed_learning_resources.py`  
**Size:** 10.1 KB  
**Executes:** Loads `igot_courses_enriched.csv` + `nssta_training_programmes.csv` → `learning_resources` collection

**What it does:**
- Reads 68 iGOT courses from CSV
- Reads 80 NSSTA programmes from CSV
- Transforms to unified schema with `provider` field
- Parses duration strings:
  - "2h 42m" → 2.7 hours
  - "5 day(s)" → 40 hours (8h/day)
- Creates 3 indexes (provider, status, resource_id)
- Marks NSSTA as TENTATIVE

**Run:**
```powershell
python -m app.scripts.seed_learning_resources
```

**Expected output:**
```
✅ Learning resources seeded successfully!
📊 Summary:
  iGOT courses: 68
  NSSTA programmes: 80
  Total: 148
  iGOT by difficulty: (breakdown)
```

---

### 3. seed_resource_mappings.py

**Location:** `backend/app/scripts/seed_resource_mappings.py`  
**Size:** 10.2 KB  
**Executes:** Links resources to competencies → `learning_resource_mappings` collection

**What it does:**
- Reads 68 iGOT mappings from CSV
- Reads 46 NSSTA mappings from CSV
- Resolves ObjectIds from MongoDB collections
- Links resource_id (FK) → learning_resources._id
- Links competency_id (FK) → competencies._id
- Creates 4 indexes (resource_id, competency_code, provider, composite unique)
- Validates all references

**Run:**
```powershell
python -m app.scripts.seed_resource_mappings
```

**Expected output:**
```
✅ Resource mappings seeded successfully!
📊 Summary:
  iGOT mappings: 68
  NSSTA mappings: 46
  Total: 114
```

---

## DATA FILES

All CSV files are in `backend/` directory.

### Source Data (DO NOT MODIFY)

| File | Records | Purpose |
|------|---------|---------|
| `igot_courses_enriched.csv` | 68 | iGOT course catalogue |
| `nssta_training_programmes.csv` | 80 | NSSTA programme catalogue |
| `competency_taxonomy.csv` | 42 | Competency framework |
| `course_competency_mapping.csv` | 68 | iGOT → competency links |
| `nssta_competency_mapping.csv` | 46 | NSSTA → competency links |

### Supporting Files (Reference Only)

| File | Purpose |
|------|---------|
| `source_registry.csv` | Provenance/audit reference (not loaded in Phase 3) |
| `igot_courses_seed_56.csv` | Original seed (superseded by enriched_68) |
| `igot_courses_enriched.json` | JSON format (use CSV instead) |
| `nssta_training_programmes.json` | JSON format (use CSV instead) |

---

## MONGODB COLLECTIONS (Post-Execution)

### competencies (42 documents)

```
Collection: competencies
Documents: 42
Indexes:
  - code (unique) → lookup by competency code
  - domain → query by domain
  - framework_status → query by status

Schema:
{
  code: "C001",
  name: "Competency Name",
  domain: "Domain",
  parent_competency_code: "C000" or null,
  is_subskill: true/false,
  level_definitions: { "1": "...", "2": "...", ... },
  framework_status: "prototype",
  ...
}
```

---

### learning_resources (148 documents)

```
Collection: learning_resources
Documents: 148
  - 68 IGOT courses (provider: "IGOT")
  - 80 NSSTA programmes (provider: "NSSTA")
Indexes:
  - provider → query by IGOT|NSSTA
  - status → query by status
  - resource_id (unique) → lookup by ID

Schema:
{
  resource_id: "IGOT-12345" or "NSSTA-67890",
  provider: "IGOT" or "NSSTA",
  resource_type: "COURSE" or "TRAINING_PROGRAMME",
  title: "Course Title",
  metadata: {
    duration_hours: 2.7 or 40,
    difficulty: "BASIC" or "INTERMEDIATE" or null,
    target_roles: [],
    prerequisites: []
  },
  source: {
    source_type: "GOVERNMENT_PUBLICATION",
    source_url: "...",
    verification_status: "VERIFIED" or "TENTATIVE"
  },
  ...
}
```

---

### learning_resource_mappings (114 documents)

```
Collection: learning_resource_mappings
Documents: 114
  - 68 IGOT mappings
  - 46 NSSTA mappings
Indexes:
  - resource_id → query by resource
  - competency_code → query by competency
  - provider → query by provider
  - (resource_id, competency_code) unique → prevent duplicates

Schema:
{
  resource_id: ObjectId,        # FK to learning_resources
  competency_id: ObjectId,      # FK to competencies
  competency_code: "C001",
  provider: "IGOT" or "NSSTA",
  confidence: 0.5-1.0,
  mapping_quality: {
    content_alignment: 0.5-1.0,
    accuracy_score: null,
    recency_score: null
  },
  ...
}
```

---

## TEST TARGETS

### Before Execution (Baseline)

```
139 tests passing (Phase 1-2)
```

### After Week 1 (Data Loading)

```
139 tests passing (no regressions)
```

### After Week 2 (Provider & Engine)

```
150+ tests passing (139 + engine tests)
```

### After Week 3 (API & Verification)

```
159+ tests passing (139 + 20 new tests)
```

---

## EXECUTION TIMELINE

### Week 1 (Data Foundation)

**Day 1-2:** ✅ Create seed scripts (COMPLETE)
**Day 3:** Execute seed scripts
**Day 4:** Create models & repository, verify tests

### Week 2 (Provider & Engine)

**Day 1-2:** Provider abstraction (IGOT, NSSTA, Factory)
**Day 3-4:** Recommendation engine with 5-component scoring
**Day 5:** API endpoints (3 routes)

### Week 3 (Testing & Verification)

**Day 1-2:** Unit & integration tests
**Day 3-4:** E2E tests, example recommendations
**Day 5:** Final verification report

---

## KEY DECISIONS (LOCKED)

✅ **5-Component Scoring** (not 6)
- Removed engagement_quality (5%)
- Rationale: No reliable learner telemetry yet

✅ **Configurable Weights** (not hardcoded)
- Store in RecommendationScoringConfig class
- Rationale: Flexible for future tuning

✅ **Deterministic Ranking** (no LLM selection)
- Formula-based scoring only
- LLM can explain results post-hoc
- Rationale: Auditability

✅ **Unified Collections** (not separate IGOT/NSSTA)
- One learning_resources collection (provider field)
- One learning_resource_mappings collection
- Rationale: Reduces duplication, easier querying

✅ **CSV-Based Seeding** (not manual)
- Reusable seed scripts
- Rationale: Maintainability for future updates

✅ **Neutral Metadata** (not optimistic)
- Missing fields → 0.5, not 1.0
- Rationale: Avoid bias

✅ **No Force-Mapping** (40 NSSTA unmapped)
- Only 46 of 80 NSSTA have mappings
- Unmapped remain browseable
- Rationale: Data integrity

---

## VERIFICATION CHECKLIST

After executing all seed scripts:

- [ ] MongoDB connection working
- [ ] competencies collection: 42 documents
- [ ] learning_resources collection: 148 documents
- [ ] learning_resource_mappings collection: 114 documents
- [ ] All indexes created
- [ ] No orphaned references
- [ ] No duplicate resource IDs
- [ ] No duplicate (resource_id, competency_code) pairs
- [ ] pytest → 139/139 passing
- [ ] No regressions in existing tests
- [ ] Data queryable via mongosh

---

## COMMON COMMANDS

### Run Seed Scripts

```powershell
cd backend
python -m app.scripts.seed_competencies
python -m app.scripts.seed_learning_resources
python -m app.scripts.seed_resource_mappings
```

### Verify MongoDB

```powershell
mongosh "mongodb://localhost:27017/shikshasetu"

# In mongosh shell
db.competencies.countDocuments()
db.learning_resources.countDocuments()
db.learning_resource_mappings.countDocuments()
```

### Run Tests

```powershell
cd backend
pytest tests/ -v
```

### Check Indexes

```powershell
# In mongosh shell
db.competencies.getIndexes()
db.learning_resources.getIndexes()
db.learning_resource_mappings.getIndexes()
```

---

## TROUBLESHOOTING

### "MongoDB connection refused"
→ Ensure MongoDB running: `mongod`

### "CSV file not found"
→ Verify in backend/ directory: `ls -la *.csv`

### "Collection already has documents"
→ Script asks to clear. Answer `y` to reimport.

### "Competency not found"
→ Run seed_competencies FIRST

### "Resource not found"
→ Run seed_learning_resources BEFORE seed_resource_mappings

---

## NEXT STEPS

1. **Execute seed scripts** (Week 1 Day 3)
2. **Verify data** in MongoDB (Week 1 Day 3)
3. **Create models** (Week 1 Day 4)
4. **Create repository** (Week 1 Day 4)
5. **Verify tests** (Week 1 Day 4)

Then proceed to Week 2: Provider & Engine

---

**Last Updated:** August 27, 2026  
**Status:** ✅ READY TO EXECUTE  
**By:** Kiro
