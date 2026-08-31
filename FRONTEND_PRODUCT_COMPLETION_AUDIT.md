# ShikshaSetu — Frontend Product Experience & Architectural Audit
**Product**: ShikshaSetu — AI-enabled Skill Intelligence & Learning Platform  
**Team**: Team Kinetics (SIH 2026)  
**Audit Date**: August 31, 2026  
**Auditor**: Senior Full-Stack & Frontend Product Architect  
**Scope**: Complete Frontend Read-Only Audit across Official, Trainer, and Admin Roles  

---

## 1. Executive Summary

This document presents a comprehensive, read-only architectural and product audit of the **ShikshaSetu** frontend application. 

While the FastAPI + MongoDB backend is hardened, fully RBAC-enabled, and verified with **218 passing automated tests**, the frontend currently presents an uneven state:
1. **Trainer Portal (Phase 2C)** is newly modularized, typed, and fully connected to live backend endpoints.
2. **Official Experience** is largely concentrated inside a monolithic file (`LiveHome.tsx` / `Home.tsx`) with missing dedicated views for Quizzes, Evidence timeline, and Progress history, as well as an outdated legacy mock file (`Home.tsx`).
3. **Admin Experience** is currently a visual layout stub without live workforce analytics views.
4. **Architectural Principle ("Learning ≠ Proven Competency")** is respected in backend evidence models, but requires clear UI reinforcement on the Official learning and quiz feedback screens.
5. **API Client Duplication** exists between `src/lib/api.ts` (fetch-based, centralized, active) and `src/services/api.ts` (axios-based, legacy token keys).

---

## 2. Directory & Component Inventory

```
frontend/client/src/
├── App.tsx                          (Role-based router & app shell)
├── index.css                        (Tailwind design system tokens)
├── const.ts                         (Route & config constants)
├── main.tsx                         (Vite entry point)
├── components/
│   ├── ErrorBoundary.tsx            (Global react error boundary)
│   ├── LearningActivityCard.tsx     (Learning activity card)
│   ├── ManusDialog.tsx              (Dialog utility component)
│   ├── Map.tsx                      (Visual dependency graph)
│   └── ui/                          (Shadcn UI primitives)
├── contexts/
│   ├── AuthContext.tsx              (JWT auth state machine & session restore)
│   └── ThemeContext.tsx             (Theme provider)
├── hooks/
│   ├── useLearningActivities.ts     (Hook for learning activity lifecycle)
│   ├── useComposition.ts            (Input composition helper)
│   ├── useMobile.tsx                (Mobile breakpoint detector)
│   └── usePersistFn.ts              (Function ref memoization)
├── layouts/
│   ├── OfficialLayout.tsx           (Learner layout with capability pathway)
│   ├── TrainerLayout.tsx            (Trainer workspace layout with warm theme)
│   └── AdminLayout.tsx              (Admin analytics layout with purple theme)
├── lib/
│   ├── api.ts                       (Central typed API client)
│   └── utils.ts                     (Classname utilities)
├── pages/
│   ├── LoginPage.tsx                (Full login & registration page)
│   ├── LiveHome.tsx                 (Monolithic Official portal state machine)
│   ├── Home.tsx                     (Legacy mock/static demo page)
│   ├── LearningPage.tsx             (Focused learning activity page)
│   ├── NotFound.tsx                 (404 fallback page)
│   └── trainer/
│       ├── TrainerDashboard.tsx     (KPI stats & pipeline visualizer)
│       ├── TrainerMaterials.tsx     (Material repo & drag-and-drop uploader)
│       ├── TrainerQuestionGenerator.tsx (AI question generator & RAG tracker)
│       ├── TrainerQuestionReview.tsx    (Review studio with edit/approve/reject)
│       ├── TrainerQuizStudio.tsx        (Draft builder, publisher & assigner)
│       └── TrainerLearnerResults.tsx    (Learner attempts & feedback modal)
├── services/
│   └── api.ts                       (Deprecated axios duplicate client)
└── types/                           (Ambient TypeScript declarations)
```

---

## 3. Detailed Audit Matrix

