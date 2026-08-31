# ShikshaSetu — Decision Tree for Phase 2

**Start here.** Answer the questions. Follow the path. Build accordingly.

---

## DECISION 1: What is your primary goal right now?

```
                    PRIMARY GOAL?
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   [A]              [B]              [C]
  SIH            Small            Full
  Demo           Pilot           Scale
  Only         (10-20)           (50+)
   │               │               │
   │               │               │
   ▼               ▼               ▼
(Follow A)    (Follow B)      (Follow C)
```

---

## PATH A: SIH DEMO ONLY (No Institutional Features)

**Goal:** Impress SIH judges with working core loop

**Timeline:** < 2 weeks

**Your path:**
```
         START (This Week)
              │
              ▼
    ┌─────────────────────┐
    │  CLARIFY DEADLINE   │
    │  Do we have time?   │
    │  < 2 weeks → YES    │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │    EXECUTE P0 ONLY (5-10 days)  │
    │                                 │
    │  • Add 3-4 more roles           │
    │  • Expand question bank         │
    │  • Verify resource mappings     │
    │  • Data consistency audit       │
    │  • E2E test passes              │
    │                                 │
    │  Output: Bulletproof demo data  │
    └─────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │      DRY RUN DEMO (2 days)      │
    │                                 │
    │  • Register user                │
    │  • Take assessment              │
    │  • View gaps                    │
    │  • Get recommendations          │
    │  • Start learning               │
    │  • Take second assessment       │
    │  • Verify competency update     │
    │                                 │
    │  Test with multiple roles       │
    │  Document findings              │
    └─────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │   SUBMIT TO SIH JUDGES          │
    │                                 │
    │  Show: Core loop works          │
    │  Show: Learning ≠ Assessment    │
    │  Show: Competency updates       │
    │  Show: Multi-user isolation     │
    └─────────────────────────────────┘
              │
              ▼
         WAIT FOR FEEDBACK
```

**What to build:** P0 only (data quality)

**What NOT to build:** P1, P2 features (admin, analytics, etc.)

**Expected outcome:** Working demo that proves concept

**After SIH:** Gather feedback → Decide if pilot needed → Plan Phase 2

---

## PATH B: SMALL PILOT (10-20 Real Users)

**Goal:** Prove system works with real users + institutional features

**Timeline:** 2-4 weeks

**Your path:**
```
         START (This Week)
              │
              ▼
    ┌──────────────────────────────────┐
    │  CLARIFY 3 QUESTIONS             │
    │                                  │
    │  1. SIH deadline? (2-4 weeks)     │
    │  2. iGOT/NSSTA API? (unknown OK) │
    │  3. Pilot timeline? (soon)        │
    │                                  │
    │  Document answers               │
    └──────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │    EXECUTE P0 (5-10 days)        │
    │                                  │
    │  (Same as Path A)                │
    │                                  │
    │  + Prepare demo for SIH          │
    └──────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │   SUBMIT DEMO TO SIH (Optional)  │
    │                                  │
    │   (Or skip if no deadline)       │
    └──────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │   EXECUTE P1.1 (4-6 days)        │
    │   Admin User Management          │
    │                                  │
    │  • GET /admin/users endpoint     │
    │  • GET /admin/users/{id}         │
    │  • Admin UI: user list           │
    │  • Admin UI: user detail         │
    │  • Filtering by role, dept       │
    │                                  │
    │  Output: Admin can see users     │
    └──────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │   EXECUTE P1.2 (4-6 days)        │
    │   Analytics: Lightweight          │
    │                                  │
    │  • GET /analytics/competency-    │
    │    summary endpoint              │
    │  • GET /analytics/gap-           │
    │    distribution endpoint         │
    │  • GET /analytics/learning-      │
    │    adoption endpoint             │
    │  • Analytics dashboard page      │
    │                                  │
    │  Output: Leaders see trends      │
    └──────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │   PILOT WITH 10-20 USERS         │
    │                                  │
    │  • Onboard users (admin UI)      │
    │  • Users take assessments        │
    │  • Track learning progress       │
    │  • Leaders view analytics        │
    │  • Gather feedback               │
    │                                  │
    │  Duration: 2-4 weeks             │
    └──────────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────────┐
    │   ANALYZE PILOT FEEDBACK         │
    │                                  │
    │  What worked?                   │
    │  What didn't?                   │
    │  What's missing?                │
    │  What's next?                   │
    │                                  │
    │  Plan Phase 2 based on actual   │
    │  user needs, not guesses        │
    └──────────────────────────────────┘
              │
              ▼
         PHASE 2 PLANNING
```

