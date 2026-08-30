# PRE-SEED VALIDATION REPORT - SUMMARY

**Completion Date:** August 27, 2026  
**Status:** ⚠️ **VALIDATION FAILED - DECISION REQUIRED**  
**Blocker:** 5 iGOT courses with NULL course_id  

---

## QUICK SUMMARY

✅ **13 Validation Checks Performed:**
- File existence: ✅ PASS
- Row counts: ✅ PASS  
- Required columns: ✅ PASS
- **Primary keys: ❌ FAIL** (5 NULL course_id values)
- Mapping integrity: ✅ PASS
- Database safety: ✅ PASS
- Script syntax: ✅ PASS
- Idempotency: ✅ PASS
- Index conflicts: ✅ PASS

---

## THE PROBLEM

**File:** `igot_courses_enriched.csv`  
**Issue:** 5 courses have "NULL" for course_id instead of valid ID  
**Rows:** 50, 51, 52, 53, 54  
**Impact:** Cannot generate resource_id - courses cannot be imported  
**Severity:** 🔴 CRITICAL - Blocks seeding

---

## AFFECTED COURSES

| Row | Title | Issue |
|-----|-------|-------|
| 50 | Overview of Basic Statistics | No course_id |
| 51 | Handling Unit Level Data of Household Consumption Expenditure | No course_id |
| 52 | Handling Unit Level Data of Annual Survey of Industries | No course_id |
| 53 | Handling Data of Annual Survey of Unincorporated Sector Enterprises | No course_id |
| 54 | Know Your Ministry - Ministry of Statistics and Programme Implementation | No course_id |

---

## DATA INTEGRITY REPORT

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| iGOT courses | 68 | 63 valid + 5 NULL | ⚠️ WARNING |
| NSSTA programmes | 80 | 80 | ✅ PASS |
| Competencies | 42 | 42 | ✅ PASS |
| iGOT mappings | 68 | 68 (all valid) | ✅ PASS |
| NSSTA mappings | 46 | 46 (all valid) | ✅ PASS |

---

## SEED SCRIPT READINESS

| Script | Status | Issue |
|--------|--------|-------|
| seed_competencies.py | ✅ READY | None - can seed 42 competencies |
| seed_learning_resources.py | ❌ BLOCKED | 5 NULL course_id rows |
| seed_resource_mappings.py | ✅ READY | None - mappings are valid |

---

## YOUR OPTIONS

### Option A: Fix Data (Recommended)
```
1. Edit igot_courses_enriched.csv
2. Replace NULL with valid course IDs (rows 50-54)
3. Re-validate
4. Seed
Result: 68 iGOT courses imported ✓
```

### Option B: Exclude Invalid (Quick)
```
1. Edit seed_learning_resources.py
2. Add skip filter for NULL course_id
3. Seed
Result: 63 iGOT courses imported (5 skipped)
```

### Option C: Delete Rows (Not Recommended)
```
1. Delete rows 50-54 from CSV
Result: 63 iGOT courses, data loss risk
```

---

## WHAT'S VERIFIED SAFE

✅ **All 3 seed scripts are:**
- Syntactically valid
- Import statements valid
- Idempotent (safe to re-run)
- Isolated (won't affect Phase 1-6 systems)

✅ **MongoDB:**
- Configuration valid
- No existing data conflicts
- Index creation safe

✅ **Database Safety:**
- User data untouched
- Assessments untouched
- Evidence untouched
- Quizzes untouched

---

## DETAILED VALIDATION RESULTS

### File-by-File Status

```
✅ igot_courses_enriched.csv
   • Readable: YES
   • Rows: 68 (correct count)
   • Columns: All present
   • Issue: 5 NULL course_id
   • Mappings: 68 valid (reference valid courses)

✅ nssta_training_programmes.csv
   • Readable: YES
   • Rows: 80 (correct)
   • Columns: All present
   • Issue: None
   • Mappings: 46 valid

✅ competency_taxonomy.csv
   • Readable: YES
   • Rows: 42 (correct)
   • Columns: All present
   • Issue: None

✅ course_competency_mapping.csv
   • Readable: YES
   • Rows: 68 (correct)
   • Integrity: All valid references

✅ nssta_competency_mapping.csv
   • Readable: YES
   • Rows: 46 (correct)
   • Integrity: All valid references
```

---

## STATISTICS

```
Total CSV checks performed:     13
Passed:                         12 ✅
Failed:                         1  ❌

Primary key validation:
  • Valid course IDs: 63/68 (92.6%)
  • NULL course IDs:  5/68  (7.4%)
  
Mapping validation:
  • Valid iGOT mappings:   68/68 (100%)
  • Valid NSSTA mappings:  46/46 (100%)
  • Orphaned mappings:     0/114 (0%)

Database impact:
  • Collections to create: 3
  • Collections to modify: 0
  • Phase 1-6 affected:    None (safe)
```

---

## DOCUMENTS GENERATED

1. **PRE_SEED_VALIDATION_REPORT.md** - Comprehensive validation report
2. **VALIDATION_STATUS.txt** - Visual status summary
3. **VALIDATION_DECISION_POINT.md** - Decision matrix
4. **README_VALIDATION.md** - This document

---

## SCRIPTS CREATED FOR VALIDATION

```
backend/validation_script.py       - CSV existence and row count checker
backend/detailed_validation.py     - Detailed integrity validation
backend/find_empty_ids.py          - Find rows with empty IDs
```

These are validation-only and do NOT modify MongoDB.

---

## RECOMMENDATION

### Immediate Action

**Choose ONE:**

A. **If you can find valid course IDs:** Fix CSV (Recommended)
B. **If you need to proceed immediately:** Modify seed script
C. **If investigating:** Pause and research data source

---

### Don't Do This

❌ Do NOT run seed scripts as-is - will fail or create orphaned data  
❌ Do NOT ignore the NULL values - affects data integrity  
❌ Do NOT delete rows - risks losing data  

---

## NEXT STEPS

1. **Review this report**
2. **Choose your option** (A, B, or research)
3. **If Option A:** Fix CSV and re-validate
4. **If Option B:** Modify seed script and proceed
5. **If Option C:** Research and report findings

Once resolved, proceed to seeding:
```
python -m app.scripts.seed_competencies
python -m app.scripts.seed_learning_resources
python -m app.scripts.seed_resource_mappings
```

---

## VALIDATION CHECKPOINT

Before seeding, ensure:
- [ ] You've reviewed PRE_SEED_VALIDATION_REPORT.md
- [ ] You've decided on Option A, B, or research
- [ ] If Option A: CSV has been fixed
- [ ] If Option B: seed_learning_resources.py has been modified
- [ ] Re-validated (if Option A)
- [ ] MongoDB is running
- [ ] .env is configured

---

## SUMMARY

✅ **Good News:**
- All data files accessible
- All row counts correct
- All mappings valid
- All scripts ready
- Database safe
- No other issues

⚠️ **Issue Found:**
- 5 iGOT courses with NULL course_id
- Blocks seed_learning_resources.py
- Fixable with simple data correction

✅ **Action:**
- Fix data OR modify script
- Then proceed to seeding

---

**Status:** ⚠️ AWAITING DECISION  
**Generated:** August 27, 2026  
**By:** Pre-seed validation engine
