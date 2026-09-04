# ShikshaSetu — Global UI Animation & Micro-Interaction Audit Report
**Phase A — Frontend Architectural & Animation Surface Audit**  
**Date:** September 2026  
**Target Application:** ShikshaSetu (Empowering Civil Services & Public Education)

---

## 1. Executive Summary

This audit establishes the baseline frontend architecture of **ShikshaSetu** to design a unified, enterprise-grade, lightweight, GPU-friendly animation system. The goal is to elevate the platform to a polished government capability intelligence portal without introducing rendering bottlenecks, blocking API threads, or altering any business logic or data contracts.

---

## 2. Tech Stack & Styling Architecture

| Layer | Technology | Key Details |
| :--- | :--- | :--- |
| **Framework** | React 19 + TypeScript + Vite 7 | Fast modular bundler, ESM format |
| **CSS Engine** | Tailwind CSS v4 + `tw-animate-css` | Uses `@import "tailwindcss";` and `@theme inline` tokens |
| **Core Fonts** | *Manrope* (Sans), *Source Serif 4* (Display) | Professional civic typography |
| **State & Navigation** | Role-based router in `App.tsx` | Lazy-loaded Suspense views for Official, Trainer, and Admin |
| **Component Library** | Radix UI primitives + Lucide Icons + Sonner | Accessible primitives with custom styling in `components/ui/` |
| **Motion Philosophy** | Pure CSS transforms (`translateY`, `opacity`, `scale`) | Non-blocking, zero JavaScript layout-thrashing, GPU-accelerated |

---

## 3. Inventory of Pages & Layouts

### A. Official / Learner Workspace (10 Pages)
* **Layout:** `src/layouts/OfficialLayout.tsx` — Fixed sidebar with capability pathway strip (`Role → Assess → Gap → Learn → Practice → Validate`), top navigation bar with language toggle and user status.
* **Pages:**
  1. `OfficialDashboard.tsx` — Welcome hero banner, 4 key capability KPI cards, Priority Skill Gaps list, Next Best Action recommendation card, recent learning activities.
  2. `OfficialCompetencies.tsx` — Civil service competency framework matrix, domain filters, status indicators (Strong / Developing / Needs Attention), proficiency levels.
  3. `OfficialAssessments.tsx` — Dynamic IRT adaptive assessment engine, question cards, option selection, step progression, real-time theta estimation feedback, authoritative validation modal.
  4. `OfficialSkillGaps.tsx` — Role capability framework gap analysis, critical/high/medium severity indicators, required vs current proficiency bars, start assessment CTA.
  5. `OfficialRecommendations.tsx` — AI-recommended iGOT/MoSPI learning feed, match scores, competency alignment tags, provider filters.
  6. `OfficialLearning.tsx` — Active and completed curriculum modules, interactive course reader modal, module progress updating, completion evidence triggering.
  7. `OfficialQuizzes.tsx` — Trainer-assigned practice quizzes, question answer selection, instant scoring breakdown, supporting evidence recording.
  8. `OfficialEvidence.tsx` — Immutable competency evidence ledger, authoritative vs supporting distinction, confidence indicators (0.85 vs 0.30), certificate verification.
  9. `OfficialProgress.tsx` — Longitudinal capability progression metrics, learning hours, authoritative IRT assessment history timeline, verified competency evolution.
  10. `OfficialProfile.tsx` — Civil servant employee profile, designation, department mapping, credentials.

### B. Trainer Workspace (6 Pages)
* **Layout:** `src/layouts/TrainerLayout.tsx` — Operations sidebar with curriculum status and quick actions.
* **Pages:**
  1. `TrainerDashboard.tsx` — AI Assessment Studio dashboard, curriculum metrics, question review stats, published quiz counts.
  2. `TrainerMaterials.tsx` — Document upload portal, PDF processing pipeline, curriculum parsing status.
  3. `TrainerQuestionGenerator.tsx` — AI-grounded MCQ generator, difficulty and Bloom's taxonomy parameters.
  4. `TrainerQuestionReview.tsx` — Question audit queue, approval/rejection modal, inline option editing.
  5. `TrainerQuizStudio.tsx` — Authoritative quiz builder, question selection, learner assignment.
  6. `TrainerLearnerResults.tsx` — Learner attempt reviews, qualitative feedback submission, score analytics.

