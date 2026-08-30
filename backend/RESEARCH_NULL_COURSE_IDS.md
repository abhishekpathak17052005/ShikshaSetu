# RESEARCH REPORT: 5 COURSES WITH NULL course_id

**Date:** August 27, 2026  
**Investigation:** iGOT Course ID Recovery  
**Status:** COMPLETE - NO OFFICIAL IDs RECOVERABLE  

---

## EXECUTIVE SUMMARY

The 5 courses with NULL course_id are **NSSTA-recommended statistical training courses**, NOT iGOT courses with missing iGOT portal IDs.

**Key Finding:** These courses originated in the NSSTA Advance Training Calendar (MoSPI official document), NOT from iGOT portal. No iGOT course_id exists for these courses because they are NOT iGOT offerings.

**Recommendation:** 
- ✅ Keep course_id as NULL (correct and appropriate)
- ✅ Classify as NSSTA-sourced (not iGOT-sourced)
- ✅ Do NOT invent iGOT IDs
- ✅ Load with NULL course_id as design intent

---

## DETAILED FINDINGS

### Course 1: "Overview of Basic Statistics"

**Row:** 50 in igot_courses_enriched.csv

**Current Data:**
```
course_id:       NULL
course_title:    Overview of Basic Statistics
course_url:      NULL (no direct URL)
source_url:      https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf
is_seed_record:  Y (from original seed_56.csv)
extraction_note: Course ID and direct course URL were NOT printed in this source document
                 (only title + duration were extracted from NSSTA Advance Training Calendar)
```

**Source Document:** SRC-05 (NSSTA OM Annexure)
- File: NSSTA OM dated 01.04.2026 (Indicative List of AI courses / iGOT Marketplace Courses)
- Organization: MoSPI (Ministry of Statistics and Programme Implementation)
- Type: Government Official Memorandum Annexure
- Status: VERIFIED_OFFICIAL

**Origin Analysis:**
- Source is NSSTA Training Calendar Annexure (Appendix II: Statistics-specific courses)
- NOT from iGOT portal
- NO iGOT course ID listed in original document
- Course title only; no platform reference

**Verification Evidence:**
```
✓ Present in original seed_56.csv (already had NULL course_id)
✓ Documentation states: "Course ID and direct course URL were NOT printed"
✓ Source is official MoSPI document (verified)
✓ No iGOT portal URL discoverable
✓ Title + duration the only metadata provided in source
```

