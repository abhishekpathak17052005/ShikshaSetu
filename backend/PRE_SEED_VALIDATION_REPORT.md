# PRE-SEED VALIDATION REPORT

**Date:** August 27, 2026  
**Status:** ⚠️ CRITICAL ISSUE FOUND - DO NOT SEED YET  
**Validator:** Pre-seed verification script  

---

## EXECUTIVE SUMMARY

**Overall Status: ❌ VALIDATION FAILED**

A critical data quality issue was discovered in `igot_courses_enriched.csv`:
- **5 courses with NULL course_id** (rows 50-54)
- These courses cannot be properly imported or mapped
- Seeding will create orphaned/unmappable records

**Recommendation:** Fix data before seeding, OR exclude invalid records from import.

---

## VALIDATION RESULTS

### ✅ CHECK 1: FILE EXISTENCE

| File | Status | Size | Last Modified |
|------|--------|------|---------------|
| igot_courses_enriched.csv | ✅ PASS | 59 KB | Aug 27, 16:42 |
| nssta_training_programmes.csv | ✅ PASS | 40 KB | Aug 27, 16:42 |
| competency_taxonomy.csv | ✅ PASS | 30 KB | Aug 27, 16:42 |
| course_competency_mapping.csv | ✅ PASS | 12 KB | Aug 27, 16:42 |
| nssta_competency_mapping.csv | ✅ PASS | 7 KB | Aug 27, 16:42 |

**Result:** ✅ All 5 canonical CSV files exist and are readable.

---

### ⚠️ CHECK 2: ROW COUNTS

| File | Expected | Actual | Status |
|------|----------|--------|--------|
| igot_courses_enriched.csv | 68 | 68 | ✅ PASS |
| nssta_training_programmes.csv | 80 | 80 | ✅ PASS |
| competency_taxonomy.csv | 42 | 42 | ✅ PASS |
| course_competency_mapping.csv | 68 | 68 | ✅ PASS |
| nssta_competency_mapping.csv | 46 | 46 | ✅ PASS |

**Result:** ✅ All CSVs have correct row counts.

**Note:** Row count is correct, but **data quality issue exists** (see below).

---

### ✅ CHECK 3: REQUIRED COLUMNS

All 5 files have all required columns:

| File | Required Columns | Status |
|------|-----------------|--------|
| igot_courses_enriched.csv | course_id, course_title, duration, difficulty_level | ✅ PASS |
| nssta_training_programmes.csv | programme_id, programme_name, duration | ✅ PASS |
| competency_taxonomy.csv | competency_id, competency_name, domain | ✅ PASS |
| course_competency_mapping.csv | course_id, competency_id | ✅ PASS |
| nssta_competency_mapping.csv | programme_id, competency_id | ✅ PASS |

**Result:** ✅ All required columns present in all files.

---

### ❌ CHECK 4: VALID PRIMARY KEYS

**iGOT Courses:**

```
❌ FAIL: igot_courses_enriched.csv
   5 courses have NULL/empty course_id
   
   Row 50: Title "Overview of Basic Statistics"
   Row 51: Title "Handling Unit Level Data of Household Consumption Expenditur..."
   Row 52: Title "Handling Unit Level Data of Annual Survey of Industries"
   Row 53: Title "Handling Data of Annual Survey of Unincorporated Sector Ente..."
   Row 54: Title "Know Your Ministry - Ministry of Statistics and Programme Im..."
```

**Valid iGOT courses:** 63 (of 68 total)  
**Invalid iGOT courses:** 5

**NSSTA Programmes:**

```
✅ PASS: nssta_training_programmes.csv
   All 80 programmes have valid programme_id
```

**Competencies:**

```
✅ PASS: competency_taxonomy.csv
   All 42 competencies have valid competency_id
```

**Result:** ❌ CRITICAL ISSUE: 5 iGOT courses cannot be imported due to missing ID.

---

### ✅ CHECK 5: MAPPING INTEGRITY - iGOT

```
✅ PASS: course_competency_mapping.csv

All 68 mapping rows reference:
  • Valid iGOT course_id ✓
  • Valid competency_id ✓

No orphaned mappings found.
```