**What to build:** P0 + P1.1 + P1.2 (data + admin + analytics)

**What NOT to build yet:** P1.3-P1.5, P2

**Expected outcome:** Working institutional system with user/analytics management

**After pilot:** Feedback-driven Phase 2 planning

---

## PATH C: FULL SCALE (50+ Users, Production Ready)

**Goal:** Complete institutional system ready for rollout

**Timeline:** 4-8 weeks

**Your path:**
```
         START (This Week)
              │
              ▼
    ┌────────────────────────────────────┐
    │   CLARIFY 3 QUESTIONS              │
    │                                    │
    │   1. SIH deadline? (4+ weeks)       │
    │   2. iGOT/NSSTA? (plan to get API) │
    │   3. Pilot? (YES - after build)    │
    │                                    │
    │   Document answers                │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │      EXECUTE P0 (5-10 days)        │
    │   Data Quality & Multiple Roles    │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │    EXECUTE P1.1 (4-6 days)         │
    │    Admin User Management           │
    │                                    │
    │  • Full CRUD on users              │
    │  • Role assignment                 │
    │  • Bulk import (CSV)               │
    │  • Department management           │
    │  • Audit logging                   │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │    EXECUTE P1.2 (4-6 days)         │
    │    Analytics & Reporting           │
    │                                    │
    │  • Competency trends               │
    │  • Gap distribution                │
    │  • Learning adoption               │
    │  • Assessment performance          │
    │  • Department summaries            │
    │  • Institutional dashboards        │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │    EXECUTE P1.3 (2-3 weeks)        │
    │   Learning Pathways                │
    │                                    │
    │  • Multi-step sequences            │
    │  • Difficulty progression          │
    │  • Prerequisite chains             │
    │  • Adaptive routing                │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │    EXECUTE P1.4 (6-8 weeks)        │
    │   Live iGOT/NSSTA Integration      │
    │                                    │
    │  [DECISION POINT]                  │
    │                                    │
    │  API credentials available?        │
    │    YES → Implement live APIs       │
    │    NO  → Continue w/ seeded data   │
    │           (mark as prototype)      │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │    EXECUTE P1.5 (2-3 weeks)        │
    │   Assessment Result Explanation    │
    │                                    │
    │  • Evidence breakdown              │
    │  • Confidence explanation          │
    │  • Next action recommendation      │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │  EXECUTE P2.1 (3-4 weeks)          │
    │  Accessibility & Offline           │
    │                                    │
    │  • WCAG 2.1 AA compliance          │
    │  • Service worker setup            │
    │  • Offline caching                 │
    │  • Sync on reconnect               │
    │                                    │
    │  (Or defer if time is tight)       │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │   PILOT WITH 50+ USERS (4 weeks)   │
    │                                    │
    │  • Test at scale                   │
    │  • Performance testing             │
    │  • User feedback                   │
    │  • Production readiness            │
    └────────────────────────────────────┘
              │
              ▼
    ┌────────────────────────────────────┐
    │   PRODUCTION DEPLOYMENT            │
    │                                    │
    │  • Database backups                │
    │  • Monitoring setup                │
    │  • Incident response plan          │
    │  • User training                   │
    │  • Go live                         │
    └────────────────────────────────────┘
```

