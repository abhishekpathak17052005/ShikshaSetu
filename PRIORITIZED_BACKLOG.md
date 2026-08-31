# ShikshaSetu — Prioritized Development Backlog

**Purpose:** Convert Product Vision Audit findings into actionable MUST/SHOULD/LATER work, grounded in the original SIH 26101 objective.

**Decision Framework:** Every backlog item must answer: **"Which requirement or user problem from the original ShikshaSetu vision does this solve?"**

If it doesn't answer that question, it doesn't go in MUST or SHOULD. It goes to LATER or is not built.

---

## ARCHITECTURAL PRINCIPLE (Preserved Across All Phases)

```
Learning ≠ Competency

Learning → Supporting Evidence (0.3)
Assessment → Demonstrated Capability (0.8)
Demonstrated Capability → Competency Update
Competency → Skill Gap
Skill Gap → Recommendation
Recommendation → Learning
```

**This is non-negotiable.** Every feature must respect this separation.

---

## CONTEXT: What the Original SIH 26101 Objective Demands

From strict.md Round 1 scope, the core objective is:

```
Employee Profile
  ↓
Competency Assessment
  ↓
Current Competency
  ↓
Required Competency (Role-based)
  ↓
Skill Gap
  ↓
iGOT + NSSTA Recommendations
  ↓
Learning
  ↓
Assessment (Capability)
  ↓
Competency Update
  ↓
Updated Recommendation
  ↓
[Loop repeats]
```

**This loop is now COMPLETE and E2E VERIFIED.**

The question becomes: **What else does the original SIH problem statement expect?**

Without access to the exact SIH 26101 document, we must infer from the strict.md guidance. It emphasizes:

1. **Official statistics context** (MoSPI, iGOT, NSSTA, TPAC)
2. **Public sector employee development**
3. **Competency-driven capability growth**
4. **Evidence-based advancement** (not self-declared)
5. **Institutional adoption** (not just individual learning)

---

## P0: MUST-BUILD (Core Loop Dependencies)

These items are **required to complete the SIH objective as stated**. The core loop depends on them.

### P0.1 — Role & Competency Seeding (Initial Setup)

**What:** Ensure at least 3-5 government/statistical roles are properly defined with competency requirements.

**Why:** Currently only "Statistical Officer" is seeded. SIH demo may showcase multiple roles (Officer, Senior Officer, Manager, Statistician, etc.). Role diversity proves the system scales beyond single role.

**Scope:**
- Define 3-5 statistical roles (not just 1)
- Link each to appropriate required competencies
- Seed via migration/script (not manual)

**Effort:** 1 day

**Success Criteria:**
- GET /roles returns 3+ roles
- Each role has 5-8 required competencies
- Different roles have different requirements (Officer ≠ Manager)
- Frontend can switch roles and see different gaps/recommendations

**SIH Relevance:** 🟢 **CRITICAL** — Judges will ask "Does this scale to multiple roles?" Currently single role.

---

### P0.2 — Question Bank Completeness

**What:** Ensure sufficient diversity in assessment questions across all major competencies.

**Why:** Currently 40 questions across 8 competencies = 5/competency. For robust demo, want 8-10 questions per competency for variety and reliability.

**Scope:**
- Add questions to question bank (target: 80-100 total)
- Ensure all 8 hero competencies well-covered
- Mix difficulty levels (some easy, some hard)

**Effort:** 2-3 days (can be done via seed script)

**Success Criteria:**
- 80+ questions in question bank
- Each major competency has 8+ questions
- Question bank has variety (not all same difficulty)
- E2E test still passes (no regressions)

**SIH Relevance:** 🟡 **IMPORTANT** — Judges will take multiple assessments. More questions = more robust demo.

---

### P0.3 — Learning Resources Diversity

**What:** Ensure learning resource mappings cover all main competency gaps, not just Python.

**Why:** Currently recommendations heavily weighted toward Python. For institutional credibility, need resources mapped to Statistical, Technical, and Governance competencies.

**Scope:**
- Review learning_resource_mappings collection
- Ensure 70%+ of competencies have at least 2-3 mapped resources
- Add mappings if gaps exist (metadata already seeded)