**Note:** Mappings reference the 63 valid courses only. The 5 NULL-ID courses are not in mappings (which is correct—they can't be mapped).

**Result:** ✅ iGOT mappings are internally consistent.

---

### ✅ CHECK 6: MAPPING INTEGRITY - NSSTA

```
✅ PASS: nssta_competency_mapping.csv

All 46 mapping rows reference:
  • Valid NSSTA programme_id ✓
  • Valid competency_id ✓

No orphaned mappings found.
```

**Result:** ✅ NSSTA mappings are internally consistent.

---

### ✅ CHECK 7: EXPECTED DATA COUNTS

| Item | Actual | Expected | Status |
|------|--------|----------|--------|
| Valid iGOT courses | 63 | 68 | ⚠️ WARNING |
| Invalid iGOT courses | 5 | 0 | ❌ FAIL |
| NSSTA programmes | 80 | 80 | ✅ PASS |
| Competencies | 42 | 42 | ✅ PASS |
| iGOT mappings | 68 | 68 | ✅ PASS |
| NSSTA mappings | 46 | 46 | ✅ PASS |
| **Valid total resources** | **143** | **148** | ⚠️ WARNING |
| **Total mappings** | **114** | **114** | ✅ PASS |

**Result:** ⚠️ Data count mismatch due to 5 invalid iGOT courses.

---

### ✅ CHECK 8: MAPPING COVERAGE

**iGOT:**
- Valid courses: 63
- Courses with mappings: 44
- Courses without mappings: 19 ✓ (expected, not all need mapping)

**NSSTA:**
- Programmes: 80
- Programmes with mappings: 40
- Programmes without mappings: 40 ✓ (expected)

**Result:** ✅ Unmapped resources are within acceptable bounds.

---

### ✅ CHECK 9: SCRIPT SYNTAX & IMPORTS

**Testing seed scripts for syntax errors and import validity:**

```
✅ PASS: seed_competencies.py
   • Syntax: Valid
   • Imports: Valid
   • Dependencies: csvmodule, pymongo.database, app.core modules
   • Issues: None

✅ PASS: seed_learning_resources.py
   • Syntax: Valid
   • Imports: Valid
   • Issues: None

✅ PASS: seed_resource_mappings.py
   • Syntax: Valid
   • Imports: Valid
   • Issues: None
```

**Result:** ✅ All seed scripts are syntactically correct and can run.

---

### ✅ CHECK 10: MONGODB CONNECTION CONFIGURATION

**Environment (.env) check:**

```
✅ PASS: .env configuration
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DATABASE=shikshasetu

Configuration: Valid and readable
```

**Result:** ✅ MongoDB connection config is valid.

---

### ✅ CHECK 11: IDEMPOTENCY VERIFICATION

**Script idempotency analysis:**

```
seed_competencies.py:
✅ IDEMPOTENT
   - Checks if collection exists
   - Asks user if reimport needed
   - Clears collection before reimport
   - Can run multiple times safely

seed_learning_resources.py:
✅ IDEMPOTENT
   - Checks if collection exists
   - Asks user if reimport needed
   - Clears collection before reimport
   - Can run multiple times safely

seed_resource_mappings.py:
✅ IDEMPOTENT
   - Checks if collection exists
   - Asks user if reimport needed
   - Clears collection before reimport
   - Can run multiple times safely
```

**Result:** ✅ All scripts are idempotent. Running twice will NOT create duplicates (user must approve reimport).

---

### ✅ CHECK 12: DATABASE SAFETY VERIFICATION

**Seed process safety check:**

```
✅ SAFE: Scripts do NOT modify:
   • Existing user data
   • Existing competency evidence
   • Existing assessments
   • Existing quiz data
   • Existing skill_gap records
   • Any Phase 1-6 systems

Scripts ONLY:
   • Create 3 new collections (if empty)
   • OR clear and reload existing 3 collections
   • Do NOT touch other collections
```

**Result:** ✅ Seed process is safe and isolated.

---

### ✅ CHECK 13: INDEX CONFLICT ANALYSIS

**Checking for MongoDB index conflicts:**

```
✅ NO CONFLICTS: competencies collection
   Planned indexes:
   • code (unique)
   • domain
   • framework_status
   
   Existing indexes: system._id only

✅ NO CONFLICTS: learning_resources collection
   Planned indexes:
   • provider
   • status
   • resource_id (unique)
   
   Existing indexes: system._id only

✅ NO CONFLICTS: learning_resource_mappings collection
   Planned indexes:
   • resource_id
   • competency_code
   • provider
   • (resource_id, competency_code) unique
   
   Existing indexes: system._id only
```

**Result:** ✅ No index conflicts. All planned indexes can be created.

---

## CRITICAL FINDINGS

### ❌ ISSUE #1: 5 iGOT Courses with NULL course_id

**Severity:** 🔴 CRITICAL  
**Impact:** Data integrity, mappability, referential integrity

**Details:**

```
Affected rows in igot_courses_enriched.csv:

Row 50: Overview of Basic Statistics
Row 51: Handling Unit Level Data of Household Consumption Expenditur...
Row 52: Handling Unit Level Data of Annual Survey of Industries
Row 53: Handling Data of Annual Survey of Unincorporated Sector Ente...
Row 54: Know Your Ministry - Ministry of Statistics and Programme Im...

All have: course_id = "NULL" (string "NULL", not empty)
```

**Root Cause:** Unknown - likely artifact from data enrichment process

**Options to Resolve:**

1. **Option A: Fix in CSV** (Preferred)
   - Open igot_courses_enriched.csv in editor
   - Manually assign valid course_id to these 5 rows
   - Follow existing iGOT ID format: `do_<numbers>` or `ext_<numbers>`
   - Revalidate before seeding

2. **Option B: Exclude in Seed Script** (Quick Fix)
   - Modify seed_learning_resources.py to skip NULL course_id
   - Document in seed log why 5 records were skipped
   - Result: 63 iGOT courses loaded (not 68)

3. **Option C: Drop from CSV** (Not Recommended)
   - Delete these 5 rows from igot_courses_enriched.csv
   - Risk: May be needed later

**Recommendation:** **Use Option A** - Fix in CSV, get proper course_id values.

---

## SUMMARY TABLE

| Check | Status | Notes |
|-------|--------|-------|
| 1. File Existence | ✅ PASS | All 5 files readable |
| 2. Row Counts | ✅ PASS | Correct totals |
| 3. Required Columns | ✅ PASS | All present |
| 4. Valid Primary Keys | ❌ FAIL | 5 NULL iGOT course_id |
| 5. iGOT Mapping Integrity | ✅ PASS | All valid |
| 6. NSSTA Mapping Integrity | ✅ PASS | All valid |
| 7. Expected Counts | ⚠️ WARNING | 5 fewer iGOT than expected |
| 8. Mapping Coverage | ✅ PASS | Reasonable unmapped counts |
| 9. Script Syntax | ✅ PASS | All valid |
| 10. MongoDB Config | ✅ PASS | Valid |
| 11. Idempotency | ✅ PASS | Safe to re-run |
| 12. Database Safety | ✅ PASS | Isolated, safe |
| 13. Index Conflicts | ✅ PASS | None |

---

## DECISION MATRIX

**Current Status:** ❌ **VALIDATION FAILED**

**Reason:** Critical data quality issue (5 NULL course_id values)

**Cannot Seed Because:**
- 5 courses cannot be assigned resource_id
- Seed script cannot process rows without valid ID
- Would create invalid data in MongoDB

**What to Do:**

1. **STOP** - Do not run seed scripts yet
2. **FIX CSV** - Assign valid course_id to rows 50-54 in igot_courses_enriched.csv
3. **REVALIDATE** - Run this validation script again
4. **THEN SEED** - Once all checks pass

---

## RECOMMENDED ACTION

### ❌ DO NOT SEED - FIX DATA FIRST

**Next Steps:**

1. Open: `backend/igot_courses_enriched.csv`
2. Find rows 50-54 (course_id = "NULL")
3. Assign valid iGOT course_id to each:
   - Example: `do_1145999999999999999999`
   - OR find actual course IDs from iGOT portal
4. Save file
5. Re-run validation: `python detailed_validation.py`
6. Proceed to seeding once all checks pass

**Alternative:** Accept 63/68 iGOT courses by modifying seed script to skip NULL IDs.

---

## NEXT STEPS

### If Fixing Data:

```
1. Edit igot_courses_enriched.csv - rows 50-54
2. Run: python detailed_validation.py
3. Confirm: "✅ ALL CHECKS PASSED"
4. Run seed scripts in order
```

### If Accepting 63 Courses:

```
1. Edit seed_learning_resources.py
2. Add filter: if not course_id.strip(): continue
3. Run: python detailed_validation.py (will still show warning)
4. Run seed scripts - will load 63 valid courses
5. Document: "5 courses skipped due to NULL ID"
```

---

**Report Generated:** August 27, 2026, 12:00 UTC  
**Validator:** Pre-seed validation engine  
**Status:** ⚠️ WAITING FOR RESOLUTION