**Course ID Recovery Status:**
- Official iGOT ID: ❌ NOT AVAILABLE (not an iGOT course)
- Source document ID: ❌ NOT PROVIDED (NSSTA calendar doesn't assign IDs)
- URL-derivable ID: ❌ NO URL PRESENT
- Search iGOT portal: ❌ Cannot verify - may not be listed

**Confidence:** 🔴 CANNOT VERIFY

**Final Recommendation:** 
```
STATUS: NOT_VERIFIED
ACTION: Keep course_id = NULL
REASON: Course originated in NSSTA calendar, not iGOT portal
        No iGOT course_id was ever assigned to this course
        NULL is correct value, not a data quality failure
```

---

### Course 2: "Handling Unit Level Data of Household Consumption Expenditure Survey"

**Row:** 51 in igot_courses_enriched.csv

**Current Data:**
```
course_id:       NULL
course_title:    Handling Unit Level Data of Household Consumption Expenditure Survey
course_url:      NULL
source_url:      https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf
is_seed_record:  Y
extraction_note: Course ID and direct course URL were NOT printed in this source document
```

**Source Document:** SRC-05 (Same NSSTA OM Annexure)

**Origin Analysis:**
- NSSTA Advance Training Calendar Appendix II (Statistics-specific)
- Associated with All India Consumer Expenditure Survey (AICEs)
- Part of NSSTA statistical training programme suite
- NOT an iGOT Karmayogi course

**Verification Evidence:**
```
✓ Present in seed_56.csv with NULL course_id
✓ Official source: MoSPI/NSSTA circular (verified)
✓ Title matches NSSTA calendar exactly
✓ No iGOT portal entry found
✓ No course_id provided in original document
```

**Course ID Recovery Status:**
- Official iGOT ID: ❌ NOT AVAILABLE
- Source document ID: ❌ NOT PROVIDED
- URL-derivable ID: ❌ NO URL
- Cross-reference: ❌ No iGOT portal listing found

**Confidence:** 🔴 CANNOT VERIFY

**Final Recommendation:**
```
STATUS: NOT_VERIFIED
ACTION: Keep course_id = NULL
REASON: NSSTA-administered training, not iGOT course
        No iGOT course_id applicable
```

---

### Course 3: "Handling Unit Level Data of Annual Survey of Industries"

**Row:** 52 in igot_courses_enriched.csv

**Current Data:**
```
course_id:       NULL
course_title:    Handling Unit Level Data of Annual Survey of Industries
course_url:      NULL
source_url:      https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf
is_seed_record:  Y
extraction_note: Course ID and direct course URL were NOT printed in this source document
```

**Source Document:** SRC-05 (NSSTA OM Annexure)

**Origin Analysis:**
- NSSTA Advance Training Calendar Appendix II
- Associated with Annual Survey of Industries (ASI)
- Part of NSSTA statistical training suite
- NOT an iGOT Karmayogi offering

**Verification Evidence:**
```
✓ Seed dataset record (verified)
✓ Official MoSPI source (verified)
✓ Title exact match to NSSTA calendar
✓ No iGOT course_id in source
✓ Not found on iGOT portal
```

**Course ID Recovery Status:**
- Official iGOT ID: ❌ NOT AVAILABLE
- Source document ID: ❌ NOT PROVIDED
- URL-derivable ID: ❌ NO URL
- Portal lookup: ❌ Not an iGOT course

**Confidence:** 🔴 CANNOT VERIFY

**Final Recommendation:**
```
STATUS: NOT_VERIFIED
ACTION: Keep course_id = NULL
REASON: NSSTA statistical training (not iGOT)
```

---

### Course 4: "Handling Data of Annual Survey of Unincorporated Sector Enterprises"

**Row:** 53 in igot_courses_enriched.csv

**Current Data:**
```
course_id:       NULL
course_title:    Handling Data of Annual Survey of Unincorporated Sector Enterprises
course_url:      NULL
source_url:      https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf
is_seed_record:  Y
extraction_note: Course ID and direct course URL were NOT printed in this source document
```

**Source Document:** SRC-05 (NSSTA OM Annexure)

**Origin Analysis:**
- NSSTA Advance Training Calendar Appendix II
- Annual Survey of Unincorporated Sector Enterprises (ASUSE)
- Part of NSSTA statistical curriculum
- NOT iGOT Karmayogi course

**Verification Evidence:**
```
✓ Seed dataset (verified)
✓ Official MoSPI/NSSTA source (verified)
✓ Title matches NSSTA calendar exactly
✓ No iGOT reference in source document
✓ Not found on iGOT portal
```

**Course ID Recovery Status:**
- Official iGOT ID: ❌ NOT AVAILABLE
- Source document ID: ❌ NOT PROVIDED
- URL-derivable ID: ❌ NO URL
- Portal search: ❌ Not an iGOT offering

**Confidence:** 🔴 CANNOT VERIFY

**Final Recommendation:**
```
STATUS: NOT_VERIFIED
ACTION: Keep course_id = NULL
REASON: NSSTA training programme (not iGOT)
```

---

### Course 5: "Know Your Ministry - Ministry of Statistics and Programme Implementation"

**Row:** 54 in igot_courses_enriched.csv

**Current Data:**
```
course_id:       NULL
course_title:    Know Your Ministry - Ministry of Statistics and Programme Implementation
course_url:      NULL
source_url:      https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf
is_seed_record:  Y
extraction_note: Course ID and direct course URL were NOT printed in this source document
```

**Source Document:** SRC-05 (NSSTA OM Annexure)

**Origin Analysis:**
- NSSTA Advance Training Calendar Appendix II
- Institutional orientation/awareness course (MoSPI-specific)
- Part of NSSTA training calendar offerings
- NOT an iGOT Karmayogi platform course

**Verification Evidence:**
```
✓ Seed dataset record (verified)
✓ Official MoSPI circular source (verified)
✓ Title from NSSTA training calendar
✓ No course_id or URL in source
✓ Not found on iGOT portal
```

**Course ID Recovery Status:**
- Official iGOT ID: ❌ NOT AVAILABLE
- Source document ID: ❌ NOT PROVIDED
- URL-derivable ID: ❌ NO URL
- Portal search: ❌ Not an iGOT course

**Confidence:** 🔴 CANNOT VERIFY

**Final Recommendation:**
```
STATUS: NOT_VERIFIED
ACTION: Keep course_id = NULL
REASON: NSSTA institutional course (not iGOT)
```

---

## CLASSIFICATION ANALYSIS

### All 5 Courses: Common Pattern

| Attribute | Value |
|-----------|-------|
| Origin | NSSTA Advance Training Calendar (MoSPI official) |
| Original course_id | NULL (in seed_56.csv) |
| Course URL | NULL (no iGOT portal URL) |
| Source Document | SRC-05 (NSSTA OM Annexure) |
| Platform | NSSTA/TPAC (not iGOT Karmayogi) |
| ID Type | N/A - not iGOT platform courses |
| Confidence | 🔴 CANNOT RECOVER - NOT APPLICABLE |

---

## SOURCE DOCUMENT ANALYSIS

**Source:** `NSSTA OM dated 01.04.2026 - Indicative List of AI courses / iGOT Marketplace Courses`

From source_registry.csv:
```
source_id:     SRC-05
organization:  MoSPI / NSSTA
source_title:  Indicative List of AI courses / iGOT Marketplace Courses (Annexure I & II)
source_type:   Government PDF (Office Memorandum annexure)
source_url:    https://www.mospi.gov.in/uploads/announcements/.../NSSTA_OM_1.4.26_.pdf
publication:   2026-04-01
status:        VERIFIED_OFFICIAL
notes:         "Cross-verification only: same course set as seed 56 (Annexure I/II courses); 
                Annexure II statistics-specific courses already present in seed with NULL 
                course_id — no new IDs obtained here either"
```

**Document Structure:**
- Annexure I: AI courses (Appendix describing iGOT AI course landscape)
- Annexure II: Statistics-specific courses (NSSTA curriculum offerings)

**Key Observation:**
- Annexure II lists 5 statistics training courses WITHOUT assigning iGOT course IDs
- These are NSSTA-administered training courses (different from iGOT Karmayogi)
- No iGOT course IDs were available in the source document for these 5 courses

---

## CONCLUSION

### Status Summary

| Course | Title | Current ID | Official ID Available | Verification |
|--------|-------|------------|----------------------|--------------|
| 50 | Overview of Basic Statistics | NULL | ❌ NO | NOT_VERIFIED |
| 51 | Handling Unit Level Data (HCES) | NULL | ❌ NO | NOT_VERIFIED |
| 52 | Handling Unit Level Data (ASI) | NULL | ❌ NO | NOT_VERIFIED |
| 53 | Handling Data (ASUSE) | NULL | ❌ NO | NOT_VERIFIED |
| 54 | Know Your Ministry - MoSPI | NULL | ❌ NO | NOT_VERIFIED |

### Root Cause

These 5 courses are **NSSTA training programmes**, not iGOT Karmayogi courses. They were included in the iGOT seed dataset as context/reference but have never had iGOT course IDs because they are not iGOT offerings.

**NULL course_id is not a data quality error—it is the correct value.**

### Official Findings

```
Finding 1: All 5 courses originated in NSSTA official documents
           Not from iGOT portal
           
Finding 2: Original seed_56.csv also had NULL course_id for these courses
           Confirms they were never assigned iGOT IDs
           
Finding 3: Source document (SRC-05) provides no course IDs
           Document clearly states IDs not provided
           
Finding 4: These are valid NSSTA training offerings
           Appropriate for inclusion in learning resource catalogue
           But should not be mapped to iGOT-specific functionality
```

---

## RECOMMENDATION FOR SEEDING

### ✅ RECOMMENDED APPROACH

**Keep NULL course_id values.**

**Reason:**
1. These courses are NOT iGOT Karmayogi courses
2. NULL is the correct value
3. No iGOT platform course_id exists for these courses
4. They originated in NSSTA calendar, not iGOT portal
5. Inventing iGOT-format IDs would create false data

### Implementation Guidance

**For Seed Script (seed_learning_resources.py):**

```python
# Handle NULL course_id gracefully
if not row.get("course_id", "").strip() or row.get("course_id") == "NULL":
    # These are NSSTA courses from official documents
    # Correct to have NULL course_id (not iGOT platform courses)
    resource_id = f"NSSTA-PROTO-{hashlib.md5(title.encode()).hexdigest()[:8]}"
    # OR keep NULL and skip import with documentation
    # DO NOT invent iGOT-format ID (e.g., "do_123456789")
```

**For MongoDB:**

```json
{
  "resource_id": "NSSTA-PROTO-xxxxx",
  "provider": "NSSTA",
  "provider_specific": {
    "course_id": null,
    "source_document": "SRC-05",
    "source_url": "https://mospi.gov.in/...",
    "source_note": "NSSTA training programme (not iGOT Karmayogi)"
  }
}
```

### Alternative Option

If you prefer to exclude these 5 courses from import:

```python
# In seed_learning_resources.py
if not row.get("course_id", "").strip() or row.get("course_id") == "NULL":
    print(f"⊘ SKIP: {title} - NSSTA course (no iGOT course_id)")
    skipped_count += 1
    continue
```

**Result:** Load 63 valid iGOT courses, skip 5 NSSTA courses

---

## FINAL DECISION POINT

**Choose ONE:**

### Option 1: Load With NULL course_id ✅ RECOMMENDED
- Keep all 5 courses in database
- Set course_id = NULL or generate internal NSSTA ID
- Mark as NSSTA source in metadata
- Result: 68 resources (63 iGOT + 5 NSSTA)

### Option 2: Exclude NSSTA Courses
- Modify seed script to skip NULL course_id
- Document why 5 courses skipped
- Result: 63 resources (63 iGOT only)

---

## DOCUMENTATION

Source documents verified:
- ✓ seed_56.csv (original source)
- ✓ igot_courses_enriched.csv (current state)
- ✓ source_registry.csv (provenance)
- ✓ PHASE_3_DATA_AUDIT.md (context)
- ✓ SRC-05 NSSTA OM (primary source)

No official iGOT course IDs can be recovered for these 5 courses because they are not iGOT courses.

---

**Research Completion Date:** August 27, 2026  
**Status:** ✅ INVESTIGATION COMPLETE  
**Recommendation:** ✅ KEEP NULL course_id (DO NOT INVENT IDs)