**Effort:** 1-2 days

**Success Criteria:**
- All Statistical competencies have 2+ resource mappings
- All Technical competencies have 2+ resource mappings
- Recommendations for different gaps show different resources
- No "no recommendations available" scenarios

**SIH Relevance:** 🟡 **IMPORTANT** — Credibility. If a judge gaps on Sampling but gets "no resources," looks broken.

---

### P0.4 — Data Consistency Audit & Seed Migration

**What:** Audit all seed data for consistency, fix any orphaned records, ensure clean state.

**Why:** Over months of development, data may have inconsistencies (e.g., role with non-existent competencies, resources with no mappings, etc.).

**Scope:**
- Validate all role_requirements reference real competencies
- Validate all learning_resource_mappings reference real resources
- Remove orphaned records
- Ensure seed script is idempotent (re-run produces same state)

**Effort:** 1-2 days

**Success Criteria:**
- Seed script runs clean (no errors)
- Database audit passes (no orphans)
- E2E test passes (no data issues)

**SIH Relevance:** 🟢 **CRITICAL** — Bad data kills demo. Must be bulletproof.

---

## P1: SHOULD-BUILD (Product Completeness for Institutional Context)

These features are **important for demonstrating institutional viability**. They're not in the core loop, but they're what an institution would ask for.

### P1.1 — Admin Dashboard: User Management

**What:** Basic admin interface to list users, view their status, see their competency profile.

**Why:** SIH judges or pilot users will ask "How do I manage employees in the system?" Currently no admin UI exists.

**Scope:**
- GET /admin/users endpoint (list with filters)
- Admin UI page (user list, view user detail)
- Show user's role, competencies, gaps, recommendations

**Effort:** 2-3 weeks

**Success Criteria:**
- Admin can list 50+ users
- Can filter by department, role, status
- Can view any user's competency profile
- Can see aggregated gaps per user

**SIH Relevance:** 🟡 **IMPORTANT** — Proves institutional scalability. Round 1 demo might not need it, but pilot users will.

---

### P1.2 — Analytics: Basic Competency Trends

**What:** Simple dashboard showing:
- Average competency level (all users, by role, by department)
- Gap distribution (how many users have gaps > 1.5?)
- Assessment completion rate
- Learning resource usage

**Why:** Institutional leaders want visibility. "Are my people improving?"

**Scope:**
- GET /analytics/competency-summary endpoint
- GET /analytics/gap-distribution endpoint
- GET /analytics/learning-adoption endpoint
- Simple dashboard page (no complex visualizations)

**Effort:** 3-4 weeks

**Success Criteria:**
- Dashboard loads real data (not mock)
- Shows competency trends over time
- Can filter by department/role
- Metrics are accurate (spot-checked vs. direct DB queries)

**SIH Relevance:** 🟡 **IMPORTANT** — Institutional value prop. Without analytics, hard to justify adoption.

---

### P1.3 — Learning Pathway: Simple Multi-Step Sequences

**What:** When a user has a large gap (>2.0), recommend 2-3 resources in sequence (Beginner → Intermediate) instead of one.

**Why:** Large gaps shouldn't be closed by a single course. Need multi-step learning.

**Scope:**
- Detect large gaps (> 2.0)
- Generate 2-3 step pathway (ordered by difficulty)
- Show pathway in UI (step 1/3, step 2/3, etc.)
- Track progress through pathway

**Effort:** 2-3 weeks

**Success Criteria:**
- Python gap 2.5 → pathway has 3 steps
- Steps are ordered (easy → medium → hard)
- User completes step 1 → step 2 unlocks
- Competency updates reflect progress through pathway

**SIH Relevance:** 🟡 **IMPORTANT** — Shows sophistication. Single recommendations look naive for complex gaps.

---

### P1.4 — Live iGOT/NSSTA Resource Integration (IF Access Available)

**What:** Switch from seeded data to live API calls to iGOT/NSSTA platforms.

**Why:** Real content = institutional credibility. Seeded data is honest for Round 1, but live data is impressive for pilots.