| Audit Area | Current Status | Findings & Specific Location | Action Required |
|---|---|---|---|
| **Role-Based Routing** | 🟡 PARTIAL | `App.tsx` correctly checks `user.access_role` (`TRAINER` $\to$ `TrainerApp`, `ADMIN` $\to$ `AdminApp`, `OFFICIAL`/`EMPLOYEE` $\to$ `OfficialApp`). However, `OfficialApp` loads `LiveHome.tsx` directly instead of using modular pages with `OfficialLayout.tsx`. | Modularize Official pages into `src/pages/official/` wrapped by `OfficialLayout`. |
| **Authentication Flow** | 🟢 COMPLETE | `LoginPage.tsx` & `AuthContext.tsx` call `POST /api/v1/auth/login` and `GET /api/v1/auth/me`. Session is restored via `shikshasetu_token`. | Remove legacy fallback keys (`shikshasetu_demo_token`). |
| **Official Dashboard** | 🟡 PARTIAL | `LiveHome.tsx` Dashboard view renders mapped competencies and gaps from backend API, but lacks detailed domain breakdowns, recent learning hours, and clear capability assessment status card. | Build a dedicated `OfficialDashboard.tsx` with standard KPI cards, domain distribution, and next best action. |
| **My Competencies Page** | 🟢 COMPLETE | `LiveHome.tsx` Competencies view pulls real competency models from `/competencies` and overlays gap profile from `/skill-gaps/me`. | Extract into standalone `MyCompetencies.tsx` component with domain filtering and search. |
| **Skill Gaps Page** | 🟢 COMPLETE | Renders real backend gap calculations (`/skill-gaps/me`) with priority badges, current/required levels, and "View Recommendations" CTA. | Extract into standalone `SkillGaps.tsx`. |
| **Recommendations Page** | 🟢 COMPLETE | Consumes `GET /recommendations/me` and 5-factor scoring explanation details from backend. | Extract into standalone `Recommendations.tsx` with 1-click "Start Learning" activity creation. |
| **My Learning Page** | 🟡 PARTIAL | `LearningPage.tsx` exists and hooks to `/learning-activities`, but in `LiveHome.tsx`, "Learning" was conflated with trainer material upload/generation. | Create clean `MyLearning.tsx` that lists active/completed learning activities, tracks progress %, logs supporting evidence on completion, and clearly states: *"Your competency level has not changed yet. Take a formal capability assessment to validate."* |
| **Official Quizzes Page** | 🔴 MISSING | Official does not have a dedicated Quizzes view listing assigned trainer quizzes (`GET /api/v1/quizzes/assigned`), attempting quizzes, and viewing score/explanations without leaking answers. | Build dedicated `OfficialQuizzes.tsx` with Available, In-Progress, and Completed quiz attempt lifecycle. |
| **Evidence Timeline** | 🔴 MISSING | Official does not have a dedicated Evidence page distinguishing **Supporting Evidence** (confidence 0.3, learning completions) from **Authoritative Evidence** (confidence 0.8+, formal capability assessments). | Build dedicated `OfficialEvidence.tsx` timeline. |
| **Official Progress Page** | 🔴 MISSING | No dedicated Progress page showing assessment history, learning hours, quizzes completed, and gap reduction over time. | Build dedicated `OfficialProgress.tsx` with real historical metrics (and honest empty state if new). |
| **Trainer Portal (All 6 Pages)** | 🟢 COMPLETE | Complete workflow implemented: Dashboard, Materials, AI Generator, Question Review (Edit/Approve/Reject), Quiz Studio (Publish/Assign), Learner Results & Feedback. | Verified with 0 build errors. |
| **Admin Portal (All Pages)** | 🔴 MISSING / STUB | `AdminLayout.tsx` exists with navigation, but `AdminApp` in `App.tsx` currently renders a placeholder stub. | Build dedicated Admin analytics pages: `AdminDashboard.tsx`, `WorkforceOverview.tsx`, `CompetencyAnalytics.tsx`, `SkillGapAnalytics.tsx`, `TrainingEffectiveness.tsx`, `EmergingSkills.tsx`, `CapacityPlanning.tsx`, `AdminUsers.tsx`, `AdminReports.tsx`. |
| **API Client Unification** | 🔴 DUPLICATE | `src/lib/api.ts` vs `src/services/api.ts`. `src/services/api.ts` uses stale token key `shikshasetu_demo_token`. | Consolidate everything into `src/lib/api.ts`, update `useLearningActivities.ts` to use `src/lib/api.ts`, and eliminate `src/services/api.ts`. |
| **Capability Assessment Route Alignment** | 🔴 MISMATCH | In `src/lib/api.ts`, capability assessments pointed to `/capability-assessments` instead of backend route `/api/v1/assessments/capability`. | Align endpoint paths in `src/lib/api.ts`. |
| **Mock / Static Data** | 🔴 DEAD CODE | `Home.tsx` contains static arrays (`gaps`, `resources`, `assessmentQuestions`) that do not hit the backend. | Deprecate/remove `Home.tsx` in favor of modular role-based architecture. |

