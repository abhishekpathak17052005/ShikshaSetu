# PHASE 3: NEXT STEPS

**Current Status:** ✅ Week 1 Day 1-2 Complete  
**Date:** August 27, 2026  
**Ready to Execute:** YES  

---

## WHAT'S DONE

### ✅ Week 1 Day 1-2 Deliverables

1. **3 Seed Scripts Created**
   - `seed_competencies.py` (6.7 KB)
   - `seed_learning_resources.py` (10.1 KB)
   - `seed_resource_mappings.py` (10.2 KB)

2. **8 Documentation Files**
   - PHASE_3_READY.md (quick reference)
   - PHASE_3_EXECUTION_GUIDE.md (step-by-step)
   - PHASE_3_WEEK1_STATUS.md (completion report)
   - PHASE_3_INDEX.md (documentation index)
   - Plus 4 pre-existing architecture docs

3. **Data Verified**
   - ✅ `igot_courses_enriched.csv` (68 courses)
   - ✅ `nssta_training_programmes.csv` (80 programmes)
   - ✅ `competency_taxonomy.csv` (42 competencies)
   - ✅ `course_competency_mapping.csv` (68 mappings)
   - ✅ `nssta_competency_mapping.csv` (46 mappings)

4. **Architecture Finalized**
   - ✅ 5-component scoring locked
   - ✅ Provider abstraction designed
   - ✅ API endpoints specified
   - ✅ Multi-gap support planned
   - ✅ Deduplication logic defined

---

## IMMEDIATE NEXT STEPS (Week 1 Day 3)

### Step 1: Setup Environment

```powershell
cd backend

# Activate virtual environment (if needed)
.\.venv\Scripts\activate

# Verify .env exists
type .env
```

Expected output:
```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=shikshasetu
```

### Step 2: Ensure MongoDB Running

```powershell
# Start MongoDB (if not running)
mongod --dbpath "C:\data\db"

# In another terminal, verify connection
mongosh "mongodb://localhost:27017"
```

Expected: `test>` prompt in mongosh

### Step 3: Execute Seed Scripts (In Order)

```powershell
# 1. Load competencies (42 docs)
python -m app.scripts.seed_competencies
# Output: "✅ Competencies seeded successfully!"
# Inserts: 42 documents

# 2. Load resources (148 docs)
python -m app.scripts.seed_learning_resources
# Output: "✅ Learning resources seeded successfully!"
# Inserts: 68 iGOT + 80 NSSTA

# 3. Load mappings (114 docs)
python -m app.scripts.seed_resource_mappings
# Output: "✅ Resource mappings seeded successfully!"
# Inserts: 68 iGOT + 46 NSSTA
```

### Step 4: Verify Data in MongoDB

```powershell
mongosh "mongodb://localhost:27017/shikshasetu"

# In mongosh shell:

# Check counts
db.competencies.countDocuments()              # → 42
db.learning_resources.countDocuments()        # → 148
db.learning_resource_mappings.countDocuments() # → 114

# Check sample data
db.competencies.findOne()
db.learning_resources.findOne()
db.learning_resource_mappings.findOne()

# Verify indexes
db.competencies.getIndexes()
db.learning_resources.getIndexes()
db.learning_resource_mappings.getIndexes()

# Exit
exit
```

### Step 5: Run Tests (Verify No Regressions)

```powershell
# Run all tests
pytest tests/ -v

# Expected: 139/139 passing
# If different, check for regressions
```

### Step 6: Verify Query Performance

```powershell
mongosh "mongodb://localhost:27017/shikshasetu"

# In mongosh shell:

# Query resources by provider
db.learning_resources.find({ provider: "IGOT" }).count()      # → 68
db.learning_resources.find({ provider: "NSSTA" }).count()     # → 80

# Query mappings by provider
db.learning_resource_mappings.find({ provider: "IGOT" }).count()   # → 68
db.learning_resource_mappings.find({ provider: "NSSTA" }).count()  # → 46

# Find resources for a competency
db.learning_resource_mappings.find({ competency_code: "C001" })

# Check mapping integrity
db.learning_resource_mappings.find().count()  # → 114 (no duplicates)

exit
```

---

## WEEK 1 DAY 4: CREATE MODELS & REPOSITORY

After data loading verified:

### 1. Create Learning Resources Module

```bash
mkdir backend/app/learning_resources
touch backend/app/learning_resources/__init__.py
```

### 2. Create Models (`models.py`)

Pydantic schemas for:
- `CompetencyReference` (nested in resources)
- `ResourceMetadata` (nested: duration_hours, difficulty, etc.)
- `ResourceSource` (nested: source_type, source_url, etc.)
- `LearningResource` (full document schema)
- `LearningResourceMapping` (full document schema)

### 3. Create Repository (`repository.py`)

Methods:
- `get_resources_by_competency(competency_code, provider=None)`
- `get_resource_details(resource_id)`
- `get_resources_by_provider(provider_name)`
- `search_resources(query, filters)`

### 4. Create Unit Tests

Test loading, querying, schema validation.

---

## WEEK 2 DAY 1-2: PROVIDER ABSTRACTION

### Create Provider Package

