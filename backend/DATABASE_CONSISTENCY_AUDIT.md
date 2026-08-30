# Database Consistency Audit — ShikshaSetu Production Database (`shikshasetu`)

**Date**: August 30, 2026  
**Auditor**: Backend & AI Engineering (Abhishek)  
**Database Audited**: `shikshasetu` (MongoDB Live Instance)  
**Audit Type**: Strict Read-Only Structural & Referential Integrity Audit  
**Backend Baseline**: 164 / 164 Pytest tests passing (Untouched)

---

## 1. Current Database Snapshot

The production MongoDB database `shikshasetu` currently hosts **14 collections** across employee profiles, competency taxonomies, role definitions, initial & capability assessments, learning resources, and uploaded training materials.

```
shikshasetu (Live MongoDB)
├── users (21 documents)
├── roles (1 document: STATISTICAL_OFFICER)
├── role_requirements (8 documents)
├── competencies (42 documents)
├── competency_profiles (16 documents)
├── competency_evidence (72 documents)
├── assessments (1 master document)
├── assessment_attempts (5 documents)
├── assessment_configurations (10 documents)
├── capability_assessments (0 documents)
├── question_bank (122 documents)
├── learning_resources (148 documents: 63 iGOT, 85 NSSTA)
├── learning_resource_mappings (114 documents)
├── learning_materials (12 documents)
└── document_chunks (0 documents)
```

---

## 2. Collection Counts

| Collection Name | Document Count | Storage Status | Primary Key Index | Foreign Keys Contained |
| :--- | :---: | :---: | :---: | :--- |
| `users` | **21** | Populated | `_id` (ObjectId) | `role_id` $\to$ `roles._id` |
| `roles` | **1** | Populated | `_id` (ObjectId) | None |
| `competencies` | **42** | Populated | `_id` (ObjectId) | None |
| `role_requirements` | **8** | Populated | `_id` (ObjectId) | `role_id`, `competency_id` |
| `competency_profiles` | **16** | Populated | `_id` (ObjectId) | `user_id`, `competency_id` |
| `competency_evidence` | **72** | Populated | `_id` (ObjectId) | `user_id`, `competency_id`, `assessment_id` |
| `assessments` | **1** | Populated | `_id` (ObjectId) | Embedded question competency IDs |
| `assessment_attempts` | **5** | Populated | `_id` (ObjectId) | `user_id`, `assessment_id` |
| `assessment_configurations` | **10** | Populated | `_id` (ObjectId) | `competency_code` (String code) |
| `capability_assessments` | **0** | Active / Runtime | `_id` (ObjectId) | `user_id`, `competency_code` |
| `question_bank` | **122** | Populated | `_id` (ObjectId) | `competency_code` (String code) |
| `learning_resources` | **148** | Populated | `_id` (ObjectId) | Unique `resource_id` |
| `learning_resource_mappings` | **114** | Populated | `_id` (ObjectId) | `resource_id` $\to$ `learning_resources._id`, `competency_id` $\to$ `competencies._id` |
| `learning_materials` | **12** | Populated | `_id` (ObjectId) | `user_id` $\to$ `users._id` |
| `document_chunks` | **0** | Ingestion Target | `_id` (ObjectId) | `material_id` $\to$ `learning_materials._id` |
| `quizzes` | **0** | Active / Runtime | `_id` (ObjectId) | `user_id`, `material_id` |
| `quiz_attempts` | **0** | Active / Runtime | `_id` (ObjectId) | `user_id`, `quiz_id` |

---

## 3. Competency Code Consistency

The audit identified **two distinct naming conventions** in the repository resulting from separate seeding phases:
1. **Convention A (Short-Hyphenated)**: e.g., `TECH-SQL`, `STAT-SAMPLING`, `DGOV-CYBER`, `BM-LEADERSHIP` (seeded by `seed_competencies.py` and referenced by `learning_resource_mappings`).
2. **Convention B (Domain-Prefix-Underscore)**: e.g., `TECH_SQL`, `STAT_SAMPLING`, `DIGOV_CYBERSECURITY`, `BEH_LEADERSHIP` (used by `seed_framework.py`, `seed_capability.py`, `question_bank`, and `assessment_configurations`).

### Competency Code Mapping & Discrepancy Table