**Scope:**
- Confirm iGOT API access is available (key blocker)
- Implement iGOT provider (fetch courses, link to competencies)
- Implement NSSTA provider (fetch training programmes, link to competencies)
- Fallback to seeded data if API unavailable
- No breaking changes to recommendation engine

**Effort:** 6-8 weeks (heavily dependent on API availability and documentation)

**Dependencies:** 
- ✋ **BLOCKER:** Do we have iGOT API credentials? Timeline?
- ✋ **BLOCKER:** Do we have NSSTA API credentials? Timeline?

**Success Criteria:**
- Recommendations pull from live iGOT
- Enrollment links direct to real iGOT courses
- NSSTA programmes visible in recommendations
- Graceful fallback if APIs unavailable

**SIH Relevance:** 🟢 **CRITICAL IF AVAILABLE** — Live integration is a major differentiator. But don't wait for this; proceed with seeded data if not available.

---

### P1.5 — Assessment Result Explanation

**What:** After assessment, show user:
- Why competency increased/decreased (which evidence types contributed)
- Confidence breakdown (why confidence is 0.8 vs. 0.5)
- Next recommended action (take another assessment, learn resource, etc.)

**Why:** Users want to understand their scores. "Why did my competency go from 2.5 to 2.8?"

**Scope:**
- POST /assessments/{id}/submit returns detailed explanation
- Frontend displays:
  - Competency change (2.5 → 2.8 +0.3)
  - Evidence contributing to change
  - Confidence percentage and why
  - Next recommended action

**Effort:** 1-2 weeks

**Success Criteria:**
- User sees clear explanation of score
- Evidence breakdown is accurate
- Confidence is explained
- Next action is suggested

**SIH Relevance:** 🟡 **NICE** — Improves UX but not critical for demo.

---

## P2: LATER (Can defer until institutional pilot feedback)

These are valuable but not prerequisites for Round 1 demo or initial institutional pilots.

### P2.1 — Role Transition Workflows

- User approaching promotion: show learning path for new role requirements
- Recommend "transition learning" (close current gaps + prep for next role)

**Effort:** 2-3 weeks  
**SIH Relevance:** 🔵 NICE — Career development feature, not core loop

---

### P2.2 — Accessibility (WCAG Formal Audit)

- Formal accessibility testing
- ARIA labels, keyboard navigation, screen reader testing
- Target: WCAG 2.1 AA compliance

**Effort:** 3-4 weeks (includes manual testing)  
**SIH Relevance:** 🔵 NICE — Important for production, not demo-critical

---

### P2.3 — Offline-First Support

- Service workers, offline caching
- Queue assessments taken offline
- Sync when reconnected

**Effort:** 3-4 weeks  
**SIH Relevance:** 🔵 NICE — Nice to have, not demo-critical

---

### P2.4 — AI Document Processing

- Upload PDF/PPTX/DOCX
- Extract text, generate questions via LLM
- Add questions to question bank

**Effort:** 6-8 weeks  
**SIH Relevance:** 🔵 NICE — Impressive but requires LLM access; defer

---

### P2.5 — Audit Logging

- Log all admin actions (user changes, role updates, etc.)
- Track assessment attempts, competency updates
- Audit trail for compliance

**Effort:** 2-3 weeks  
**SIH Relevance:** 🔵 NICE — Important for production, not demo

---

## DECISION FRAMEWORK: What to Build Now

### Before Round 1 SIH Submission

**MUST Build:** P0.1 through P0.4 (3-5 days)
- Multiple roles seeded
- Question bank expanded
- Resource mappings complete
- Data consistency audit passed

**CAN BUILD (Optional, improves demo):** P1.1, P1.2 (admin + analytics lite)
- Adds institutional credibility
- 4-6 weeks effort
- Demonstrates scalability

**DO NOT BUILD YET:** P1.3-P1.5 (learning pathways, AI, etc.)
- Core loop works; no need yet
- Save for Phase 2 after judge feedback

### After Round 1 (For Institutional Pilot)

**Build in Order:**
1. P0.1-P0.4 (data quality)
2. P1.1 (admin basics)
3. P1.2 (analytics basics)
4. P1.3 (learning pathways) — only if feedback says gaps are too large
5. P1.4 (live iGOT/NSSTA) — only if API access confirmed

