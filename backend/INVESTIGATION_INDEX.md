# INVESTIGATION INDEX: NULL COURSE_ID RESEARCH

**Date:** August 27, 2026  
**Status:** ✅ Complete - Awaiting Decision  

---

## DOCUMENTS GENERATED

### Executive Summaries
1. **DECISION_POINT.txt** ← START HERE
   - Quick overview of options
   - Side-by-side comparison
   - Where to go next

2. **RESEARCH_FINDINGS_SUMMARY.txt**
   - Detailed analysis for each course
   - Key evidence
   - Recommendations

### Full Reports
3. **RESEARCH_COMPLETE_REPORT.md** ← COMPREHENSIVE REFERENCE
   - Complete investigation details
   - Methodology
   - Findings for each course
   - Confidence assessment

4. **RESEARCH_NULL_COURSE_IDS.md** ← DETAILED FINDINGS
   - Individual course analysis
   - Source document review
   - ID recovery status
   - Implementation guidance

### Validation Reports
5. **PRE_SEED_VALIDATION_REPORT.md**
   - Pre-seed validation results
   - 13 validation checks
   - Issue identification

6. **VALIDATION_STATUS.txt**
   - Quick status summary
   - Checks matrix
   - Database safety verification

7. **VALIDATION_DECISION_POINT.md**
   - Options for resolving NULL issue
   - Decision matrix
   - Next steps

8. **README_VALIDATION.md**
   - Executive validation summary
   - Documentation reference
   - Troubleshooting

---

## KEY FINDINGS

### The Issue
5 courses in `igot_courses_enriched.csv` have `course_id = NULL`

### The Discovery
These are NOT iGOT courses with missing IDs.
They are NSSTA training programmes from official government documents.

### The Conclusion
✅ **NULL is the correct value**

No iGOT course_id exists because these are not iGOT offerings.

### The Recommendation
🟢 **USE OPTION A: Load with NULL course_id (RECOMMENDED)**

---

## QUICK REFERENCE

### For Decision Makers
→ Read: `DECISION_POINT.txt`
→ Time: 5 minutes
→ Action: Choose Option A or B

### For Developers
→ Read: `RESEARCH_FINDINGS_SUMMARY.txt`
→ Time: 10 minutes
→ Action: Prepare seed script modifications if needed

### For Complete Context
→ Read: `RESEARCH_COMPLETE_REPORT.md`
→ Time: 20 minutes
→ Action: Full understanding of investigation

---

## EVIDENCE CHAIN

1. **Pre-seed Validation** (`PRE_SEED_VALIDATION_REPORT.md`)
   - Identified 5 NULL course_id values
   - Flagged as validation issue

2. **Research Initiated** (`DECISION_POINT.txt`)
   - Asked: Can these IDs be recovered?
   - Committed to investigation

3. **Data Audit** (`PHASE_3_DATA_AUDIT.md`)
   - Reviewed existing data documentation
   - Found source registry (SRC-05)

4. **Investigation Performed** (`RESEARCH_NULL_COURSE_IDS.md`)
   - Traced each course to source
   - Analyzed origin documents
   - Verified authenticity

5. **Findings Documented** (`RESEARCH_COMPLETE_REPORT.md`)
   - Confirmed: NSSTA courses, not iGOT
   - Confirmed: NULL is correct value
   - Confirmed: No iGOT ID available

6. **Decision Required** (`DECISION_POINT.txt`)
   - Option A: Load with NULL ✅ RECOMMENDED
   - Option B: Skip NULL courses
   - User chooses path forward

---

## COURSES INVESTIGATED

### Row 50: Overview of Basic Statistics
- Source: SRC-05 (NSSTA OM)
- Status: NSSTA course
- Recommendation: Keep NULL

### Row 51: Handling Unit Level Data of Household Consumption Expenditure Survey
- Source: SRC-05 (NSSTA OM)
- Status: NSSTA course
- Recommendation: Keep NULL

### Row 52: Handling Unit Level Data of Annual Survey of Industries
- Source: SRC-05 (NSSTA OM)
- Status: NSSTA course
- Recommendation: Keep NULL

### Row 53: Handling Data of Annual Survey of Unincorporated Sector Enterprises
- Source: SRC-05 (NSSTA OM)
- Status: NSSTA course
- Recommendation: Keep NULL

