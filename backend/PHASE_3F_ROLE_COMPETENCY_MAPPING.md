# Phase 3F — Role & Department-Specific Competency Mapping Architecture

> [!IMPORTANT]
> **Data Governance Notice**:
> "Current role competency requirements are prototype/configurable application mappings and are not authoritative government policy."
> Every role and role requirement record in the system is explicitly stamped with:
> - `mapping_status = "PROTOTYPE_CONFIGURED"`
> - `source = "INTERNAL_PROTOTYPE_V1"`
> - `framework_status = "prototype"`
> 
> They must never be represented as official DoPT, MoSPI, or iGOT gazetted policies.

---

## 1. Problem Being Solved

Prior to Phase 3F, civil service personnel belonging to different ministries (e.g. Education, MeitY, Finance) were receiving the exact same competency taxonomy and global training recommendations.

The **Role & Department Competency Mapping Layer** establishes an authoritative application-level mapping pipeline:

```text
User Identity (Department + Designation)
       ↓
Deterministic Role Resolver (app/roles/resolver.py)
       ↓
Resolved Role & Applicable Competency Requirements (role_requirements)
       ↓
Active Competency Profiles (Current Level vs Required Level)
       ↓
Role-Scoped Skill Gaps (app/skill_gaps/service.py)
       ↓
Constrained Candidate Generation (Resource → Competency Mappings)
       ↓
5-Factor Scoring & Ranked Recommendations (app/learning_resources/scoring.py)
```

---

## 2. Configured Departments (7 Ministries / Groups)

1. **Ministry of Statistics & Programme Implementation (MoSPI)** / National Sample Survey Office (NSSO)
2. **Ministry of Education** / Department of School Education & Literacy / Higher Education
3. **Ministry of Electronics and Information Technology (MeitY)**
4. **Ministry of Finance** / Department of Expenditure / Economic Affairs
5. **Ministry of Health and Family Welfare (MoHFW)**
6. **Ministry of Rural Development (MoRD)**
7. **Department of Personnel and Training (DoPT)** / Ministry of Personnel, Public Grievances and Pensions

---

## 3. Configured Roles (10 Application Roles)

1. `STATISTICAL_OFFICER` (MoSPI)
2. `DATA_ANALYST_OFFICER` (MoSPI)
3. `EDUCATION_OFFICER` (MoE)
4. `DIGITAL_LEARNING_SPECIALIST` (MoE)
5. `DIGITAL_GOVERNANCE_ARCHITECT` (MeitY)
6. `CYBERSECURITY_GOVERNANCE_OFFICER` (MeitY)
7. `PUBLIC_FINANCIAL_MANAGEMENT_OFFICER` (MoF)
8. `PUBLIC_HEALTH_DATA_OFFICER` (MoHFW)
9. `RURAL_DEVELOPMENT_OFFICER` (MoRD)
10. `CAPACITY_BUILDING_OFFICER` (DoPT)

---

## 4. Designation Aliases

| Role Code | Role Name | Designation Aliases |
| :--- | :--- | :--- |
| `STATISTICAL_OFFICER` | Statistical Officer | Statistical Officer, Junior Statistical Officer (JSO), Senior Statistical Officer (SSO), ISS Probationer |
| `DATA_ANALYST_OFFICER` | Data Analyst Officer | Data Analyst, Statistical Assistant, Data Officer |
| `EDUCATION_OFFICER` | Education & Curriculum Officer | Teacher, Senior Teacher (PGT/TGT), Headmaster / Principal, Block Education Officer (BEO), District Education Officer (DEO), Curriculum Specialist |
| `DIGITAL_LEARNING_SPECIALIST` | Digital Pedagogy & EdTech Specialist | Digital Learning Specialist, EdTech Coordinator, Smart Classroom Lead, Online Assessment Officer |
| `DIGITAL_GOVERNANCE_ARCHITECT` | Informatics Officer / Digital Governance Architect | Informatics Officer, Scientist 'B', Systems Analyst, Digital Architecture Lead |
| `CYBERSECURITY_GOVERNANCE_OFFICER` | Cybersecurity Governance Officer | Information Security Officer, Cyber Security Analyst, IT Security Lead, CISO Analyst |
| `PUBLIC_FINANCIAL_MANAGEMENT_OFFICER` | Accounts Officer (AAO / AO) | Assistant Accounts Officer, Accounts Officer, Financial Analyst, Budget Officer |
| `PUBLIC_HEALTH_DATA_OFFICER` | Public Health Data Officer | Health Statistician, Public Health Analyst, Epidemiological Data Officer |
| `RURAL_DEVELOPMENT_OFFICER` | Rural Development & Field Programme Officer | Block Development Officer, Programme Manager, Field Coordinator |
| `CAPACITY_BUILDING_OFFICER` | Capacity Building & Training Officer | Training Coordinator, Under Secretary (Training), Capacity Building Specialist |

---

## 5. 42 Canonical Competencies Taxonomy