**What to build:** P0 + P1.1 + P1.2 + P1.3 + P1.4 (if API available) + P1.5 + P2.1

**What NOT to build yet:** AI document processing, advanced ML

**Expected outcome:** Production-ready institutional system

**Timeline:** 8-12 weeks full build + 4 week pilot = ~4 months

---

## HOW TO CHOOSE YOUR PATH

**Ask yourself:**

1. **"Are we demoing to SIH judges in < 2 weeks?"**
   - YES → PATH A (demo only)
   - NO → Continue to Q2

2. **"Do we need institutional features before full rollout?"**
   - YES, but small pilot first → PATH B
   - YES, and we need everything → PATH C
   - NO, just demo → PATH A

3. **"What's our real timeline?"**
   - < 2 weeks → PATH A
   - 2-4 weeks → PATH B (maybe)
   - 4-8 weeks → PATH B or C

---

## THE BLOCKER: iGOT/NSSTA API Access

**This affects Path C only.**

**Check NOW:**

```
Do we have iGOT API credentials?
└─ YES → Proceed with P1.4 in timeline
└─ NO, but getting them → Plan for later
└─ NO and not planned → Use seeded data forever

Do we have NSSTA API credentials?
└─ YES → Proceed with P1.4 in timeline
└─ NO, but getting them → Plan for later
└─ NO and not planned → Use seeded data forever
```

**Don't wait until Week 6 to discover API access is missing.**

---

## QUICK REFERENCE: WHAT EACH PATH BUILDS

| Component | Path A | Path B | Path C |
|-----------|--------|--------|--------|
| P0: Data Quality | ✅ | ✅ | ✅ |
| P1.1: Admin | ❌ | ✅ | ✅ |
| P1.2: Analytics | ❌ | ✅ | ✅ |
| P1.3: Pathways | ❌ | ❌ | ✅ |
| P1.4: Live APIs | ❌ | ❌ | ✅* |
| P1.5: Explanations | ❌ | ❌ | ✅ |
| P2.1: Accessibility | ❌ | ❌ | ✅ |
| **Timeline** | **5-10d** | **2-4w** | **8-12w** |
| **Effort** | **Minimal** | **Moderate** | **Substantial** |
| **Goal** | Demo | Pilot | Production |

*If API credentials available

---

## DECISION CHECKLIST

Before you proceed with ANY path, confirm:

```
☐ SIH deadline confirmed (or: no SIH deadline)
☐ Pilot timeline confirmed (or: no pilot planned)
☐ iGOT/NSSTA API status confirmed (or: continuing with seeded data)
☐ Decision on PATH A / B / C made
☐ Team understands scope
☐ Timeline approved by stakeholders
☐ Resources allocated (backend dev, frontend dev, QA)
```

Once all 7 items are checked:

✅ **START EXECUTING YOUR PATH**

---

## IF YOU'RE UNSURE: Default Recommendation

**For most teams:** **PATH B (Small Pilot)**

Why?
- Gives you SIH demo capability (Path A features included)
- Adds institutional features (admin + analytics)
- Not overcommitting to full production build (Path C)
- Gets real user feedback before major investment
- Timeline is reasonable (2-4 weeks)
- Sets up Phase 2 for informed decision-making

**Execute:** P0 → P1.1 → P1.2 → Pilot → Listen to feedback → Phase 2 planning

---

## FINAL DECISION: Which Path?

```
                    YOU ARE HERE
                         │
              I need to answer 3 questions:
              
              1. SIH deadline? _______________
              2. iGOT/NSSTA API? ____________
              3. Pilot planned? _____________
              
              
              Based on my answers, I choose:
              
              [ ] PATH A — Demo only (tight)
              [ ] PATH B — Small pilot (comfortable)
              [ ] PATH C — Full scale (ambitious)
              
              
              Next action: Execute tasks for my path
```

---

**Choose your path. Execute it with confidence. Listen to feedback. Iterate.**

The core loop works. You've proven it. Now build what your users actually need.