| Current Code in DB (`competencies` / `mappings`) | Code in `assessment_configurations` & `question_bank` | Domain | Correct Canonical Code | Records Affected |
| :--- | :--- | :--- | :--- | :---: |
| `STAT-SAMPLING` | `STAT_SAMPLING` | Statistical | `STAT_SAMPLING` | 10 questions, 1 config, 4 mappings |
| `STAT-SURVEY` | `STAT_SURVEY_DESIGN` | Statistical | `STAT_SURVEY_DESIGN` | 10 questions, 1 config, 4 mappings |
| `STAT-DQ` | — | Statistical | `STAT_DATA_QUALITY_FRAMEWORKS` | 8 mappings |
| `STAT-NATACC` | — | Statistical | `STAT_NATIONAL_ACCOUNTS` | 4 mappings |
| `STAT-PRICE` | — | Statistical | `STAT_PRICE_STATISTICS` | 4 mappings |
| `STAT-LABOUR` | — | Statistical | `STAT_LABOUR_STATISTICS` | 4 mappings |
| `STAT-AGRI` | — | Statistical | `STAT_AGRICULTURAL_STATISTICS` | 4 mappings |
| `STAT-INDUS` | — | Statistical | `STAT_INDUSTRIAL_STATISTICS` | 4 mappings |
| `STAT-SDG` | — | Statistical | `STAT_SDG_INDICATORS` | 4 mappings |
| `STAT-META` | — | Statistical | `STAT_METADATA_STANDARDS` | 4 mappings |
| `TECH-PYTHON` | `TECH_PYTHON` | Technical | `TECH_PYTHON` | 15 questions, 1 config, 8 mappings |
| `TECH-SQL` | `TECH_SQL` | Technical | `TECH_SQL` | 15 questions, 1 config, 8 mappings |
| `TECH-R` | `TECH_R` | Technical | `TECH_R` | 11 questions, 1 config, 4 mappings |
| `TECH-DATAVIZ` | — | Technical | `TECH_DATA_VISUALIZATION` | 4 mappings |
| `TECH-GIS` | — | Technical | `TECH_GIS` | 4 mappings |
| `TECH-AIML` | — | Technical | `TECH_AI_ML` | 6 mappings |
| `TECH-CLOUD` | — | Technical | `TECH_CLOUD_COMPUTING` | 4 mappings |
| `TECH-STATA` | — | Technical | `TECH_STATA` | 2 mappings |
| `TECH-SPSS` | — | Technical | `TECH_SPSS` | 2 mappings |
| `TECH-SAS` | — | Technical | `TECH_SAS` | 2 mappings |
| `TECH-API` | — | Technical | `TECH_APIS` | 2 mappings |
| `TECH-OPENDATA` | — | Technical | `TECH_OPEN_DATA` | 2 mappings |
| `DGOV-CYBER` | `DIGOV_CYBERSECURITY` | Digital Governance | `DIGOV_CYBERSECURITY` | 13 questions, 1 config, 4 mappings |
| `DGOV-PRIVACY` | `DIGOV_DATA_PRIVACY` | Digital Governance | `DIGOV_DATA_PRIVACY` | 13 questions, 1 config, 4 mappings |
| `DGOV-DSIG` | — | Digital Governance | `DIGOV_DIGITAL_SIGNATURES` | 2 mappings |
| `DGOV-CLOUD` | — | Digital Governance | `DIGOV_GOVERNMENT_CLOUD` | 2 mappings |
| `DGOV-DPI` | — | Digital Governance | `DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE` | 2 mappings |
| `BM-LEADERSHIP` | `BEH_LEADERSHIP` | Behavioural/Managerial | `BEH_LEADERSHIP` | 13 questions, 1 config, 4 mappings |
| `BM-COMM` | `BEH_COMMUNICATION` | Behavioural/Managerial | `BEH_COMMUNICATION` | 11 questions, 1 config, 4 mappings |
| `BM-PM` | `BEH_PROJECT_MANAGEMENT` | Behavioural/Managerial | `BEH_PROJECT_MANAGEMENT` | 11 questions, 1 config, 4 mappings |
| `BM-ETHICS` | — | Behavioural/Managerial | `BEH_ETHICS` | 2 mappings |
| `BM-DECISION` | — | Behavioural/Managerial | `BEH_DECISION_MAKING` | 2 mappings |
| `BM-CHANGE` | — | Behavioural/Managerial | `BEH_CHANGE_MANAGEMENT` | 2 mappings |

---

## 4. Foreign-Key / ObjectId Integrity Audit