```bash
mkdir backend/app/learning_resources/providers
touch backend/app/learning_resources/providers/__init__.py
```

### Create Files

1. `base.py` - Abstract `LearningResourceProvider` class
2. `igot_provider.py` - `PrototypeIGOTProvider`
3. `nssta_provider.py` - `PrototypeNSSTAProvider`
4. `factory.py` - `ProviderFactory.get_provider()`

---

## WEEK 2 DAY 3-5: RECOMMENDATION ENGINE

### Create Recommendation Module

```bash
mkdir backend/app/recommendations
touch backend/app/recommendations/__init__.py
```

### Create Files

1. `engine.py` - `RecommendationEngine` with 5-component scoring
2. `schemas.py` - Request/response Pydantic models
3. `router.py` - FastAPI endpoints
4. `scoring.py` - Scoring formula implementation

### 3 API Endpoints

```
GET /api/v1/recommendations/me
  → Personalized recommendations for authenticated user

GET /api/v1/learning-resources
  → Browse all resources (paginated)

GET /api/v1/learning-resources/{resource_id}
  → Get resource details
```

---

## WEEK 3: TESTING & VERIFICATION

### Unit Tests

- `test_seed_competencies.py`
- `test_seed_learning_resources.py`
- `test_seed_resource_mappings.py`

### Integration Tests

- `test_recommendation_engine.py`
- `test_provider_factory.py`
- `test_repository.py`

### E2E Tests

- `test_recommendations_api.py`
- `test_learning_resources_api.py`

### Target

**159+ tests passing** (139 existing + 20 new)

---

## DECISION POINTS

If issues arise, refer to:

### If MongoDB Connection Fails
→ Check MONGODB_URI in .env
→ Verify mongod is running
→ Run: `mongosh "mongodb://localhost:27017"`

### If CSV Not Found
→ Verify in backend/ directory
→ Check file names exactly match

### If Script Says "Collection Already Has Documents"
→ Script will ask "Clear and reimport? (y/n)"
→ Answer `y` to proceed

### If Test Regression Detected
→ Do NOT modify existing tests
→ Check if seed script changed existing data
→ Revert seed and retry

### If Data Integrity Issue
→ Check orphaned references via mongosh
→ Verify all mapping resources exist
→ Verify all mapping competencies exist

---

## DOCUMENTATION TO REFERENCE

During execution, refer to:

1. **Quick Reference:** [PHASE_3_READY.md](PHASE_3_READY.md) (2 pages)
2. **Step-by-Step:** [PHASE_3_EXECUTION_GUIDE.md](PHASE_3_EXECUTION_GUIDE.md) (5 pages)
3. **Troubleshooting:** See "Troubleshooting" section in execution guide
4. **Architecture:** [PHASE_3_FINAL_ARCHITECTURE.md](PHASE_3_FINAL_ARCHITECTURE.md) (15 pages)
5. **Complete Index:** [PHASE_3_INDEX.md](PHASE_3_INDEX.md) (10 pages)

---

## SUCCESS CRITERIA

✅ **Week 1 Day 3 Complete When:**
- [ ] All 3 seed scripts execute without error
- [ ] 42 competencies in MongoDB
- [ ] 148 resources in MongoDB
- [ ] 114 mappings in MongoDB
- [ ] All indexes created
- [ ] 139/139 tests passing
- [ ] No regressions

✅ **Week 1 Day 4 Complete When:**
- [ ] Models created and imported
- [ ] Repository CRUD working
- [ ] Unit tests written
- [ ] 139/139 tests still passing

✅ **Week 2 Complete When:**
- [ ] Provider abstraction working
- [ ] Recommendation engine scoring all 5 components
- [ ] 3 API endpoints working
- [ ] 150+ tests passing

✅ **Week 3 Complete When:**
- [ ] 159+ tests passing
- [ ] E2E tests passing
- [ ] Example recommendations showing scoring breakdown
- [ ] Final verification report ready

---

## QUICK COMMAND REFERENCE

```powershell
# Navigate to backend
cd backend

# Run seed scripts (in order)
python -m app.scripts.seed_competencies
python -m app.scripts.seed_learning_resources
python -m app.scripts.seed_resource_mappings

# Run tests
pytest tests/ -v

# Start backend
uvicorn app.main:app --reload

# Connect to MongoDB
mongosh "mongodb://localhost:27017/shikshasetu"

# Check document counts (in mongosh)
db.competencies.countDocuments()
db.learning_resources.countDocuments()
db.learning_resource_mappings.countDocuments()
```

---

## CURRENT STATE

**Ready to Execute:**
- ✅ All seed scripts in place
- ✅ All CSVs available
- ✅ MongoDB configured
- ✅ Tests verified (139/139 baseline)
- ✅ Documentation complete

**Next Action:**
→ Execute: `python -m app.scripts.seed_competencies`

**Timeline:**
- Week 1 Day 3-4: Data loading & models
- Week 2 Day 1-5: Provider & engine
- Week 3 Day 1-5: Tests & verification

**Target:** 159+ tests passing by end of Week 3

---

**Prepared by:** Kiro  
**Date:** August 27, 2026  
**Status:** ✅ READY TO EXECUTE