### Row 54: Know Your Ministry - Ministry of Statistics and Programme Implementation
- Source: SRC-05 (NSSTA OM)
- Status: NSSTA course
- Recommendation: Keep NULL

---

## SOURCE VERIFICATION

**SRC-05: MoSPI/NSSTA Office Memorandum**
- Date: 01.04.2026
- Type: Government PDF
- Document: NSSTA OM Annexure (Indicative List of AI courses / iGOT Marketplace Courses)
- Structure: Annexure I (iGOT courses) + Annexure II (NSSTA courses)
- All 5 courses: In Annexure II
- Status: VERIFIED_OFFICIAL

**SRC-01: Original Seed Dataset**
- All 5 courses: Present in seed_56.csv with NULL course_id
- Confirms: NULL is pre-existing (not recent corruption)
- Confirms: Not an import artifact

---

## DECISION SUPPORT

### Option A: Load with NULL course_id ✅ RECOMMENDED

**Why:**
- NULL is factually correct
- NSSTA courses are valid offerings
- Complete data
- No data invention
- Preserves provenance

**Result:**
- 148 resources in database
- Includes all 5 NSSTA-direct courses
- Proper classification

**Implementation:**
- No CSV modification needed
- Seed script can process NULL normally
- Generate internal ID (NSSTA-PROTO-xxxxx) for reference

### Option B: Skip NULL courses

**Why:**
- Simpler (no NULL values)
- Avoids edge cases
- Only iGOT courses in database

**Result:**
- 143 resources in database
- Loses 5 valid courses
- Incomplete NSSTA coverage

**Implementation:**
- Modify seed_learning_resources.py
- Add filter: skip if course_id is NULL
- Document why courses skipped

---

## NEXT ACTIONS

### Step 1: Choose Option
- Read: `DECISION_POINT.txt`
- Decide: Option A or Option B
- Confirm: Reply with your choice

### Step 2: Implement
- If Option A: Proceed to seeding
- If Option B: I modify seed script, then seed

### Step 3: Execute
- python -m app.scripts.seed_competencies
- python -m app.scripts.seed_learning_resources
- python -m app.scripts.seed_resource_mappings

### Step 4: Verify
- Check MongoDB document counts
- Run test suite
- Confirm no regressions

---

## CONFIDENCE ASSESSMENT

🟢 **HIGH (99% confidence)**

**Evidence Quality:**
- ✅ Official source verified (SRC-05)
- ✅ Provenance traced (seed_56.csv)
- ✅ Extraction notes documented
- ✅ No conflicting evidence
- ✅ Consistent across all 5 courses
- ✅ Pre-existing (not recent corruption)

---

## DOCUMENTS STRUCTURE

```
backend/
├── INVESTIGATION_INDEX.md (you are here)
├── DECISION_POINT.txt (START HERE)
├── RESEARCH_FINDINGS_SUMMARY.txt (quick overview)
├── RESEARCH_COMPLETE_REPORT.md (detailed findings)
├── RESEARCH_NULL_COURSE_IDS.md (individual analysis)
├── PRE_SEED_VALIDATION_REPORT.md (validation results)
├── VALIDATION_STATUS.txt (status matrix)
├── VALIDATION_DECISION_POINT.md (earlier decision point)
├── README_VALIDATION.md (validation summary)
├── research_null_courses.py (investigation script)
└── [other files...]
```

---

## READING GUIDE

### If you have 5 minutes:
→ Read: `DECISION_POINT.txt`

### If you have 15 minutes:
→ Read: `DECISION_POINT.txt` + `RESEARCH_FINDINGS_SUMMARY.txt`

### If you have 30 minutes:
→ Read: `RESEARCH_COMPLETE_REPORT.md`

### If you need everything:
→ Read: `RESEARCH_NULL_COURSE_IDS.md` + `RESEARCH_COMPLETE_REPORT.md`

---

## CURRENT STATUS

```
✅ Validation Phase: COMPLETE
✅ Investigation Phase: COMPLETE
✅ Findings Phase: COMPLETE
⏸️  Decision Phase: AWAITING YOUR CHOICE
```

---

**Index Created:** August 27, 2026  
**Status:** Ready for decision  
**Next:** User chooses Option A or B