---

## 4. Architectural Principle Verification: "Learning ≠ Proven Competency"

### Backend Baseline (Verified)
- `POST /learning-activities/{id}/complete` records evidence with type `LEARNING_ACTIVITY` and confidence `0.3`. It does **NOT** modify the official's authoritative competency level.
- `POST /assessments/capability/{id}/submit` and `POST /assessments/{id}/submit` record evidence with confidence `0.8 - 1.0` and update the authoritative competency profile and recalculate skill gaps.

### Frontend Audit Finding
In `LiveHome.tsx` (lines 520-542), the legacy quiz submission banner displayed:
`"Updated Level: 4.2 / 5.0 · Evidence Logged"`.
This blurred the boundary between informal learning quizzes and formal capability assessments.

### Mandatory UI Contract for Official Experience
1. When an official finishes a learning resource or practice quiz:
   - Status: `"Learning Activity Completed"`
   - Evidence: `"Supporting Evidence Recorded (Confidence: 0.30)"`
   - Competency Note: `"Your competency level remains unchanged. Complete a formal capability assessment to validate capability growth."`
   - Action CTA: `"Take Capability Assessment"`
2. When an official finishes a formal Capability Assessment:
   - Status: `"Formal Capability Assessment Scored"`
   - Evidence: `"Authoritative Assessment Evidence Recorded (Confidence: 0.85)"`
   - Competency Note: `"Competency profile updated from 2.5 to 3.8. Skill gaps recalculated."`

---

## 5. Role-by-Role Gap & Target Architecture

### Role 1: Official / Employee (Learner)
Target Folder: `frontend/client/src/pages/official/`

| Page | Required Route / Nav ID | Source Data / Backend Endpoint | Implementation Status |
|---|---|---|---|
| **Official Dashboard** | `Dashboard` | `GET /skill-gaps/me`, `GET /competencies`, `GET /learning-activities` | 🟡 Needs modular component |
| **My Competencies** | `My Competencies` | `GET /competencies`, `GET /skill-gaps/me` | 🟡 Needs modular component |
| **Assessments** | `Assessments` | `POST /assessments`, `GET /assessments/{id}`, `POST /assessments/{id}/submit`, `GET /assessments/capability` | 🟡 Needs modular component |
| **Skill Gaps** | `Skill Gaps` | `GET /skill-gaps/me` | 🟡 Needs modular component |
| **Recommendations** | `Recommendations` | `GET /recommendations/me` | 🟡 Needs modular component |
| **My Learning** | `My Learning` | `GET /learning-activities`, `PUT /learning-activities/{id}`, `POST /learning-activities/{id}/complete` | 🟡 Needs modular component |
| **Quizzes** | `Quizzes` | `GET /quizzes/assigned`, `GET /quizzes/{id}`, `POST /quizzes/{id}/submit` | 🔴 Missing dedicated component |
| **Evidence** | `Evidence` | `GET /learning-activities` (evidence list) + `/assessments` results | 🔴 Missing dedicated component |
| **Progress** | `Progress` | `GET /learning-activities`, `GET /skill-gaps/me` history | 🔴 Missing dedicated component |
| **Profile** | `Profile` | `GET /users/me`, `PUT /users/me` | 🟡 Needs modular component |

### Role 2: Trainer (Content & Assessments)
Folder: `frontend/client/src/pages/trainer/`

| Page | Nav ID | Backend Endpoint | Status |
|---|---|---|---|
| **Trainer Dashboard** | `Dashboard` | `GET /trainer/dashboard` | 🟢 Complete & Verified |
| **Learning Materials** | `Learning Materials` | `GET /trainer/materials` | 🟢 Complete & Verified |
| **Upload Material** | `Upload Material` | `POST /learning-materials/upload` | 🟢 Complete & Verified |
| **AI Question Generator** | `AI Question Generator` | `POST /trainer/materials/{id}/generate` | 🟢 Complete & Verified |
| **Question Review** | `Question Review` | `GET/PUT/POST /trainer/questions/*` | 🟢 Complete & Verified |
| **Quiz Studio** | `Quiz Studio` | `POST/GET /trainer/quizzes/*`, `POST /trainer/quizzes/{id}/assign` | 🟢 Complete & Verified |
| **Published Quizzes** | `Published Quizzes` | `GET /trainer/quizzes` | 🟢 Complete & Verified |
| **Learner Results** | `Learner Results` | `GET /trainer/quizzes/{id}/attempts`, `POST /trainer/attempts/{id}/feedback` | 🟢 Complete & Verified |
| **Trainer Profile** | `Profile` | `GET /users/me` | 🟢 Complete & Verified |

