# Phase 3I — ShikshaSetu Typography System & Full UI Font Redesign Audit

**Date**: 2026-09-04  
**Status**: Comprehensive Read-Only Audit Complete  
**Target Fonts**:  
- **Primary**: `Plus Jakarta Sans` (Weights: 400, 500, 600, 700, 800)  
- **Secondary Technical**: `JetBrains Mono` (Weights: 400, 500, 600)  

---

## 1. Current Font Architecture
- The frontend is built on **Vite v7 + React 18 + TailwindCSS v4** (`@tailwindcss/vite` with `@theme inline` block in `src/index.css`).
- Root font variables are declared inside `index.css`:
  - `--font-sans: "Manrope", sans-serif;`
  - `--font-display: "Source Serif 4", serif;`
- Global body font rule in `index.css:30`:
  `body { margin: 0; background: #f4f7fb; color: #18304f; font-family: "Manrope", sans-serif; -webkit-font-smoothing: antialiased; }`
- No local `@font-face` files are currently bundled; font assets are fetched over CDN.

---

## 2. Current Font Families & Weights
- **Current Families in Use**:
  - `Manrope` (400, 500, 600, 700, 800)
  - `Source Serif 4` (600, 700 — rarely referenced in actual components)
  - Browser fallback generic `monospace` / `font-mono` (used in scattered `<code>` blocks)
- **Deficiencies of Current System**:
  - Over-reliance on `font-black` (weight 900) across titles and table headers, which causes excessive visual heaviness rather than clean geometric hierarchy.
  - Lack of a standardized `font-mono` configuration (using default browser courier/consolas fallback without dedicated weights).
  - Mixed weight patterns for labels (`font-extrabold` vs `font-bold` vs `font-semibold` on identical uppercase caption badges).

---

