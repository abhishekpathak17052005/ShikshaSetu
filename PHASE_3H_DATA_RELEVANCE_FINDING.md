# Phase 3H — Data Relevance Finding Report

**Reference**: Task Rule 33 (Critical Course Relevance Check)  
**Date**: September 2026  
**Subject**: Role & Curriculum Data Alignment for Ministry of Education Personnel  

---

## 1. Summary of Finding

During the Phase 3H inspection of the **Learning Tracker** (`OfficialLearning.tsx`), **Personalized Recommendations** (`OfficialRecommendations.tsx`), and the local curriculum catalog (`courseContent.ts`), we audited whether personnel under the **Ministry of Education** (such as *Education & Curriculum Officer*, *Teacher*, or *Curriculum Specialist*) are served role-inappropriate statistical or cybersecurity learning resources.

---

## 2. Detailed Observations

| Attribute | Details |
|---|---|
| **Affected Pages** | `OfficialRecommendations.tsx`, `OfficialLearning.tsx`, `OfficialSkillGaps.tsx` |
| **API Endpoints** | `GET /api/v1/recommendations/me`, `GET /api/v1/learning-activities`, `GET /api/v1/skill-gaps/me` |
| **Observed Resource Catalog** | Primary static catalog entries in `courseContent.ts` are heavily weighted towards MoSPI domain topics: `TECH_DATA_VISUALIZATION` ("Data Visualization & Dashboards"), `STAT_SAMPLING` ("Statistical Sampling & Large-Scale Surveys"), and `TECH_PYTHON` ("Python Programming for Public Administration"). |
| **Expected Role Relevance for Education Users** | Ministry of Education officers require pedagogical, foundational literacy/numeracy (FLN), NEP 2020 curriculum framework, assessment design, and classroom communication competencies (`EDU_PEDAGOGY`, `EDU_CURRICULUM_DESIGN`, `BEH_COMMUNICATION`, `GOV_ETHICS`). |
| **Behavior Under Dynamic Resolution** | When an Education user is authenticated, the backend dynamic role resolver correctly resolves their role to `EDUCATION_OFFICER` and assigns appropriate competencies. However, when the frontend loads detailed curriculum chapters for these competencies, `getCourseCurriculum()` falls back to a dynamically synthesized 3-chapter generic template because explicit rich chapter data is only authored for the 4 initial MoSPI competencies. |
| **Probable Cause** | Initial seed data focused on the MoSPI pilot dataset; rich course chapter content in `courseContent.ts` was authored specifically for statistical competencies before the multi-department dynamic role resolution was added in Phase 3F/3G. |
| **Severity** | **Low to Moderate (Content/Pedagogy Depth)** — Does NOT break functionality, API contracts, RBAC, or scoring; fallback curriculum generator safely renders valid structured chapters, objectives, and case studies. |

---

## 3. Recommendation (Post-Animation Task)

1. In a subsequent content-seeding pass, author rich domain-specific chapters for `EDU_PEDAGOGY`, `EDU_CURRICULUM_DESIGN`, and `BEH_COMMUNICATION` within `courseContent.ts` to provide deep domain parity with the MoSPI statistical courses.
2. Maintain strict presentation neutrality in animation components so recommendation reason badges dynamically reflect the user's actual mapped competency code.
3. Keep business logic and backend ranking models untouched during animation tasks.