### Role 3: Administrator (Workforce Intelligence)
Target Folder: `frontend/client/src/pages/admin/`

| Page | Nav ID | Source Data / Backend Integration | Status |
|---|---|---|---|
| **Admin Dashboard** | `Dashboard` | Aggregated metrics: workforce count, average capability, critical gaps, learning participation | 🔴 Missing component |
| **Workforce Overview** | `Workforce Overview` | `GET /trainer/learners` + `GET /roles` + department distribution | 🔴 Missing component |
| **Competency Analytics** | `Competency Analytics` | `GET /competencies` + domain coverage aggregation | 🔴 Missing component |
| **Skill Gap Analytics** | `Skill Gap Analytics` | Department-wide gap distribution & priority breakdown | 🔴 Missing component |
| **Training Effectiveness** | `Training Effectiveness` | Learning completion rate vs assessment performance | 🔴 Missing component |
| **Emerging Skills** | `Emerging Skills` | High-demand competencies & emerging digital governance skills | 🔴 Missing component |
| **Capacity Planning** | `Capacity Planning` | Current workforce skill deficit & capacity building demand | 🔴 Missing component |
| **Users / Workforce** | `Users` | User directory with designations, roles, and status | 🔴 Missing component |
| **Reports** | `Reports` | Exportable workforce readiness summary | 🔴 Missing component |
| **Admin Profile** | `Profile` | `GET /users/me` | 🔴 Missing component |

---

## 6. API Endpoint Coverage & Alignment