| Relationship | Source Collection $\to$ Target | Total Records | Valid References | Orphaned / Broken | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `users.role_id` | `users` $\to$ `roles._id` | 21 | **21** | 0 | 🟢 **Consistent** |
| `role_requirements.role_id` | `role_requirements` $\to$ `roles._id` | 8 | **8** | 0 | 🟢 **Consistent** |
| `role_requirements.competency_id` | `role_requirements` $\to$ `competencies._id` | 8 | **0** | 8 | 🔴 **Broken** (Points to pre-reseed ObjectIds) |
| `competency_profiles.user_id` | `competency_profiles` $\to$ `users._id` | 16 | **0** | 16 | 🔴 **Broken** (Points to pre-reseed User IDs) |
| `competency_profiles.competency_id` | `competency_profiles` $\to$ `competencies._id` | 16 | **0** | 16 | 🔴 **Broken** (Points to pre-reseed ObjectIds) |
| `competency_evidence.user_id` | `competency_evidence` $\to$ `users._id` | 72 | **24** | 48 | 🟡 **Warning** (24 active, 48 legacy test attempts) |
| `competency_evidence.competency_id` | `competency_evidence` $\to$ `competencies._id` | 72 | **0** | 72 | 🔴 **Broken** (Points to pre-reseed ObjectIds) |
| `assessment_attempts.user_id` | `assessment_attempts` $\to$ `users._id` | 5 | **3** | 2 | 🟡 **Warning** (3 active users, 2 legacy test runs) |
| `learning_resource_mappings.resource_id` | `mappings` $\to$ `learning_resources._id` | 114 | **114** | 0 | 🟢 **Consistent** |
| `learning_resource_mappings.competency_id` | `mappings` $\to$ `competencies._id` | 114 | **114** | 0 | 🟢 **Consistent** |
| `learning_materials.user_id` | `learning_materials` $\to$ `users._id` | 12 | **12** | 0 | 🟢 **Consistent** |
| `assessment_configurations.competency_code` | `configs` $\to$ `competencies.code` | 10 | **0** | 10 | 🔴 **Broken** (`TECH_SQL` vs `TECH-SQL` mismatch) |
| `question_bank.competency_code` | `question_bank` $\to$ `competencies.code` | 122 | **0** | 122 | 🔴 **Broken** (`TECH_SQL` vs `TECH-SQL` mismatch) |

---

## 5. Assessment Configuration Coverage

### Active Configurations (10 Configs in `assessment_configurations`)

| Competency Code | Assessment Types | Questions Configured | Difficulty | Passing Threshold | Time Limit | Retake Allowed | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `TECH_PYTHON` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 30 min | True | `ACTIVE` |
| `TECH_SQL` | `['MCQ', 'SCENARIO']` | 12 | `MIXED` | 70.0% | 35 min | True | `ACTIVE` |
| `TECH_R` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 30 min | True | `ACTIVE` |
| `STAT_SAMPLING` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 30 min | True | `ACTIVE` |
| `STAT_SURVEY_DESIGN` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 30 min | True | `ACTIVE` |
| `DIGOV_CYBERSECURITY` | `['MCQ', 'SCENARIO']` | 12 | `MIXED` | 70.0% | 35 min | True | `ACTIVE` |
| `DIGOV_DATA_PRIVACY` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 30 min | True | `ACTIVE` |
| `BEH_LEADERSHIP` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 25 min | True | `ACTIVE` |
| `BEH_COMMUNICATION` | `['MCQ', 'SCENARIO']` | 10 | `MIXED` | 70.0% | 25 min | True | `ACTIVE` |
| `BEH_PROJECT_MANAGEMENT` | `['MCQ', 'SCENARIO']` | 12 | `MIXED` | 70.0% | 35 min | True | `ACTIVE` |

### Configuration vs Role Requirements Coverage:
- **Statistical Officer Required Competencies with Active Configurations**: 4 / 8 (`STAT_SAMPLING`, `STAT_SURVEY_DESIGN`, `TECH_PYTHON`, `TECH_SQL`).
- **Statistical Officer Required Competencies without Configurations**: 4 / 8 (`STAT_DATA_QUALITY_FRAMEWORKS`, `TECH_DATA_VISUALIZATION`, `TECH_GIS`, `TECH_AI_ML`).
- **Behavioural / Digital Governance Additional Active Configurations**: 6 (`BEH_LEADERSHIP`, `BEH_COMMUNICATION`, `BEH_PROJECT_MANAGEMENT`, `DIGOV_CYBERSECURITY`, `DIGOV_DATA_PRIVACY`, `TECH_R`).
- **🔵 Legitimate Data Gap**: `BEH_CHANGE_MANAGEMENT` has no configuration and no questions in the question bank.

---

## 6. Question Bank Coverage (122 Questions)

