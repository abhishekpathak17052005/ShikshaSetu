# PHASE 3: EXECUTION GUIDE

**Status:** ✅ Ready to Execute  
**Date:** August 27, 2026  
**Target:** Week 1 Data Loading Complete  

---

## WHAT'S READY

### ✅ Seed Scripts Created

```
backend/app/scripts/
  ├── seed_competencies.py           (loads competency_taxonomy.csv → 42 docs)
  ├── seed_learning_resources.py     (loads iGOT + NSSTA → 148 docs)
  └── seed_resource_mappings.py      (links resources to competencies → 114 docs)
```

### ✅ Data Files Available

```
backend/
  ├── competency_taxonomy.csv              (42 competencies)
  ├── igot_courses_enriched.csv            (68 iGOT courses)
  ├── nssta_training_programmes.csv        (80 NSSTA programmes)
  ├── course_competency_mapping.csv        (68 mappings)
  └── nssta_competency_mapping.csv         (46 mappings)
```

### ✅ Architecture Ready

```
MongoDB
  ├── competencies                    (42 docs, unique index on code)
  ├── learning_resources              (148 docs, unique index on resource_id)
  └── learning_resource_mappings      (114 docs, composite unique index)
```

---

## EXECUTION STEPS

### Step 1: Navigate to Backend Directory

```powershell
cd backend
```

### Step 2: Verify Environment Variables

Check `.env` file has MongoDB connection:

```
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=shikshasetu
```

If using different values, ensure MongoDB is running at that URI.

### Step 3: Run Seed Scripts in Order

```powershell
# 1. Seed competencies (42 docs)
python -m app.scripts.seed_competencies

# 2. Seed learning resources (148 docs)
python -m app.scripts.seed_learning_resources

# 3. Seed mappings (114 docs)
python -m app.scripts.seed_resource_mappings
```

### Step 4: Verify Data in MongoDB

```powershell
# Using mongosh CLI
mongosh "mongodb://localhost:27017/shikshasetu"

# In mongosh shell:
db.competencies.countDocuments()              # Should be 42
db.learning_resources.countDocuments()        # Should be 148
db.learning_resource_mappings.countDocuments() # Should be 114

# View sample data
db.competencies.findOne()
db.learning_resources.findOne()
db.learning_resource_mappings.findOne()

# Check indexes
db.competencies.getIndexes()
db.learning_resources.getIndexes()
db.learning_resource_mappings.getIndexes()
```

### Step 5: Run Existing Tests

Verify no regressions:

```powershell
pytest tests/ -v
```

Expected: **139/139 passing** (same as before seeding)

---

## WHAT EACH SCRIPT DOES

### seed_competencies.py

**Input:** `competency_taxonomy.csv` (42 rows)

**Process:**
1. Parse CSV
2. Transform to MongoDB document schema
3. Insert to `competencies` collection
4. Create indexes:
   - `code` (unique)
   - `domain` (query by domain)
   - `framework_status` (query by status)

**Output:**
- 42 documents in `competencies`
- Summary: Top-level vs subskills, domain breakdown