| Backend Router | Backend Method & Path | Frontend API Client Method (`src/lib/api.ts`) | UI Page Connected |
|---|---|---|---|
| `auth_router` | `POST /api/v1/auth/login` | `api.auth.login` | `LoginPage.tsx` |
| `auth_router` | `POST /api/v1/auth/register` | `api.auth.register` | `LoginPage.tsx` |
| `auth_router` | `GET /api/v1/auth/me` | `api.auth.me` | `AuthContext.tsx`, `App.tsx` |
| `roles_router` | `GET /api/v1/roles` | `api.roles.list` | `LoginPage.tsx`, `AdminUsers.tsx` |
| `roles_router` | `GET /api/v1/roles/{id}/requirements` | `api.roles.getRequirements` | `OfficialDashboard.tsx` |
| `competencies_router` | `GET /api/v1/competencies` | `api.competencies.list` | `MyCompetencies.tsx`, `AdminCompetencies.tsx` |
| `skill_gaps_router` | `GET /api/v1/skill-gaps/me` | `api.skillGaps.me` | `OfficialDashboard.tsx`, `SkillGaps.tsx` |
| `recommendations_router` | `GET /api/v1/recommendations/me` | `api.recommendations.me` | `Recommendations.tsx` |
| `learning_activities_router` | `POST /api/v1/learning-activities` | `api.learningActivities.start` | `Recommendations.tsx`, `MyLearning.tsx` |
| `learning_activities_router` | `GET /api/v1/learning-activities` | `api.learningActivities.list` | `MyLearning.tsx`, `OfficialProgress.tsx` |
| `learning_activities_router` | `PUT /api/v1/learning-activities/{id}` | `api.learningActivities.update` | `MyLearning.tsx` |
| `learning_activities_router` | `POST /api/v1/learning-activities/{id}/complete` | `api.learningActivities.complete` | `MyLearning.tsx` |
| `assessments_router` | `POST /api/v1/assessments` | `api.assessments.start` | `OfficialAssessments.tsx` |
| `assessments_router` | `POST /api/v1/assessments/{id}/submit` | `api.assessments.submit` | `OfficialAssessments.tsx` |
| `capability_assessments_router` | `POST /api/v1/assessments/capability` | `api.capabilityAssessments.create` | `OfficialAssessments.tsx` |
| `capability_assessments_router` | `POST /api/v1/assessments/capability/{id}/submit` | `api.capabilityAssessments.submit` | `OfficialAssessments.tsx` |
| `quizzes_router` | `GET /api/v1/quizzes/assigned` | `api.quizzes.assigned` | `OfficialQuizzes.tsx` |
| `quizzes_router` | `GET /api/v1/quizzes/{id}` | `api.quizzes.get` | `OfficialQuizzes.tsx` |
| `quizzes_router` | `POST /api/v1/quizzes/{id}/submit` | `api.quizzes.submit` | `OfficialQuizzes.tsx` |
| `trainer_router` | `GET /api/v1/trainer/dashboard` | `api.trainer.dashboard` | `TrainerDashboard.tsx` |
| `trainer_router` | `GET /api/v1/trainer/materials` | `api.trainer.materials.list` | `TrainerMaterials.tsx` |
| `trainer_router` | `POST /api/v1/trainer/materials/{id}/generate` | `api.trainer.materials.generateQuestions` | `TrainerQuestionGenerator.tsx` |
| `trainer_router` | `GET /api/v1/trainer/materials/{id}/questions` | `api.trainer.materials.getQuestions` | `TrainerQuestionReview.tsx` |
| `trainer_router` | `PUT /api/v1/trainer/questions/{id}` | `api.trainer.questions.update` | `TrainerQuestionReview.tsx` |
| `trainer_router` | `POST /api/v1/trainer/questions/{id}/approve` | `api.trainer.questions.approve` | `TrainerQuestionReview.tsx` |
| `trainer_router` | `POST /api/v1/trainer/questions/{id}/reject` | `api.trainer.questions.reject` | `TrainerQuestionReview.tsx` |
| `trainer_router` | `POST /api/v1/trainer/quizzes` | `api.trainer.quizzes.create` | `TrainerQuizStudio.tsx` |
| `trainer_router` | `GET /api/v1/trainer/quizzes` | `api.trainer.quizzes.list` | `TrainerQuizStudio.tsx` |
| `trainer_router` | `POST /api/v1/trainer/quizzes/{id}/publish` | `api.trainer.quizzes.publish` | `TrainerQuizStudio.tsx` |
| `trainer_router` | `POST /api/v1/trainer/quizzes/{id}/assign` | `api.trainer.quizzes.assign` | `TrainerQuizStudio.tsx` |
| `trainer_router` | `GET /api/v1/trainer/quizzes/{id}/attempts` | `api.trainer.quizzes.getAttempts` | `TrainerLearnerResults.tsx` |
| `trainer_router` | `POST /api/v1/trainer/attempts/{id}/feedback` | `api.trainer.attempts.submitFeedback` | `TrainerLearnerResults.tsx` |
| `trainer_router` | `GET /api/v1/trainer/learners` | `api.trainer.learners.list` | `TrainerQuizStudio.tsx`, `AdminUsers.tsx` |
| `users_router` | `PUT /api/v1/users/me` | `api.auth.updateProfile` | `ProfilePage.tsx` |

---

## 7. Implementation Roadmap & Priority Sequence

To deliver the complete 3-role experience without regressions, execution will follow this structured plan:

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: CLEANUP & CLIENT HARMONIZATION                    │
│ - Align api.ts endpoints with backend routes                │
│ - Fix capability assessment paths and activity methods      │
│ - Deprecate duplicate src/services/api.ts and Home.tsx      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: MODULAR OFFICIAL EXPERIENCE                        │
│ - Build src/pages/official/ components (Dashboard,          │
│   Competencies, Skill Gaps, Recommendations, My Learning,   │
│   Quizzes, Evidence Timeline, Progress, Profile)            │
│ - Enforce "Learning ≠ Competency" in UI feedback            │
│ - Integrate with OfficialLayout and App.tsx                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: ORGANIZATIONAL ADMIN INTELLIGENCE                  │
│ - Build src/pages/admin/ components (Dashboard, Workforce,  │
│   Competencies, Skill Gaps, Training Effectiveness,         │
│   Emerging Skills, Capacity Planning, Users, Reports)       │
│ - Integrate with AdminLayout and App.tsx                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: VERIFICATION, BUILD & COMPLETION REPORT            │
│ - Run npm run build & backend pytest test suite             │
│ - Validate cross-role RBAC & security                       │
│ - Generate FINAL_FRONTEND_PRODUCT_COMPLETION_REPORT.md      │
└─────────────────────────────────────────────────────────────┘
```