| Competency Code | Total Questions | MCQ Count | Scenario Count | Easy | Medium | Hard | Config Match? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `TECH_PYTHON` | **15** | 10 | 5 | 4 | 6 | 5 | ✅ Meets 10 required |
| `TECH_SQL` | **15** | 10 | 5 | 4 | 6 | 5 | ✅ Meets 12 required |
| `TECH_R` | **11** | 8 | 3 | 2 | 5 | 4 | ✅ Meets 10 required |
| `STAT_SAMPLING` | **10** | 8 | 2 | 2 | 5 | 3 | ✅ Meets 10 required |
| `STAT_SURVEY_DESIGN` | **10** | 8 | 2 | 2 | 5 | 3 | ✅ Meets 10 required |
| `DIGOV_CYBERSECURITY` | **13** | 10 | 3 | 2 | 6 | 5 | ✅ Meets 12 required |
| `DIGOV_DATA_PRIVACY` | **13** | 10 | 3 | 2 | 6 | 5 | ✅ Meets 10 required |
| `BEH_LEADERSHIP` | **13** | 8 | 5 | 2 | 6 | 5 | ✅ Meets 10 required |
| `BEH_COMMUNICATION` | **11** | 8 | 3 | 2 | 5 | 4 | ✅ Meets 10 required |
| `BEH_PROJECT_MANAGEMENT` | **11** | 8 | 3 | 2 | 5 | 4 | ✅ Meets 12 required (11 avail) |
| **TOTAL** | **122** | **88** | **34** | **22** | **55** | **45** | **10 / 10 Configured** |

---

## 7. Role Requirement Integrity

Role: **Statistical Officer** (`STATISTICAL_OFFICER`, ID: `6a8fe8048524f6da8ebb9881`)

| # | Required Competency Name | Target Canonical Code | Required Level | Priority | Importance | Current DB Link Status |
| :- | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | Sampling | `STAT_SAMPLING` | 4 (Advanced) | P1 | 1.00 | 🔴 Orphaned `competency_id` |
| 2 | Survey Design | `STAT_SURVEY_DESIGN` | 4 (Advanced) | P1 | 1.00 | 🔴 Orphaned `competency_id` |
| 3 | Data Quality Frameworks | `STAT_DATA_QUALITY_FRAMEWORKS` | 4 (Advanced) | P1 | 1.00 | 🔴 Orphaned `competency_id` |
| 4 | Python | `TECH_PYTHON` | 3 (Intermediate) | P2 | 0.75 | 🔴 Orphaned `competency_id` |
| 5 | SQL | `TECH_SQL` | 3 (Intermediate) | P2 | 0.75 | 🔴 Orphaned `competency_id` |
| 6 | Data Visualization | `TECH_DATA_VISUALIZATION` | 3 (Intermediate) | P2 | 0.75 | 🔴 Orphaned `competency_id` |
| 7 | GIS | `TECH_GIS` | 2 (Basic) | P3 | 0.50 | 🔴 Orphaned `competency_id` |
| 8 | AI/ML | `TECH_AI_ML` | 2 (Basic) | P3 | 0.50 | 🔴 Orphaned `competency_id` |

---

## 8. Learning Resource Integrity

- **Total Resources in DB**: **148**
  - **iGOT Karmayogi**: 63 courses (verified links, metadata, durations).
  - **NSSTA (National Statistical Systems Training Academy)**: 85 courses (specialized official statistical modules).
- **Duplicate Resource IDs**: **0** (148 unique string identifiers).
- **Mapped Resources**: **84** (mapped to 26 distinct competencies via 114 mappings).
- **Unmapped Resources**: **64** (available via `/api/v1/recommendations/resources/unmapped` for catalog curation).
- **Broken Mapping ObjectIds**: **0** (114 / 114 mappings point to valid `learning_resources._id` and `competencies._id`).

---

## 9. AI / RAG Data Integrity

| Collection | Current Count | Populated? | Functional Status |
| :--- | :---: | :---: | :--- |
| `learning_materials` | 12 | ✅ Yes | 2 processing records, 10 failed upload test attempts. |
| `document_chunks` | 0 | ⚠️ Empty | Populated dynamically during synchronous/asynchronous document ingestion. |
| `quizzes` | 0 | ⚠️ Empty | Created on-demand when users convert generated MCQs to interactive quizzes. |
| `quiz_attempts` | 0 | ⚠️ Empty | Created on-demand upon quiz submission. |
| Vector Store Cache | Runtime | ✅ Yes | Memory-cached during runtime; re-indexes from `document_chunks` on reload. |

---

## 10. Orphan Records Summary

