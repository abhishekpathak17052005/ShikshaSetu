# Data Quality Report — SIH 2026 Problem Statement 26101
**Prototype data foundation: AI Skill Intelligence Platform for India's Official Statistical System**

Generated: 2026-08-27
Scope: Part A (NSSTA/TPAC dataset), Part B (Competency taxonomy), Part C (Enriched iGOT dataset)

---

## 1. iGOT Course Dataset

| Metric | Count |
|---|---|
| Original seed records (untouched, `igot_courses_seed_56.csv`) | 56 |
| New records discovered this session | 12 |
| **Total unique records (`igot_courses_enriched.csv`)** | **68** |
| Records with `course_id` | 63 / 68 |
| Records with `course_url` | 63 / 68 |
| Records with **official** `official_competencies` | 0 / 68 |
| Records with **derived** `derived_competencies` (title-based) | 44 / 68 |
| Records with official `learning_outcomes` | 0 / 68 |
| Records with official `description` | 0 / 68 |
| Records with `provider` | 48 / 68 |
| Records with `duration` | 53 / 68 |
| Records with only title (+ maybe duration/provider), no description/LO/official competency | 68 / 68 |

**Read this carefully:** every single record in this dataset — seed and new alike — has **zero official description, learning outcomes, or official competency tags**. This is not a defect introduced this session; it reflects what the underlying government PDFs actually contain (course tables list title/provider/duration/URL, not full course metadata). The live iGOT portal likely holds richer metadata, but its course pages require JavaScript/login and were correctly excluded per your instruction not to bypass authentication.

The 12 new records (all `is_seed_record = N`) came from one additional verified official source not previously used: an NIEPID (Dept. of Empowerment of Persons with Disabilities, GoI) circular listing mandatory iGOT courses. Two other official sources checked this session (Maharashtra DVET SADHANA Saptah list; the NSSTA OM Annexures) turned out to be **the same underlying course set as the seed 56** — they were used only for cross-verification, contributing zero new unique records, which is reported honestly below rather than padded.

### 1.1 Derived vs. official metadata
- `derived_competencies` / `derived_subskills` / `derived_domain` / `derived_skill_level` are populated **only** where the course title (or difficulty_level field) contains explicit evidence. 24 of 68 records (mostly Hindi/Marathi/accessibility titles with no technical/statistical keyword) have **no** derived competency — left `NULL` rather than guessed.
- `derived_target_roles`, `derived_learning_outcomes`, and `derived_prerequisites` are `NULL` for all 68 records. Title text alone is not sufficient evidence to state a target role or a learning outcome without fabricating detail beyond what the instructions permit — so these were deliberately left blank rather than invented.
- All derivations carry `derivation_basis = "course_title"` and a conservative `derivation_confidence` (0.5 for a primary competency match, 0.45 for a subskill match) since title keyword-matching is comparatively weak evidence.

---

## 2. NSSTA / TPAC Training Programme Dataset

| Metric | Count |
|---|---|
| Total programmes extracted | 80 |
| Programmes with an official source (all — single source) | 80 / 80 |
| Programmes with a topic | 80 / 80 |
| Programmes with duration | 80 / 80 |
| Programmes with target participants | 80 / 80 |
| Programmes mapped to ≥1 competency | 40 / 80 |
| Programmes explicitly framed as TPAC-recommended | 80 / 80 |
| Programmes from the FY2025-26 Advance Training Calendar | 80 / 80 |
| Programmes with missing venue/eligibility detail | 80 / 80 (venue-institute is present; a separate `eligibility` field is NULL for all — the calendar does not state formal eligibility criteria, only which cadre/batch each row targets) |

All 80 programme rows come from a **single official document**: the MoSPI/NSSTA "(Tentative) Advance Training Calendar for FY(2025-2026)". This calendar states plainly that its entire content is "based on the recommendations of the Training Programme Approval Committee (TPAC)", so `recommended_by_TPAC = "Y"` was set for every row — this is an official claim in the source document itself, not an inference.