### C. Admin Workspace (10 Pages)
* **Layout:** `src/layouts/AdminLayout.tsx` — Governance sidebar, department switcher.
* **Pages:**
  1. `AdminDashboard.tsx` — National workforce capability dashboard, department breakdown, iGOT catalog gateway status.
  2. `WorkforceOverview.tsx` — Civil servant directory, competency distribution.
  3. `CompetencyAnalytics.tsx` — Domain matrix, average proficiency levels across ministries.
  4. `SkillGapAnalytics.tsx` — Systemic bottleneck detection, critical gap heatmaps.
  5. `TrainingEffectiveness.tsx` — Pre vs post assessment capability lift metrics.
  6. `EmergingSkills.tsx` — Future skill forecasting and public service trends.
  7. `CapacityPlanning.tsx` — Departmental readiness projections.
  8. `AdminUsers.tsx` — User directory and RBAC access roles.
  9. `AdminReports.tsx` — Exportable capability compliance reports.
  10. `AdminProfile.tsx` — Admin administrative profile.

### D. Global Overlay Component
* `CapabilityAssistant.tsx` (`Karmayogi AI Co-Pilot`) — Floating assistant with slide-up chat drawer, citation badges (`STAT_SAMPLING`, `BEH_COMMUNICATION`), quick-action suggestion chips, and responsive minimization.

---

## 4. Existing Animation Footprint & Deficiencies

1. **Ad-hoc `animate-fadeIn` and `animate-pulse`**: Many pages use inline `animate-fadeIn` from `tw-animate-css`, which triggers once on mount but lacks coordinated stagger, clean micro-interactions, or unified timing.
2. **Missing Stagger & Progressive Reveal**: KPI cards and list items appear all at once or have hardcoded `nth-child` rules only in `index.css` for specific classes (`.metric-card`, `.gap-row`).
3. **Static Numbers**: KPI scores (e.g. `3.8 / 5.0`, `12.4 hrs`, `4 gaps`) jump instantly upon API resolution without smooth reveal transitions.
4. **Interactive States**: Buttons, option selectors, and modal transitions lack refined tactile feedback (`active:scale(0.98)`).
5. **No Visual Hierarchy in Loading Transitions**: While `PageSkeleton.tsx` exists, transitions from skeleton to rendered data can cause minor visual jumping.

---

## 5. Design System & Unified Animation Vocabulary

To maintain high performance and prevent CSS bloat, all animations will be codified into a single centralized CSS layer in `src/index.css` and reusable React motion helper primitives:

### Unified Timing & Easing
* **Page Transition (`page-enter`):** `200ms cubic-bezier(0.16, 1, 0.3, 1)` — `opacity: 0 → 1`, `translateY: 8px → 0`
* **Card Entrance (`card-enter`):** `240ms cubic-bezier(0.16, 1, 0.3, 1)` — `opacity: 0 → 1`, `translateY: 6px → 0`
* **Stagger Delays (`stagger-1` through `stagger-6`):** `30ms` intervals (`30ms, 60ms, 90ms, 120ms, 150ms, 180ms`)
* **Micro-interactions (`btn-press`, `card-hover`):** `150ms ease-out` — `transform: scale(0.98)` on active, subtle shadow change
* **Progress Reveal (`progress-bar-fill`):** `600ms cubic-bezier(0.25, 1, 0.5, 1)`
* **Status Badge Reveal (`badge-pop`):** `180ms cubic-bezier(0.34, 1.56, 0.64, 1)` — `scale(0.95) → scale(1)`
* **Reduced Motion Guarantee:** Mandatory fallback via `@media (prefers-reduced-motion: reduce)` setting all animation and transition durations to `0.01ms`.

---

## 6. Audit Verification on Role/Course Experience (Rule 20)

* **Inspection:** We audited `OfficialLearning.tsx` and `useLearningActivities.ts`.
* **Findings:** `useLearningActivities` fetches user-specific learning activities via `api.learningActivities.list()`. The backend associates activities with the logged-in user's profile and mapped competencies. In `OfficialRecommendations.tsx`, courses are filtered by user competency codes.
* **Safeguard:** No backend filtering logic or API contracts will be modified. Pure presentation enhancements will distinguish between user-enrolled role modules and catalog items.

---

## 7. Next Steps & Phasing Plan

* **Phase B:** Create global animation system tokens, utility classes, and helper hooks/components (`NumberReveal`, `ProgressFill`, `StaggerContainer`).
* **Phase C:** Implement on Official Pages (Dashboard, Competencies, Assessments, Skill Gaps, Recommendations, Learning, Quizzes, Evidence, Progress, Profile, AI Co-Pilot).
* **Phase D:** Implement on Trainer Pages (Dashboard, Materials, Question Generator, Review, Studio, Results).
* **Phase E:** Implement on Admin Pages (Dashboard, Workforce, Competency Analytics, Analytics views, Users, Reports).
* **Phase F & G:** Performance verification (`npm run check`, `npm run build`), zero layout shift verification, responsive visual QA across desktop and mobile viewports.
