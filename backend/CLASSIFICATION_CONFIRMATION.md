# CLASSIFICATION CONFIRMATION: 5 NSSTA/MoSPI Records

**Date:** August 27, 2026  
**Status:** ✅ CONFIRMED - Ready to seed  

---

## PREVIEW RESULTS

### Record 1: Overview of Basic Statistics (Row 50)

**In MongoDB:**
```json
{
  "resource_id": "NSSTA-PROTO-317DDEE7",
  "provider": "NSSTA",
  "resource_type": "TRAINING_PROGRAMME",
  "title": "Overview of Basic Statistics",
  "course_id": null,
  "source": {
    "source_url": "https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf",
    "source_document": "SRC-05",
    "verification_status": "TENTATIVE"
  }
}
```

**Classification:** ✅ NSSTA/MoSPI (NOT iGOT)

---

### Record 2: Handling Unit Level Data of Household Consumption Expenditure Survey (Row 51)

**In MongoDB:**
```json
{
  "resource_id": "NSSTA-PROTO-93BB1023",
  "provider": "NSSTA",
  "resource_type": "TRAINING_PROGRAMME",
  "title": "Handling Unit Level Data of Household Consumption Expenditure Survey",
  "course_id": null,
  "source": {
    "source_url": "https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf",
    "source_document": "SRC-05",
    "verification_status": "TENTATIVE"
  }
}
```

**Classification:** ✅ NSSTA/MoSPI (NOT iGOT)

---

### Record 3: Handling Unit Level Data of Annual Survey of Industries (Row 52)

**In MongoDB:**
```json
{
  "resource_id": "NSSTA-PROTO-8C325AD3",
  "provider": "NSSTA",
  "resource_type": "TRAINING_PROGRAMME",
  "title": "Handling Unit Level Data of Annual Survey of Industries",
  "course_id": null,
  "source": {
    "source_url": "https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf",
    "source_document": "SRC-05",
    "verification_status": "TENTATIVE"
  }
}
```

**Classification:** ✅ NSSTA/MoSPI (NOT iGOT)

---

### Record 4: Handling Data of Annual Survey of Unincorporated Sector Enterprises (Row 53)

**In MongoDB:**
```json
{
  "resource_id": "NSSTA-PROTO-753C9ADA",
  "provider": "NSSTA",
  "resource_type": "TRAINING_PROGRAMME",
  "title": "Handling Data of Annual Survey of Unincorporated Sector Enterprises",
  "course_id": null,
  "source": {
    "source_url": "https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf",
    "source_document": "SRC-05",
    "verification_status": "TENTATIVE"
  }
}
```

**Classification:** ✅ NSSTA/MoSPI (NOT iGOT)

---

### Record 5: Know Your Ministry - Ministry of Statistics and Programme Implementation (Row 54)

**In MongoDB:**
```json
{
  "resource_id": "NSSTA-PROTO-1D940B5B",
  "provider": "NSSTA",
  "resource_type": "TRAINING_PROGRAMME",
  "title": "Know Your Ministry - Ministry of Statistics and Programme Implementation",
  "course_id": null,
  "source": {
    "source_url": "https://www.mospi.gov.in/uploads/announcements/...NSSTA_OM_1.4.26_.pdf",
    "source_document": "SRC-05",
    "verification_status": "TENTATIVE"
  }
}
```

**Classification:** ✅ NSSTA/MoSPI (NOT iGOT)

---

## VERIFICATION CHECKLIST

### ✅ course_id Handling
- [x] Original NULL course_id preserved
- [x] NOT converted to iGOT ID format
- [x] NOT invented as "do_xxxxx" or "ext_xxxxx"
- [x] Stored as NULL in database

### ✅ Provider Classification
- [x] provider = "NSSTA" (NOT "IGOT")
- [x] Correct classification based on source
- [x] Source document verified (SRC-05)
- [x] Will NOT be counted as iGOT catalogue courses

### ✅ Resource Identification
- [x] Internal ID: NSSTA-PROTO-xxxxx (for database relationships only)
- [x] NOT used as course_id
- [x] Generated from title hash for determinism
- [x] Unique per record

### ✅ Provenance
- [x] Source URL preserved
- [x] Source document: SRC-05 (MoSPI/NSSTA OM)
- [x] Verification status: TENTATIVE (calendar, not confirmed)
- [x] Extraction note preserved

### ✅ Resource Type
- [x] resource_type = "TRAINING_PROGRAMME" (NOT "COURSE")
- [x] Correctly indicates NSSTA offering
- [x] Matches provider classification

---

## EXPECTED MONGODB COUNTS

After seeding:

| Collection | Count | Notes |
|------------|-------|-------|
| competencies | 42 | From competency_taxonomy.csv |
| learning_resources | 148 | 63 iGOT + 80 NSSTA + 5 NSSTA-direct |
| learning_resource_mappings | 114 | 68 iGOT + 46 NSSTA |

### learning_resources Breakdown:

```
provider='IGOT': 63 courses
  • All with valid course_id
  • All from iGOT portal or NIEPID source
  • resource_type='COURSE'

provider='NSSTA': 85 programmes
  • 80 from nssta_training_programmes.csv (with programme_id)
  • 5 from igot_courses_enriched.csv (with course_id=NULL)
  • All resource_type='TRAINING_PROGRAMME'
  • All from MoSPI/NSSTA official sources
```

---

## RECOMMENDATION MAPPING IMPACT

**These 5 NSSTA/MoSPI records:**
- ✅ Will be included in learning_resources collection
- ✅ Can be linked to competencies via mappings
- ❌ Will NOT be incorrectly classified as iGOT courses
- ❌ Will NOT inflate iGOT course count
- ✅ Will be available for recommendations but properly labeled NSSTA

**Recommendation engine will:**
- Treat them as NSSTA resources (provider='NSSTA')
- Apply appropriate confidence levels (TENTATIVE for NSSTA)
- Include them in resource pool for NSSTA provider
- Not confuse them with iGOT catalogue courses

---

## CONFIRMATION

✅ **All 5 records will be correctly classified**

```
Status: READY TO SEED
Classification: NSSTA/MoSPI (verified)
Provider: NSSTA (correct)
course_id: NULL (preserved)
Provenance: SRC-05 (maintained)
```

**Proceeding with seeding...**

---

**Confirmed:** August 27, 2026  
**By:** Pre-seed classification verification  
**Status:** ✅ APPROVED FOR SEEDING