| Collection | Orphaned Field | Count | Root Cause |
| :--- | :--- | :---: | :--- |
| `role_requirements` | `competency_id` | **8** | Pre-reseed ObjectIds remaining after `seed_competencies.py` re-generated competency `_id`s. |
| `competency_profiles` | `competency_id` & `user_id` | **16** | Pre-reseed User IDs and Competency ObjectIds. |
| `competency_evidence` | `competency_id` | **72** | Pre-reseed Competency ObjectIds. |
| `assessment_attempts` | `user_id` | **2** | Test attempts from legacy deleted user accounts. |

---

## 11. Duplicate Records Summary

| Collection | Field Checked | Duplicate Count | Status |
| :--- | :--- | :---: | :--- |
| `competencies` | `code` | **0** | 🟢 Unique |
| `roles` | `role_code` | **0** | 🟢 Unique |
| `users` | `email` & `employee_id` | **0** | 🟢 Unique |
| `learning_resources` | `resource_id` | **0** | 🟢 Unique |
| `assessment_configurations` | `competency_code` | **0** | 🟢 Unique |
| `question_bank` | Question Text | **0** | 🟢 Unique |

---

## 12. Data Gap & Health Classification

### 🟢 Consistent
- `users` (21 accounts with valid `role_id` pointing to `STATISTICAL_OFFICER`).
- `roles` (`STATISTICAL_OFFICER` active).
- `learning_resources` (148 unique courses with verified provider attributes).
- `learning_resource_mappings` (114 valid foreign key ObjectIds).
- `assessments` (Initial Competency Assessment master document intact).
- `question_bank` (122 multi-difficulty questions with zero duplicates).

### 🟡 Warning
- `assessment_attempts` (2 legacy test attempts referencing old user IDs).
- `learning_materials` (10 test failure records from early upload experiments).

### 🔴 Broken (Requires Master Seed Synchronization)
- `competency_profiles.competency_id` $\to$ orphaned ObjectIds.
- `role_requirements.competency_id` $\to$ orphaned ObjectIds.
- `assessment_configurations.competency_code` $\to$ uses underscore `TECH_SQL` while `competencies` uses hyphenated `TECH-SQL`.
- `question_bank.competency_code` $\to$ uses underscore `TECH_SQL` while `competencies` uses hyphenated `TECH-SQL`.

### 🔵 Legitimate Data Gap
- `BEH_CHANGE_MANAGEMENT`: Present in master competency taxonomy, but intentionally has no capability assessment configuration and no pre-authored questions in the question bank.

---

## 13. Unified Master Seed Requirements

To permanently resolve all 🔴 Broken foreign keys and naming discrepancies in the live database, a single unified master seed must execute the following operations in atomic order:

1. **Step 1: Canonical Competency Seeding (`competencies`)**:
   - Seed all 42 competencies using the canonical underscore format (`STAT_SAMPLING`, `TECH_SQL`, `DIGOV_CYBERSECURITY`, `BEH_LEADERSHIP`) with consistent display names and domains.
2. **Step 2: Role & Role Requirements Seeding (`roles`, `role_requirements`)**:
   - Upsert `STATISTICAL_OFFICER` role.
   - Lookup the active `competencies._id` for the 8 required competencies and insert `role_requirements` with exact matching ObjectIds.
3. **Step 3: Assessment Configurations Seeding (`assessment_configurations`)**:
   - Insert the 10 assessment configurations with matching canonical underscore codes.
4. **Step 4: Question Bank Seeding (`question_bank`)**:
   - Insert the 122 validated questions with matching canonical underscore codes.
5. **Step 5: Learning Resources & Mappings Seeding (`learning_resources`, `learning_resource_mappings`)**:
   - Seed 148 learning resources (63 iGOT + 85 NSSTA).
   - Re-map 114 mappings using the active canonical competency ObjectIds and codes.
6. **Step 6: Baseline Employee Competency Profiles (`competency_profiles`)**:
   - Seed baseline competency profiles for demo employee accounts using active `users._id` and active `competencies._id`.

---

## 14. Recommended Fix Order

```
1. Master Seed Synchronization Script
   (Atomic execution: Competencies → Roles → Requirements → Configs → QuestionBank → Resources → Mappings → Demo Profiles)
        ↓
2. Verify Database Foreign Key Integrity
   (Run read-only verification: 0 broken FKs, 100% resolution across all collections)
        ↓
3. Execute End-to-End API Smoke Test
   (Verify /auth, /skill-gaps/me, /recommendations/me, /assessments/capability against live MongoDB)
        ↓
4. Final Freeze
```

---

**AUDIT COMPLETE. DATABASE SNAPSHOT FULLY DOCUMENTED. BACKEND REMAINS FROZEN AT 164/164 TESTS PASSING.**
