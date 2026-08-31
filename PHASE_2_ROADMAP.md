# ShikshaSetu Phase 2 — Feature Roadmap

**Foundation:** Phase 1 core loop is COMPLETE & E2E VERIFIED  
**Timeline:** After Product Vision Audit approved  
**Scope:** Build features needed for institutional rollout, deprioritize nice-to-have

---

## Phase 2 MUST-BUILD (Critical for Production)

### P2.1 — Admin Dashboard & User Management

**Why:** Without admin tools, the system is employees-only. Impossible to manage users, assign roles, view institutional metrics.

**Scope:**
- Admin endpoints:
  - GET /admin/users (with department, role, status filters)
  - PATCH /admin/users/{id} (update role, designation, status)
  - POST /admin/users/bulk-import (CSV import)
  - DELETE /admin/users/{id} (deactivate, keep audit trail)

- Admin UI:
  - User management page (list, edit, bulk actions)
  - Department view (users per department)
  - Role assignment interface
  - Audit log viewer

**Estimated Effort:** 2 weeks (backend + frontend)

**Dependencies:** None (builds on existing auth + role system)

**Success Criteria:**
- Admin can list/filter users by department/role
- Admin can change a user's role and re-run competency assessment
- Bulk import works (50+ users from CSV)
- All changes audit-logged

---

### P2.2 — Analytics & Reporting Dashboard

**Why:** Institutional decision-makers need to see competency trends, learning adoption, gap distribution.

**Scope:**
- Analytics endpoints:
  - GET /analytics/competency-trends (avg level over time, per competency)
  - GET /analytics/learning-adoption (% users completed resources, by type)
  - GET /analytics/gap-distribution (gap sizes across org, by domain)
  - GET /analytics/assessment-performance (% passing, by competency)
  - GET /analytics/department-summary (dept-level metrics)

- Frontend Dashboards:
  - Institutional Analytics (trends, adoption, gaps)
  - Department Superintendent View (department-level summary)
  - Employee Progress View (individual learning trends)

**Estimated Effort:** 3 weeks (backend queries + frontend dashboards)

**Dependencies:** Analytics endpoints, time-series data aggregation

**Success Criteria:**
- Dashboard shows real data (not mock)
- Trend lines show competency improvement over time
- Can filter by department, role, date range
- Superintendent sees department-level aggregates only

---

### P2.3 — Learning Pathway Orchestration

**Why:** Single-step recommendations work for simple gaps. Complex gaps need multi-step sequences (e.g., Python gap requires Prerequisites → Basics → Intermediate → Advanced).

**Scope:**
- Data Model:
  - learning_pathways collection (sequence of resources tied to competency goal)
  - pathway_steps (ordered steps with prerequisites, difficulty)

- Recommendation Algorithm:
  - Detect prerequisite chains (e.g., Python → Data Viz → Statistics)
  - Auto-generate sequence (Beginner → Intermediate → Advanced)
  - Adaptive routing (user underperforms → repeat → move to next)

- UI:
  - Pathway view (multi-step learning sequence)
  - Progress visualization (step 1/5 complete)
  - Save pathway for later

**Estimated Effort:** 4 weeks (complex algorithm, testing, UI)

**Dependencies:** Prerequisite metadata, learning_resource updates

**Success Criteria:**
- System recommends 3-5 step pathway for complex gaps
- User follows pathway step-by-step
- Competency updates correctly after each step
- Pathways are persisted and resumable

---

### P2.4 — Live iGOT/NSSTA Integration

**Why:** Currently using seeded data. Live integration brings real, up-to-date courses and training programmes.

**Scope:**
- Backend:
  - iGOT Provider: Real API integration (if live access available)
    - GET courses by competency
    - Track enrollment + completion status
    - Fetch live metadata updates
  
  - NSSTA Provider: Real API integration (if live access available)
    - GET training programmes
    - Check batch availability
    - Track registrations

- Fallback: If live APIs unavailable, use cached/prototype adapter (honest about limitations)

