# Phase 3 Technical Debt & Data Gaps

## Data Discrepancies

### 1. Competency Framework Gap (9 items)

**CSV has 42 competency rows**
**Database has 33 seeded competencies**

Missing 9 items - likely sub-competencies or intentionally excluded.

**Action Required:**
- [ ] Document which 9 are intentionally excluded
- [ ] If sub-competencies: decide how to represent them
- [ ] If missing: add to framework seed

### 2. Mapping Completeness

**iGOT Mappings:**
- CSV has: 68 mapping rows
- Seeded: 42 mappings
- Skipped: 26 mappings

**Reason:** CSV references sub-competency codes (TECH-AIML-ML, TECH-AIML-GENAI, BM-DECISION, BM-CHANGE) that don't exist in the simplified framework.

**Action Required:**
- [ ] Document which mappings are skipped and why
- [ ] Decide: add sub-competencies to framework OR update CSV to use only framework codes
- [ ] Update seeding to report this clearly

**NSSTA Mappings:**
- CSV has: 46 mapping rows
- Seeded: 46 mappings
- Skipped: 0 mappings ✅

---

## Incomplete Features

### 1. CSV Code Translation

**Status:** Workaround implemented, not permanent solution

The mapping script includes a `translate_competency_code()` function to handle CSV codes (STAT-SURVEY) → database codes (STAT_SURVEY_DESIGN).

**Action Required:**
- [ ] Either: Standardize CSV to use underscore codes
- [ ] Or: Document the translation mapping permanently
- [ ] Add validation to warn if translation fails

### 2. Provider APIs (Live Integration)

**Status:** Not implemented (by design)

Currently all resources come from seeded MongoDB. No calls to:
- Live iGOT API
- Live NSSTA API

**Action Required:**
- [ ] Document that this is Phase 4 work
- [ ] Create placeholder provider classes for future integration
- [ ] Do not claim "IGOT integration" yet

### 3. Live NSSTA Synchronization

**Status:** Not implemented

NSSTA protocols are static in database. No dynamic updates.

**Action Required:**
- [ ] Document refresh requirements
- [ ] Plan sync strategy for SIH Round 2

---

## Known Limitations

### Sub-Competencies
CSV includes skills like "Machine Learning Fundamentals" (TECH-AIML-ML) that are mapped to parent competencies (TECH-AIML). Current framework doesn't distinguish these levels.

**For SIH Round 1:** Acceptable. Document as "simplified competency model."

### NULL course_id Resources
NSSTA has 5 records with NULL course_id (proto-competencies without firm enrollment links).

**For SIH Round 1:** Acceptable. These are browseable but not recommended by default.

### Unassessed Competencies
Skill gap engine handles NULL current_level (unassessed) by treating as 0.0 for gap calculation.

**For SIH Round 1:** Acceptable. Once assessment runs, current_level updates.

---

## Before Next Phase

### Documentation Tasks
- [ ] List which 9 competencies are missing from framework
- [ ] List which 26 iGOT mappings are skipped (with reason)
- [ ] Document CSV → database code translation
- [ ] Clarify sub-competency handling
- [ ] Update README with actual counts (33 competencies, 88 mappings, not 42/114)

### Testing Tasks
- [ ] Manual Postman workflow: Register → Assess → Recommend
- [ ] Verify score breakdown
- [ ] Verify determinism
- [ ] Verify provider separation
- [ ] Document all test results

### Code Tasks
- [ ] Make CSV translation permanent (not a workaround)
- [ ] Add logging for skipped mappings
- [ ] Add validation that all framework competencies are used
- [ ] Document why NULL current_level is 0.0 (not null in gaps)

---

## For SIH Presentation

**Say:**
"The prototype uses a simplified 33-competency framework with 88 active iGOT/NSSTA resource mappings. This demonstrates the core recommendation engine: assess → identify gaps → recommend → score."

**Don't say:**
"We support 42 competencies and 114 mappings."
"Live NSSTA integration ready."
"Production-grade system."

---

## Next Steps

**Not Ready for:**
- ❌ Production deployment
- ❌ Live government API integration
- ❌ Multi-role complex assessments
- ❌ Enterprise security hardening

**Ready for:**
- ✅ SIH Round 1 demo
- ✅ Controlled Postman testing
- ✅ Frontend integration (read-only)
- ✅ Technical discussion of architecture

---

**Compiled:** 2026-08-27
**By:** Implementation Chat
**For:** SIH Round 1 Submission