**Do NOT build P2.x unless explicitly requested by pilot stakeholders.**

---

## Implementation Checklist

### Week 1: P0 (Data Quality)

- [ ] Add 3-4 more roles to seed script
- [ ] Expand question bank (40 → 80+ questions)
- [ ] Verify learning resource mappings cover all competencies
- [ ] Run data consistency audit
- [ ] E2E test still passes
- [ ] Demo scenario works (multiple roles, multiple assessments)

**Deliverable:** Clean, robust seed data. Ready for demo.

---

### Week 2-4: P1.1 + P1.2 (Optional, for institutional credibility)

- [ ] Admin user listing API
- [ ] Admin UI mockup
- [ ] Analytics endpoints (summary, gaps, adoption)
- [ ] Analytics UI mockup
- [ ] All endpoints return real data
- [ ] E2E test still passes

**Deliverable:** Admin dashboard shows institutional value.

---

### After Judge Feedback: P1.3+ (Based on Feedback)

- Wait for SIH feedback
- Adapt Phase 2 based on what judges highlight
- Don't assume what's needed; ask

**Deliverable:** Targeted Phase 2 features, not guesses.

---

## Key Decision Point: iGOT/NSSTA Integration

**BLOCKER for P1.4:** Do we have API credentials?

- **If YES:** Timeline? Start P1.4 after P0 + P1.1-P1.2
- **If NO:** Continue with seeded data (honest, not misleading)
- **If UNKNOWN:** Clarify before Phase 2 planning

**Don't start Phase 2 without this clarity.**

---

## Success Metric for This Backlog

**Before Round 1 Submission:**
- ✅ Multiple roles defined (not just 1)
- ✅ Question bank expanded (not just 5 questions/competency)
- ✅ Resource mappings complete (70%+ coverage)
- ✅ Data clean (no orphans, no inconsistencies)
- ✅ E2E test passes (core loop still works)

**For Institutional Pilot:**
- ✅ Admin can list users and view profiles
- ✅ Leaders can see competency trends
- ✅ Large gaps get multi-step learning pathways
- ✅ Live iGOT/NSSTA integration (if available)

**NOT Success Metrics (don't chase these):**
- Feature count ("we have 50 features!")
- Test count ("we have 300 tests!")
- Lines of code ("we wrote 100k lines!")

**Real Success Metric:**
- "The SIH judges understand that the core loop works, and they believe this scales to institutions."

---

## The One Rule

**Before building anything in P1 or P2, ask:**

> "Does this directly solve a requirement from the original SIH 26101 objective, or does it solve a problem an institutional pilot user would have?"

If YES → consider building it.  
If NO → put it in LATER or don't build it.

This prevents feature creep and keeps focus on the actual product vision.

---

## Final Recommendation

### Immediate (This Week)

1. Complete P0.1 through P0.4 (data quality, multiple roles, question expansion)
   - Effort: 3-5 days
   - Risk: Low (mostly configuration)
   - Impact: Round 1 demo is robust and scalable-looking

2. Review iGOT/NSSTA integration status
   - Do we have credentials?
   - What's the timeline?
   - Document decision

### Next 2-4 Weeks (Conditional)

3. **If SIH submission deadline allows + institutional pilot is confirmed:**
   - Build P1.1 + P1.2 (admin + analytics basics)
   - Shows institutional scalability
   - Improves pilot conversations

4. **If SIH submission deadline is tight:**
   - Skip P1.1-P1.2 for now
   - Focus on P0 (data quality)
   - Build P1.x after judges' feedback

### After Round 1

5. Gather judge feedback
6. Adapt Phase 2 roadmap based on feedback
7. Build only what judges/pilots actually need

---

## Summary

**P0 (Data Quality):** 3-5 days. Required. Non-negotiable.

**P1 (Institutional Features):** 2-6 weeks. Important. But wait for judge feedback before building.

**P2 (Advanced Features):** Defer. Build only after feedback.

**The Golden Rule:** Don't build features because they sound cool. Build them because they solve a real requirement or user problem.

ShikshaSetu's core loop is proven. Now make sure the demo and institutional features are bulletproof.