**Important caveats on this dataset:**
- The calendar itself is labelled "**Tentative**" — dates, venues, and batch sizes may change.
- The source does not assign programme IDs. Per your instruction, internal prototype IDs (`NSSTA-PROT-001`…`080`) were generated and explicitly flagged `id_type = "internal_prototype_id"`. These are **not** official NSSTA IDs.
- 40 of 80 programmes have no competency mapping — these are administrative/soft-skill/logistics sessions (e.g. "GFR: Procurement of Goods & Services", "Parliamentary Procedures", "e-Office Hands-on Practice") that don't map cleanly onto the SIH 26101 taxonomy and were left unmapped rather than force-mapped.
- Several rows are recurring modules (e.g. "SSS Induction Training Programme" repeats across ~9 weeks) — each week's occurrence was **not** duplicated as a separate record; recurring topics are represented once with `schedule = "Wk14 (recurring)"` etc. to avoid inflating the count artificially.

---

## 3. Competency Taxonomy

| Domain | Competencies (top-level) | Subskills |
|---|---|---|
| Statistical Competencies | 10 | 0 |
| Technical Competencies | 12 | 9 |
| Digital Governance | 5 | 0 |
| Behavioural / Managerial | 6 | 0 |
| **Total** | **33 top-level + 9 subskills = 42 rows** | |

- The 5-level (Awareness → Basic → Intermediate → Advanced → Expert) model is explicitly marked `framework_status = "prototype"` in every row — it is **our** framework, not a claimed official MoSPI/iGOT scale, per your instruction.
- Subskills exist only for Python (6) and AI/ML (3), where the problem statement's own worked example ("LLMs → NLP, Generative AI") justified decomposition. Other technical competencies (R, SQL, Stata, SPSS, SAS, GIS, Data Visualization, Cloud Computing, APIs, Open Data) were left as single top-level nodes — decomposing them without evidence from the source material would have been speculative.

---

## 4. Mapping Coverage

| Metric | Count |
|---|---|
| iGOT courses with ≥1 derived competency mapping | 44 / 68 (65%) |
| Total course→competency mapping rows | 68 |
| NSSTA programmes with ≥1 derived competency mapping | 40 / 80 (50%) |
| Total NSSTA→competency mapping rows | 46 |

All mapping rows are `mapping_type = "DERIVED"` — none are `OFFICIAL`, because no source document in this dataset explicitly tags a course or programme with a named competency from the SIH taxonomy. This is stated plainly rather than mislabeled.

---

## 5. Duplicates Removed

No duplicates were removed from the seed 56 (it was not re-processed for internal duplication) or from the 12 new NIEPID records (checked against seed by `course_id`; all 12 are unique). Two additional official sources found this session (Maharashtra DVET list, NSSTA OM Annexures) were checked **before** inclusion and found to reproduce the seed 56 exactly — so they contributed 0 new records and 0 duplicates by design (they were never merged in).

## 6. Records with Missing Fields (iGOT, selected)
- 5 seed records have `course_id = NULL` (statistics-specific courses named in an MoSPI Know-Your-Ministry style annexure, without an assigned iGOT platform ID in the source).
- 20 records (all seed) have `provider = NULL`.
- 15 records (all seed) have `duration = NULL`.
- 0 records have any official `description`, `learning_outcomes`, `tags`, `modules`, or `assessments_available` populated — this is a structural gap in every source PDF checked, not a processing error.

---

## 7. Gap vs. the Full iGOT Catalogue

iGOT Karmayogi is reported to host several thousand courses across ministries. This dataset of **68 verified records** is a small, traceable slice built entirely from documents that happen to **reproduce iGOT course lists in PDF/circular form** — it was never claimed, and should not be treated, as catalogue-level coverage. No API or bulk-download access to iGOT's own catalogue was used or attempted (correctly, per your instructions), because the live portal requires authentication.
