# Data Discrepancies - Phase 3 Seeding

## 1. Competency Framework Gap (9 Missing Items)

### CSV Source: competency_taxonomy.csv (42 rows)
### Database: 33 competencies seeded

**Missing 9 items from database:**

These appear to be in the CSV but were NOT seeded by `seed_framework.py`:

1. Sub-competency or child skill: **Machine Learning Fundamentals** (likely TECH-AIML-ML)
2. Sub-competency or child skill: **Generative AI / LLMs** (likely TECH-AIML-GENAI)
3. Sub-competency or child skill: **[Unknown - TECH variant]**
4. Related competency: **STAT-SURVEY** (vs. DB: STAT_SURVEY_DESIGN) - Code mismatch
5. Related competency: **STAT-NATACC** (vs. DB: STAT_NATIONAL_ACCOUNTS) - Code mismatch
6. Related competency: **STAT-PRICE** (vs. DB: STAT_PRICE_STATISTICS) - Code mismatch
7. Related competency: **STAT-LABOUR** (vs. DB: STAT_LABOUR_STATISTICS) - Code mismatch
8. Related competency: **STAT-AGRI** (vs. DB: STAT_AGRICULTURAL_STATISTICS) - Code mismatch
9. Related competency: **STAT-INDUS** (vs. DB: STAT_INDUSTRIAL_STATISTICS) - Code mismatch

### Analysis

The `seed_framework.py` script creates a fixed list of 33 competencies (see lines 18-50 in seed_framework.py). The original CSV may have had sub-competencies or alternative codes that aren't represented.

### Decision Required

**Option A:** The 9 items are intentionally excluded
- Sub-competencies should be handled separately (not in this phase)
- Simplified 33-item framework is sufficient for prototype
- Document this as "simplified competency model"

**Option B:** The 9 items are missing and should be added
- Extend `seed_framework.py` to include all 42 items
- Requires clarifying which are parent/child relationships
- May require schema changes for competency hierarchy

**Current Status:** Option A (implicit) - simplified framework is seeded and working
**Action:** Document this decision explicitly for SIH judges

---

## 2. iGOT Mapping Gap (26 Inactive Mappings)

### CSV Source: course_competency_mapping.csv (68 rows)
### Database: 42 iGOT mappings seeded

**26 mappings skipped - Reason: Competency codes don't exist in framework**

### Breakdown of Skipped Mappings

**Sub-competency codes not in framework (15 skip events):**
- `TECH-AIML-ML` (Machine Learning Fundamentals) - 11 occurrences
- `TECH-AIML-GENAI` (Generative AI / LLMs) - 4 occurrences

**Why:** These are mapping to skills that don't exist in the 33-competency framework.

**Behavioral competency codes not in framework (11 skip events):**
- `BM-DECISION` (Decision Making) - 3 occurrences
- `BM-CHANGE` (Change Management) - 3 occurrences

**Why:** Framework has `BEH_DECISION_MAKING` and `BEH_CHANGE_MANAGEMENT`, but CSV uses shorter codes. Translation function attempted to match but failed on these.

### CSV Sample (Skipped Rows)

```
do_1144751221174108161801, Artificial Intelligence for Public Governance, TECH-AIML-ML, Machine Learning Fundamentals, ...
[SKIP] Competency TECH-AIML-ML (translated: None) not found

do_1144751221174108161801, Artificial Intelligence for Public Governance, TECH-AIML-GENAI, Generative AI / LLMs, ...
[SKIP] Competency TECH-AIML-GENAI (translated: None) not found

[... more iGOT courses with these sub-competencies ...]
```

### Actual Seeded: 42 iGOT Mappings (from 68 CSV rows)

✅ Seeded successfully:
- TECH-PYTHON → TECH_PYTHON
- TECH-SQL → TECH_SQL
- TECH-R → TECH_R
- STAT-SAMPLING → STAT_SAMPLING
- STAT-SURVEY → STAT_SURVEY_DESIGN
- ... and 37 more (code translation working)

❌ Skipped (26 total):
- 15 sub-competency references (TECH-AIML-ML, TECH-AIML-GENAI)
- 11 behavioral competencies (BM-DECISION, BM-CHANGE)

### Decision Required

**Option A:** Accept 42/68 iGOT mappings as sufficient for prototype
- Sub-competencies are Phase 4 enhancement
- Simplified framework handles core competencies
- Document which courses are unmapped and why

**Option B:** Update CSV to use only framework-compatible codes
- Change sub-competency references to parent competencies
- Change BM-DECISION → BEH_DECISION_MAKING
- Reseed mappings

**Option C:** Extend framework to include sub-competencies
- Add TECH-AIML-ML, TECH-AIML-GENAI to framework
- Add BM-DECISION, BM-CHANGE aliases
- Update seed_framework.py
- Reseed all data

**Current Status:** Option A (implicit) - 42 iGOT mappings actively used
**Action:** Document this limitation explicitly for SIH judges

---

## 3. NSSTA Mappings (Complete)

✅ **46/46 NSSTA mappings seeded successfully**

No gaps. All NSSTA protocols matched to framework competencies.

---

## 4. Summary Statistics (Actual vs. Original Plan)

| Metric | Plan | Actual | Gap | Status |
|--------|------|--------|-----|--------|
| Competencies | 42 | 33 | -9 | 78.6% |
| iGOT Mappings | 68 | 42 | -26 | 61.8% |
| NSSTA Mappings | 46 | 46 | 0 | 100% |
| **Total Mappings** | **114** | **88** | **-26** | **77.2%** |
| Learning Resources | 148 | 148 | 0 | 100% |

---

## Recommendations for SIH Submission

### Honest Messaging

**What to say:**
"The prototype uses a simplified competency framework with 33 core competencies. We have 88 active learning resource mappings (63 iGOT + 46 NSSTA). Sub-competencies like 'Machine Learning Fundamentals' are treated as learning objectives within broader competency areas in this phase."

**What NOT to say:**
"We support all 42 competencies from the taxonomy."
"All 114 mappings are active."
"Complete taxonomy implementation."

### Documentation to Include

1. ✅ List of 33 active competencies (with domains)
2. ✅ List of 42 active iGOT mappings
3. ✅ List of 46 active NSSTA mappings
4. ✅ List of 26 inactive iGOT mappings (with reason: sub-competency not in framework)
5. ✅ List of 9 unrepresented taxonomy items (with explanation: simplified framework for prototype)

### For Future Phases

**Phase 4 (Sub-competencies):**
- Add TECH-AIML-ML, TECH-AIML-GENAI, etc. to framework
- Create parent-child competency relationships
- Reseed iGOT mappings

**Phase 4 (Complete Taxonomy):**
- Add remaining 9 competency items
- Validate against original taxonomy CSV
- Update all mapping seeds

---

## Action Items (Before Postman Verification)

- [ ] Create `COMPETENCIES_ACTIVE.md` listing all 33
- [ ] Create `MAPPINGS_ACTIVE.md` listing all 88
- [ ] Create `MAPPINGS_INACTIVE.md` listing all 26 skipped iGOT + reason
- [ ] Create `COMPETENCIES_UNREPRESENTED.md` listing 9 items + reason
- [ ] Update README.md with accurate counts
- [ ] Add note to seed scripts about these limitations
- [ ] Brief SIH judges on "simplified prototype framework"

---

**Document Created:** 2026-08-27
**Status:** Ready for Postman Verification
**Next Step:** Freeze backend, begin controlled HTTP testing