## 3. Current Font Imports
- `c:\Users\Lenovo\Desktop\ShikshaSetu\frontend\client\src\index.css:2`:
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap');
  ```
- `c:\Users\Lenovo\Desktop\ShikshaSetu\frontend\client\index.html`:
  Contains standard `<meta>` and `<title>` tags with no `<link rel="preconnect">` or duplicate font links.

---

## 4. Hardcoded Font Overrides & Inline Styles
- Checked all files in `src/`:
  - No hardcoded `style={{ fontFamily: '...' }}` declarations in any components.
  - Tailwind utility classes (`font-sans`, `font-mono`, `font-bold`, `font-extrabold`, `font-black`, `font-semibold`, `font-medium`, `font-normal`) are universally used.
  - Monospace classes currently use generic `font-mono`.

---

## 5. Typography Inconsistencies & Hierarchy Issues

| Component Area | Current Pattern | Issue | Target Phase 3I Pattern |
|---|---|---|---|
| **Page Titles** | `font-black text-2xl sm:text-3xl` | Weight 900 is too dense for civic/govtech UI | `text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]` (Plus Jakarta Sans 700) |
| **KPI Values** | `font-black text-3xl` | Good sizing, but lacks tabular alignment on rapid count-ups | `text-2xl sm:text-3xl font-bold tracking-tight text-[#123057]` (Plus Jakarta Sans 700/800) |
| **KPI Subtitles** | `text-[10px] font-extrabold uppercase` | Too bold for secondary metadata | `text-[11px] font-semibold text-slate-500 uppercase tracking-wider` (Plus Jakarta Sans 600) |
| **Competency Codes** | `text-[10px] font-bold text-slate-400 uppercase` | Rendered in sans-serif | `font-mono text-[11px] font-medium tracking-tight text-slate-500` (JetBrains Mono 500) |
| **Status / Role Badges** | `font-extrabold text-[10px]` | Heavy letterforms in small containers | `font-semibold text-[11px] tracking-wide` (Plus Jakarta Sans 600) |
| **Navigation Items** | `font-bold text-xs` (sidebar) | Equal weight between active and inactive states | Inactive: `font-medium text-xs`; Active: `font-semibold text-xs` |
| **Table Headers** | `text-[10px] font-extrabold uppercase` | Too aggressive | `text-[11px] font-semibold uppercase tracking-wider text-slate-500` |
| **Code / Citations** | `font-mono text-[10px] font-semibold` | Uses unconfigured monospace fallback | `font-mono text-[11px] font-medium text-pink-700` (JetBrains Mono 500) |
| **Login Brand** | `font-black text-2xl` | Heavy visual anchor | `font-extrabold text-2xl tracking-tight text-[#123057]` (Plus Jakarta Sans 800) |

---

## 6. Pages and Components Requiring Updates

### Layout & Navigation:
1. `OfficialLayout.tsx`: Sidebar items, pathway indicator text, profile section, language toggle.
2. `TrainerLayout.tsx`: Trainer sidebar tabs, header branding, role badge.
3. `AdminLayout.tsx`: Administrative navigation tabs, console status label.

### Official Workspace Views:
4. `OfficialDashboard.tsx`: Hero greeting, 4 KPI cards (`NumberReveal`), readiness meter, urgent gap cards.
5. `OfficialCompetencies.tsx`: Competency matrix cards, category tabs, code tags (`font-mono`), level definitions.
6. `OfficialAssessments.tsx`: Adaptive session header, scenario text, question headings, option choices, feedback pills.
7. `OfficialSkillGaps.tsx`: Deficit numbers, comparative signal bars, priority badges.
8. `OfficialRecommendations.tsx`: Learning card titles, provider tags, competency chips (`font-mono`).
9. `OfficialLearning.tsx`: Milestone cards, module durations, completion indicators.
10. `OfficialQuizzes.tsx`: Quiz card titles, question prompts, radio labels, accuracy results.
11. `OfficialEvidence.tsx`: Evidence ledger table, confidence scores (0.30 vs 0.85), record timestamps.
12. `OfficialProgress.tsx`: Growth milestone timelines, competency trajectory labels.
13. `OfficialProfile.tsx`: User attributes, designation badges, role taxonomy metadata.
14. `CapabilityAssistant.tsx` & `MarkdownRenderer.tsx`: Chat bubbles, suggestions chips, markdown H1-H4, code blocks (`font-mono`).

### Trainer Workspace Views:
15. `TrainerDashboard.tsx`: Trainer KPI counters, pending review queue, material quick-launch.
16. `TrainerMaterials.tsx`: Material library cards, chunk statistics, upload modal dropzone text.
17. `TrainerQuestionGenerator.tsx`: RAG pipeline step tracker, difficulty toggles, question count slider.
18. `TrainerQuestionReview.tsx`: Question review cards, source chunks badge, edit modal inputs.
19. `TrainerQuizStudio.tsx`: Quiz studio cards, assign modal form labels, draft/publish status pills.
20. `TrainerLearnerResults.tsx`: Learner assessment table, evaluation modal, score breakdown.

### Admin Workspace Views:
21. `AdminDashboard.tsx`: Governance KPI counters, domain capability matrix, department workforce distribution.
22. `WorkforceOverview.tsx`: Personnel registry table, department/role filter dropdowns.
23. `CompetencyAnalytics.tsx`: 42-element taxonomy table, deficit values, domain breakdown cards.
24. `SkillGapAnalytics.tsx`: High-priority gap counters, affected officials metrics.
25. `TrainingEffectiveness.tsx`: Supporting vs Authoritative evidence ledger cards, completion meters.
26. `EmergingSkills.tsx`: Emerging competency index, demand velocity, strategic interventions.
27. `CapacityPlanning.tsx`: Cohort intervention sizes, program timeline cards.
28. `AdminUsers.tsx`: User directory table, access role badges, registration dates.
29. `AdminReports.tsx`: Export report cards, file metadata, confirmation badges.
30. `AdminProfile.tsx`: Admin security credentials, system metadata.

### Shared / Global Components:
31. `LoginPage.tsx`: Platform branding, sign-in form labels, inputs, credentials hint box.
32. `MotionUtils.tsx`: `NumberReveal`, `ProgressBarFill`, `StatusTransition`, `ThinkingIndicator`.
33. `index.html` & `index.css`: Central font declarations and typography scale utilities.

---

## 7. Responsive Typography Risks
- **Long Competency Names**: E.g., *"Statistical Data Quality Frameworks & Governance"* in mobile card headers. Must use `line-clamp-2` or fluid sizing `text-sm sm:text-base` to prevent card overflow.
- **KPI Value Wraps**: `3.8 / 5.0` or `1,250 hrs` in grid columns. Using `font-bold text-2xl sm:text-3xl tracking-tight` with `whitespace-nowrap` prevents awkward line breaks.
- **Table Data Density**: Dense tables (e.g. `CompetencyAnalytics.tsx` with 7 columns) on mobile. Header uppercase tokens should be `text-[10px] sm:text-[11px]` and cells `text-xs` to preserve cell padding.

---

## 8. Third-Party & Shared Component Typography
- **Sonner Toasts**: Inherits `--font-sans` directly from `body`.
- **Lucide Icons**: Scaled with explicit pixel bounds (12px to 24px) paired with text labels.
- **ReactMarkdown / RemarkGFM**: Stylized in `MarkdownRenderer.tsx`; updated to enforce `Plus Jakarta Sans` for prose and `JetBrains Mono` for code/citations.

---

## 9. Chart & Table Typography
- Tables use standard semantic markup (`<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`).
- Header font weight adjusted to `font-semibold text-slate-500` with subtle tracking.
- Row keys in `JetBrains Mono` (`font-mono text-[11px]`) for `competency_code`, `employee_id`, and `evidence_id`.

---

## 10. Recommended Migration Plan

1. **Step 1: Central Font Loading & Token Configuration**
   - In `frontend/client/index.html`: Add preconnect links to `fonts.googleapis.com` and `fonts.gstatic.com`.
   - In `frontend/client/src/index.css`:
     - Load `Plus Jakarta Sans` (weights: 400, 500, 600, 700, 800) and `JetBrains Mono` (weights: 400, 500, 600).
     - Set `@theme inline` variables:
       - `--font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`
       - `--font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;`
     - Set `body` font family to `var(--font-sans)`.
     - Define typography scale utility classes (`.font-display`, `.font-page-title`, `.font-section-heading`, `.font-card-title`, `.font-kpi`, `.font-code`, `.font-label`).

2. **Step 2: Update Shared Layouts & Navigation**
   - Standardize sidebar font weights: Inactive = `font-medium text-xs`, Active = `font-semibold text-xs text-brand`.

3. **Step 3: Update Official, Trainer, and Admin Workspaces**
   - Apply structured hierarchy across dashboards, cards, tables, forms, and assessment studios.
   - Use `font-mono` on all competency codes (`STAT_SAMPLING`, `EDU_PEDAGOGY`), employee IDs, and evidence hashes.

4. **Step 4: Update Markdown Renderer & AI Co-Pilot**
   - Ensure `MarkdownRenderer.tsx` uses `Plus Jakarta Sans` for prose, bold titles, and `JetBrains Mono` for `<code>` blocks and citation tags.

5. **Step 5: Verification & Quality Assurance**
   - Run `npm run check` (`tsc --noEmit`).
   - Run `npm run build` (production Vite bundle verification).
   - Generate `PHASE_3I_TYPOGRAPHY_REPORT.md`.