**Schema:**
```json
{
  "code": "string",
  "name": "string",
  "domain": "string",
  "parent_competency_code": "string or null",
  "is_subskill": "boolean",
  "description": "string",
  "level_definitions": {
    "1": "string", "2": "string", ..., "5": "string"
  },
  "related_skills": ["string"],
  "related_roles": ["string"],
  "framework_status": "string",
  "source": "competency_taxonomy.csv",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### seed_learning_resources.py

**Input:**
- `igot_courses_enriched.csv` (68 rows)
- `nssta_training_programmes.csv` (80 rows)

**Process:**
1. Parse both CSVs
2. Transform iGOT courses:
   - Add `provider: "IGOT"`
   - Parse duration (e.g., "2h 42m" → 2.7)
   - Extract difficulty level
3. Transform NSSTA programmes:
   - Add `provider: "NSSTA"`
   - Parse duration (e.g., "5 day(s)" → 40)
   - Mark as TENTATIVE
4. Insert 148 total documents
5. Create indexes

**Output:**
- 148 documents in `learning_resources`
- Summary: 68 iGOT + 80 NSSTA, difficulty breakdown

**Schema:**
```json
{
  "resource_id": "IGOT-{id} or NSSTA-{id}",
  "provider": "IGOT or NSSTA",
  "resource_type": "COURSE or TRAINING_PROGRAMME",
  "title": "string",
  "metadata": {
    "duration_hours": "float or null",
    "difficulty": "string or null",
    "target_roles": [],
    "prerequisites": []
  },
  "competencies": [],
  "source": {
    "source_type": "GOVERNMENT_PUBLICATION",
    "source_url": "string",
    "source_document": "string",
    "verification_status": "VERIFIED or TENTATIVE"
  },
  "provider_specific": {
    "course_id or programme_id": "string",
    "... provider-specific fields ..."
  },
  "status": "ACTIVE",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### seed_resource_mappings.py

**Input:**
- `course_competency_mapping.csv` (68 rows)
- `nssta_competency_mapping.csv` (46 rows)

**Process:**
1. Parse both CSVs
2. Build lookup maps:
   - iGOT courses by course_id → MongoDB ObjectId
   - NSSTA programmes by programme_id → MongoDB ObjectId
   - Competencies by code → MongoDB ObjectId
3. Link each mapping:
   - resource_id (FK to learning_resources)
   - competency_id (FK to competencies)
   - confidence score
   - mapping_quality metrics
4. Insert 114 documents
5. Create indexes including composite unique (resource_id, competency_code)

**Output:**
- 114 documents in `learning_resource_mappings`
- Summary: 68 iGOT + 46 NSSTA

**Schema:**
```json
{
  "resource_id": "ObjectId (FK)",
  "competency_id": "ObjectId (FK)",
  "competency_code": "string",
  "competency_name": "string",
  "provider": "IGOT or NSSTA",
  "mapping_type": "DERIVED",
  "confidence": "float (0.0-1.0)",
  "evidence": "string",
  "mapping_quality": {
    "content_alignment": "float",
    "accuracy_score": "float or null",
    "recency_score": "float or null"
  },
  "verified_at": "datetime or null",
  "verified_by": "string or null",
  "created_at": "datetime"
}
```

---

## DATA INTEGRITY CHECKS

### After All Scripts Run

```powershell
# 1. Count documents
db.competencies.countDocuments()              # = 42
db.learning_resources.countDocuments()        # = 148
db.learning_resource_mappings.countDocuments() # = 114

# 2. Check no duplicates (resource_id)
db.learning_resources.countDocuments({}, { hint: { resource_id: 1 } })
# Should equal 148 (no duplicates)

# 3. Check unique mappings per resource-competency
db.learning_resource_mappings.aggregate([
  { $group: { _id: { resource: "$resource_id", comp: "$competency_code" }, count: { $sum: 1 } } },
  { $match: { count: { $gt: 1 } } }
])
# Should return empty (no duplicates)

# 4. Verify all mappings point to existing resources
db.learning_resource_mappings.aggregate([
  { $match: { resource_id: { $nin: db.learning_resources.find({}, { _id: 1 }).map(x => x._id) } } }
])
# Should return empty (all mappings valid)

# 5. Verify all mappings point to existing competencies
db.learning_resource_mappings.aggregate([
  { $match: { competency_id: { $nin: db.competencies.find({}, { _id: 1 }).map(x => x._id) } } }
])
# Should return empty (all mappings valid)
```

---

## TROUBLESHOOTING

### Issue: "MongoDB connection refused"

**Solution:**
1. Ensure MongoDB is running: `mongod`
2. Check connection string in `.env`
3. Verify database name matches

### Issue: "CSV file not found"

**Solution:**
1. Ensure you're in `backend/` directory
2. Verify CSV files exist: `ls -la *.csv` (or `dir *.csv` on Windows)
3. Check file names exactly match

### Issue: "Collection already has documents"

**Solution:**
1. Script will ask to clear and reimport
2. Type `y` to proceed with reimport
3. Or manually clear: `db.collection.deleteMany({})`

### Issue: "Competency code not found"

**Solution:**
1. Run `seed_competencies` first
2. Verify competency_taxonomy.csv is not corrupted
3. Check competency_id column in mapping CSVs matches

### Issue: "Resource ID not found"

**Solution:**
1. Run `seed_learning_resources` before `seed_resource_mappings`
2. Verify resource IDs in mapping CSVs match resource IDs loaded

---

## VALIDATION CHECKLIST

- [ ] MongoDB running on configured URI
- [ ] Backend .env configured
- [ ] All 5 CSV files present in backend/
- [ ] Run seed_competencies.py → 42 docs inserted
- [ ] Run seed_learning_resources.py → 148 docs inserted
- [ ] Run seed_resource_mappings.py → 114 docs inserted
- [ ] Run pytest → 139/139 passing (no regressions)
- [ ] Verify MongoDB documents via mongosh
- [ ] Check all indexes created
- [ ] Confirm no orphaned references

---

## NEXT STEPS (Week 1 Day 2-3)

After data loading verified:

1. **Create Collection Models** (`app/learning_resources/models.py`)
   - Pydantic schemas for validation
   - CompetencyReference, ResourceMetadata, ResourceSource

2. **Create Repository Layer** (`app/learning_resources/repository.py`)
   - CRUD operations
   - Query by competency
   - Query by provider
   - Search operations

3. **Unit Tests**
   - Test load operations
   - Test query operations
   - Verify data integrity

---

## CURRENT STATUS

**Week 1 Day 1-2: COMPLETE ✅**
- ✅ 3 seed scripts created
- ✅ All dependencies in place
- ✅ Execution guide prepared
- ✅ Ready to load data

**Next: Week 1 Day 3-4**
- Run seed scripts
- Verify MongoDB
- Confirm 139/139 tests pass
- Create models and repository