- Migration:
  - Keep seeded data as fallback
  - Add provider toggle (use live first, fallback to prototype)
  - No breaking changes to recommendation engine

**Estimated Effort:** 4-6 weeks (depends on API availability and documentation)

**Dependencies:** Official API credentials/documentation from iGOT + NSSTA

**Success Criteria:**
- Recommendations pull real iGOT/NSSTA resources
- Enrollment links work (users can enroll in external platforms)
- Metadata is current (courses not removed from index)
- Graceful fallback if API unavailable

---

### P2.5 — AI Document Processing & Question Generation

**Why:** Static question bank is limited. AI processing enables organizations to upload their own content and auto-generate questions.

**Scope:**
- Backend:
  - Document upload endpoint (PDF, PPTX, DOCX)
  - Text extraction pipeline (PyMuPDF, python-pptx, python-docx)
  - Chunking & semantic indexing (Chroma/FAISS)
  - LLM-based question generation (MCQ, scenario, fill-in-blank)
  - Validation (check for well-formed questions, grounding in content)
  - Question bank extension (new questions added to question bank)

- Frontend:
  - Document upload UI
  - Question preview & editing
  - Publish to question bank

**Estimated Effort:** 5-7 weeks (RAG pipeline, LLM integration, validation)

**Dependencies:** LLM API access (OpenAI, Anthropic, or open-source), vector DB

**Success Criteria:**
- Upload a PDF → extract text → generate 10 questions
- Questions are grounded in content (source chunks cited)
- Validation catches malformed questions
- Generated questions work in assessments (improve competency calculation)

---

## Phase 2 SHOULD-BUILD (Important for Institutional Adoption)

### P2.6 — Role Hierarchy & Transition Workflows

**Why:** Employees progress to higher roles (e.g., Officer → Senior Officer → Manager). System should guide competency development for role transition.

**Scope:**
- Data Model:
  - Role hierarchy (parent_role_id for role relationships)
  - Transition pathways (role_transitions collection)
  
- Features:
  - Detect when user is ready for role transition (majority of current role requirements met)
  - Recommend transition learning path (close remaining gaps + new role requirements)
  - Support multi-role users (e.g., Technical Officer + Team Lead)

**Estimated Effort:** 2-3 weeks

**Dependencies:** None (builds on existing role system)

**Success Criteria:**
- System recommends transition to Senior Officer when ready
- Transition pathway includes learning for new role requirements
- User can hold two roles simultaneously

---

### P2.7 — Assessment Result Explanation & Insights

**Why:** Users see competency updated but don't understand why. System should explain the evidence and next steps.

**Scope:**
- Assessment result page should show:
  - Which evidence types contributed to score (breakdown)
  - Why confidence level is what it is
  - How this compares to previous assessment
  - Recommended next action (take more assessments, learn resource, etc.)

**Estimated Effort:** 1-2 weeks (data already collected)

**Dependencies:** None

**Success Criteria:**
- User sees "Competency increased 2.5 → 3.1 because knowledge test +0.6"
- Confidence is explained ("80% confident based on 2 assessments")
- Recommendation: "Take one more assessment or complete recommended learning"

---

### P2.8 — Accessibility & Offline Support

**Why:** Production systems need WCAG compliance and offline resilience.

**Scope:**
- Accessibility:
  - ARIA labels on all interactive elements
  - Keyboard navigation (tab through all UI)
  - Screen reader testing (with NVDA/JAWS)
  - Color contrast audit (WCAG AA minimum)
  - Form validation accessible

- Offline:
  - Service worker (cache app shell)
  - Offline indicator
  - Queue actions taken offline
  - Sync when connection restored

**Estimated Effort:** 3-4 weeks (accessibility testing is manual + time-consuming)

**Dependencies:** Accessibility testing tools, screen reader access

