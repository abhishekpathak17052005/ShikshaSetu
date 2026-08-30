# PRE-SEED VALIDATION: DECISION POINT

**Date:** August 27, 2026  
**Status:** ⚠️ VALIDATION COMPLETE - ACTION REQUIRED  

---

## THE ISSUE

5 iGOT courses in `igot_courses_enriched.csv` have **NULL course_id** instead of valid ID:

| Row | Title | course_id |
|-----|-------|-----------|
| 50 | Overview of Basic Statistics | NULL |
| 51 | Handling Unit Level Data of Household Consumption Expenditure | NULL |
| 52 | Handling Unit Level Data of Annual Survey of Industries | NULL |
| 53 | Handling Data of Annual Survey of Unincorporated Sector Enterprises | NULL |
| 54 | Know Your Ministry - Ministry of Statistics and Programme Implementation | NULL |

**Impact:** Cannot create resource_id without course_id. These 5 courses cannot be imported.

---

## YOUR OPTIONS

### ✅ OPTION A: FIX IN CSV (Recommended)

**What to do:**
1. Open `backend/igot_courses_enriched.csv` in a text editor or Excel
2. Go to row 50
3. Replace `NULL` with a valid iGOT course ID
   - Example: `do_1145999999999999999999`
   - Or look up actual ID from iGOT portal
4. Do same for rows 51-54
5. Save file
6. Re-run validation: `python backend/detailed_validation.py`
7. Once clean: Run seed scripts

**Pros:**
- Data integrity preserved
- All 68 courses imported
- Proper course IDs recorded
- Can re-validate anytime

**Cons:**
- Requires finding valid course IDs
- Need to manually edit CSV
- Time-consuming if IDs not available

**Result:** 68 iGOT courses loaded ✓

---

### ⚡ OPTION B: EXCLUDE INVALID RECORDS (Quick Fix)

**What to do:**
1. Modify `seed_learning_resources.py`
2. Add this filter in the iGOT course loading loop:

```python
if not row.get("course_id", "").strip() or row.get("course_id") == "NULL":
    print(f"  ⚠️  Skipping course {row.get('course_title')} - no valid ID")
    continue
```

3. Run seed scripts normally
4. Document: "5 courses skipped (NULL IDs)"

**Pros:**
- No CSV editing needed
- Fast - just modify script
- Data stays as-is
- Can still seed right away

**Cons:**
- Only 63 iGOT courses imported (not 68)
- Need to document skipped courses
- May need these courses later

**Result:** 63 iGOT courses loaded (5 skipped)

---

### ❌ OPTION C: DELETE ROWS (Not Recommended)

**What to do:**
1. Delete rows 50-54 from CSV

**Pros:**
- Simple

**Cons:**
- Data lost (risky)
- May need these courses later
- Cannot recover without backup
- Reduces integrity

**Result:** 63 iGOT courses loaded (data deleted)

---

## VALIDATION SUMMARY

| Check | Result | Impact |
|-------|--------|--------|
| File existence | ✅ PASS | |
| Row counts | ✅ PASS | |
| Column names | ✅ PASS | |
| **Primary keys** | ❌ FAIL | **5 courses unimportable** |
| Mapping integrity | ✅ PASS | All valid |
| Script syntax | ✅ PASS | All valid |
| MongoDB config | ✅ PASS | Ready |
| Database safety | ✅ PASS | Phase 1-6 safe |

---

## ALL OTHER CHECKS PASSED ✅

```
✅ All 5 CSV files readable
✅ All row counts correct (68, 80, 42, 68, 46)
✅ All required columns present
✅ All 68 iGOT mappings point to valid courses
✅ All 46 NSSTA mappings point to valid programmes
✅ All 114 mappings point to valid competencies
✅ Scripts are syntactically valid
✅ MongoDB connection configured
✅ Idempotency verified
✅ Database safety verified
✅ No index conflicts
```

---

## RECOMMENDATION

**Use OPTION A (Fix in CSV)** if you have time to find valid course IDs.

**Use OPTION B (Exclude Invalid Records)** if you need to seed immediately.

**Do NOT use OPTION C (Delete)** - risks losing data.

---

## DECISION MATRIX

```
If you have valid course IDs for rows 50-54:
  → Use OPTION A

If you don't have valid course IDs:
  → Use OPTION B (proceed with 63 courses)

If you need to investigate/research:
  → Pause seeding, investigate source data
```

---

## WHAT HAPPENS IF YOU SEED WITH INVALID DATA?

**If you do nothing** and run seed scripts:
- `seed_competencies.py` → ✅ Works fine (no issues)
- `seed_learning_resources.py` → ⚠️ Fails or skips 5 rows
- `seed_resource_mappings.py` → ✅ Works fine (mappings are valid)

**If you modify script** (Option B):
- All 3 scripts work
- 63 iGOT courses loaded
- 5 courses logged as skipped

---

## NEXT STEPS

### Choose your option:

**OPTION A:**
```
1. Find valid iGOT course IDs for 5 courses
2. Edit igot_courses_enriched.csv rows 50-54
3. Replace NULL with valid ID
4. Save file
5. Run: python backend/detailed_validation.py
6. Verify all checks pass
7. Run seed scripts
```

**OPTION B:**
```
1. Edit: backend/seed_learning_resources.py
2. Add skip filter for NULL course_id
3. Save file
4. Run: python backend/detailed_validation.py (still shows warning)
5. Run seed scripts
6. Document: 5 courses skipped
```

---

## QUESTIONS?

- **Can I find these course IDs?** Check iGOT portal or source PDF
- **What if I just skip them?** Use OPTION B - perfectly valid
- **Will this affect recommendations?** No - only 5 out of 68 courses
- **Can I add them later?** Yes - seed is idempotent, can reimport

---

## STATUS

```
VALIDATION: ✅ COMPLETE
BLOCKER: ❌ 5 NULL course_id values
ACTION: 🛑 AWAITING YOUR DECISION
NEXT: Choose Option A, B, or investigate
```

**STOP HERE** - Do not run seed scripts until you decide.

---

**Report:** backend/PRE_SEED_VALIDATION_REPORT.md  
**Status:** VALIDATION_STATUS.txt