The 42 civil service competencies remain organized into 4 standardized domains:
- **Statistical & Analytical (14)**: `STAT_SAMPLING`, `STAT_SURVEY_DESIGN`, `STAT_DATA_QUALITY_FRAMEWORKS`, `STAT_ESTIMATION_TECHNIQUES`, `STAT_NATIONAL_ACCOUNTS`, `STAT_MACROECONOMIC_INDICATORS`, `STAT_PRICE_INDEX_COMPILATION`, `STAT_INDEX_THEORY`, `STAT_FIELD_OPERATIONS`, `STAT_DATA_PROCESSING`, `STAT_ADMINISTRATIVE_DATA_SYSTEMS`, `STAT_AGRICULTURAL_STATISTICS`, `STAT_INDUSTRIAL_STATISTICS`, `STAT_DEMOGRAPHIC_ESTIMATION`.
- **Technical & Computational (11)**: `TECH_PYTHON`, `TECH_R_STATISTICAL`, `TECH_SQL`, `TECH_DATA_VISUALIZATION`, `TECH_BIG_DATA_SYSTEMS`, `TECH_MACHINE_LEARNING_BASICS`, `TECH_GIS_SPATIAL_ANALYSIS`, `TECH_DATA_CLEANING`, `TECH_SURVEY_DATA_PLATFORMS`, `TECH_AI_ASSISTIVE_TOOLS`, `TECH_REPORT_AUTOMATION`.
- **Digital Governance (7)**: `DIGOV_CYBERSECURITY`, `DIGOV_PRIVACY_ETHICS`, `DIGOV_E_GOVERNANCE_SYSTEMS`, `DIGOV_OPEN_DATA_GOVERNANCE`, `DIGOV_METADATA_STANDARDS`, `DIGOV_INTEROPERABILITY_FRAMEWORKS`, `DIGOV_DIGITAL_PUBLIC_INFRASTRUCTURE`.
- **Behavioural & Managerial (10)**: `BEH_COMMUNICATION`, `BEH_ETHICS`, `BEH_LEADERSHIP`, `BEH_DECISION_MAKING`, `BEH_PROBLEM_SOLVING`, `BEH_CONTINUOUS_LEARNING`, `BEH_ADAPTABILITY`, `BEH_STAKEHOLDER_ENGAGEMENT`, `BEH_PUBLIC_SERVICE_ORIENTATION`, `BEH_TEAMWORK`.

---

## 6. Role → Competency Architecture

- **Collection**: `role_requirements`
- **Purpose**: Defines what an official in a specific job role *needs to know*.
- **Fields**: `{role_id, competency_id, competency_code, required_level, priority, importance, mapping_status, source, active}`
- **Requirement Count**: 4 to 6 balanced requirements per role (48 total requirements across 10 roles).

---

## 7. Resource → Competency Architecture

- **Collection**: `learning_resource_mappings`
- **Purpose**: Defines what a specific iGOT course or NSSTA training module *teaches*.
- **Fields**: `{resource_id, competency_id, competency_code, provider, mapping_type: "DERIVED", confidence: 0.45 - 0.80}`
- **Coverage**: 114 mapped resources. 34 unmapped resources remain in the general catalogue for search and manual browsing, isolated from recommendation candidate generation.

---

## 8. Skill-Gap Dependency

- `app/skill_gaps/service.py` evaluates gaps strictly by comparing `required_level` (from `role_requirements` matching `user["role_id"]`) against `current_level` (from `competency_profiles`).
- Out-of-role competencies are never evaluated as active skill gaps.

---

## 9. Recommendation Dependency

- **Pipeline**: Active Skill Gaps $\rightarrow$ Competency Codes $\rightarrow$ Resource Mappings $\rightarrow$ Candidate Pool $\rightarrow$ 5-Factor Scoring Formula $\rightarrow$ Ranked Recommendations.
- **Filter $\rightarrow$ Score $\rightarrow$ Rank**: Only resources mapped to an active gap enter the scoring engine. Unmapped resources or resources mapped to non-gap competencies are excluded.

---

## 10. Assessment Applicability

- `AdaptiveAssessmentService.start_session()` validates whether the requested competency exists in the official's `role_requirements`.
- Non-applicable competencies are rejected with `HTTP 403 Forbidden`.

---

## 11. AI Context Dependency

- `app/assistant/context.py` constructs LLM prompt context containing the official's department, resolved role name, active competency profiles, and top skill gaps.
- It never dumps all 42 competencies or generates ungrounded requirements.

---

## 12. Admin Analytics Dependency

- Admin endpoints (`/admin/dashboard`, `/admin/workforce`, `/admin/competencies`, `/admin/skill-gaps`, `/admin/users`) support `department: Optional[str] = Query(None)`.
- Gap distributions aggregate only active competency profiles with deficits.

---

## 13. Evidence Preservation

- `competency_evidence`, `learning_activities`, `quiz_attempts`, and `adaptive_assessment_sessions` are immutable ledgers.
- Role changes never delete historical evidence.

---

## 14. Role-Change Reconciliation

- `reconcile_user_competencies(database, user_id, new_role_id)`:
  - Idempotent execution.
  - New role-required competencies are initialized (`current_level: None`, `confidence: 0.0`).
  - Obsolete competencies are marked `status: "inactive"`.
  - Existing applicable competency levels are preserved.

---

## 15. Prototype Data Governance & Official Replacement Path

When official, gazetted competency frameworks are published:
1. Update `source` to `"DOPT_CBC_OFFICIAL_V1"`.
2. Update `mapping_status` to `"OFFICIAL_GAZETTED"`.
3. Re-run `reconcile_user_competencies()` to update benchmark levels without breaking historical records.