**Success Criteria:**
- WCAG 2.1 AA compliance (or audit report of what's not)
- App works offline (view cached data, queue assessments)
- All actions sync when back online

---

## Phase 2 NICE-TO-HAVE (Defer unless explicitly requested)

- **Learning Preference Collection:** Ask users (video/text/interactive), adapt recommendations
- **Spaced Repetition Scheduling:** Recommend refresher assessments based on Ebbinghaus curve
- **Competency Degradation:** Competency slowly decreases if not exercised (requires time tracking)
- **Learner Feedback:** User ratings of resources ("Helpful/Not Helpful", comments)
- **Peer Comparison:** Anonymized benchmarking ("You're in top 20% for this competency")
- **Mobile App:** Native iOS/Android app (build after web is solid)
- **Predictive Analytics:** ML models to predict which employees will struggle
- **Chatbot Learner Assistant:** AI-powered Q&A about learning materials
- **Institutional Competency Roadmap:** 5-year strategic competency planning
- **Data Export & Compliance:** GDPR right-to-access, data deletion tools

---

## Implementation Priority (Recommended Order)

### Phase 2A (Weeks 1-6) — Admin & Analytics
1. **P2.1 Admin User Management** — Without this, can't scale beyond single user
2. **P2.2 Analytics Dashboard** — Demonstrates institutional value

### Phase 2B (Weeks 7-12) — Content & Engagement
3. **P2.4 Live iGOT/NSSTA** — Brings real content (may require waiting for API access)
4. **P2.5 AI Document Upload** — Unlocks content creation for organizations

### Phase 2C (Weeks 13-18) — Sophistication & Compliance
5. **P2.3 Learning Pathways** — Handles complex gaps (most complex feature)
6. **P2.6 Role Transition** — Supports career development
7. **P2.7 Assessment Explanations** — Improves transparency
8. **P2.8 Accessibility & Offline** — Production readiness

---

## Success Metrics (End of Phase 2)

- [ ] Admin can onboard 100+ users in < 1 hour
- [ ] Dashboard shows real institutional metrics (competency trends, gap distribution)
- [ ] Learning pathways successfully guide users through complex gaps (3+ step sequences)
- [ ] Real iGOT/NSSTA resources available in recommendations
- [ ] Organizations can upload custom content and auto-generate questions
- [ ] Accessibility audit shows WCAG AA compliance (or clear roadmap to compliance)
- [ ] System works offline with sync on reconnect
- [ ] 200+ tests (backend + frontend), zero TypeScript errors, production build succeeds

---

## Key Decision: Live API Access

**Before starting P2.4, clarify:**
- Do we have official API credentials for iGOT? (Required for live sync)
- Do we have official API credentials for NSSTA/TPAC? (Required for training programme data)
- If not, when will they be available?

**Interim Plan:** Keep using seeded/prototype data marked clearly as "prototype." This is honest and maintains integrity. Switch to live data once credentials available.

---

## Resource Estimate

- **Phase 2 Full Scope (all MUST + SHOULD):** 18-24 weeks (2-3 person-months)
- **Phase 2A (Admin + Analytics only):** 4-6 weeks (1-2 person-months, unblocks institutional rollout)
- **Phase 2 MVP (Admin + Analytics + AI Document):** 8-10 weeks (1-2 person-months, enables content authoring)

---

## Before Starting Phase 2

1. ✅ **Product Vision Audit approved** (this document)
2. 📋 **Prioritization by stakeholders** (which Phase 2 features matter most?)
3. 🔑 **API access clarified** (iGOT/NSSTA credentials, timeline)
4. 👥 **Team capacity confirmed** (who works on what?)
5. 📅 **Timeline communicated** (when are Phase 2 features needed?)

**DO NOT start Phase 2 feature coding until these items are confirmed.**

---

## How to Use This Roadmap

- **For the Hackathon Round 1 Submission:** Mention Phase 1 complete, outline Phase 2 (don't build it yet)
- **For Institutional Pilots:** Prioritize P2.1 + P2.2 first (admin + visibility)
- **For Content Authoring:** Prioritize P2.5 (AI document processing)
- **For Complex Organizations:** Prioritize P2.3 (learning pathways)

The core loop works. Phase 2 is about making it practical for real institutions.
