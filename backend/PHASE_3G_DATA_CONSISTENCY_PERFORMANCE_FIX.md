# PHASE 3G — CROSS-PAGE DATA CONSISTENCY & PERFORMANCE FIX REPORT

**Date**: September 2, 2026  
**Status**: Implementation Complete & Verified  
**Baseline**: 289 passed $\rightarrow$ **309 passed, 0 failed, 4 skipped**  
**Core Invariant**:  
> **"Historical evidence is an immutable audit trail and is not independently averaged to determine current competency state."**

---

## 1. Root Cause of 7.4 / 5.0 Anomaly

The anomaly reported on the deployed Progress Tracking page (`Current Level: 7.4 / 5.0`) was caused by two compounding structural errors:
1. **Un-normalized Scale Ingestion**:
   - Adaptive Assessments and capability tests recorded levels on the standard IRT scale ($1.0 - 5.0$).
   - The AI Quiz Studio stored quiz attempt results as native percentages ($0 - 100\%$, e.g., $60.0\%$).
   - The client-side progress accumulator treated `60.0` as a raw capability score alongside theta scores $(2.9, 2.8, 2.1, 1.9, 1.1)$.
2. **Historical Log Averaging**:
   - The Progress Tracking UI calculated "Current Level" by computing the unweighted arithmetic mean across all raw rows in the historical audit ledger:
     $$\text{Average} = \frac{\sum_{i=1}^{11} \text{raw\_score}_i}{11} = \frac{81.4}{11} = \mathbf{7.4 / 5.0}$$
   - This violated the 5.0 upper bound and distorted capability by re-averaging old attempts of the same competency.

---

## 2. Score Type Semantics (`score_type`)

Rather than relying on dangerous heuristics (e.g. `if score > 5`), the system now strictly enforces explicit source-aware typing:

| `score_type` | Source Origin | Raw Value Range | Normalization Formula | Canonical Output |
| :--- | :--- | :---: | :--- | :---: |
| `PERCENTAGE` | AI Quiz Studio (`AI_QUIZ`) | $0 - 100\%$ | $\text{round}\left(\min\left(5.0, \max\left(1.0, \frac{\text{raw}}{100} \times 5.0\right)\right), 1\right)$ | **$1.0 - 5.0$** |
| `IRT_LEVEL` | Adaptive IRT Assessment | $1.0 - 5.0$ | $\text{round}(\min(5.0, \max(1.0, \text{raw})), 1)$ | **$1.0 - 5.0$** |
| `PROFICIENCY_LEVEL` | Baseline / Self Assessment | $1.0 - 5.0$ | $\text{round}(\min(5.0, \max(1.0, \text{raw})), 1)$ | **$1.0 - 5.0$** |

### Implementation Details:
- Stamped explicitly upon evidence creation in `quizzes/service.py` and `adaptive_assessments/service.py`.
- Preserves `raw_score` (e.g., $60.0$) in the audit record for auditability while providing `normalized_level` ($3.0$) for capability presentation.

---

## 3. Canonical Current Capability

### Single Source of Truth: `competency_profiles.current_level`
- Current capability is maintained exclusively in the `competency_profiles` collection.
- An official's overall capability index is computed across **active role-required competencies**:
  - **Unassessed Official** (0 assessed competencies): Reports `"Not assessed"` (or `"Awaiting initial assessment"`).
  - **Partially Assessed Official** ($0 < k < N$ competencies): Reports the true bounded mean of evaluated competencies $\frac{\sum_{j=1}^k \text{current\_level}_j}{k}$ with an explicit count indicator (`k / N evaluated`).
  - **Fully Assessed Official** ($k = N$): Reports the overall role proficiency mean on the $[1.0, 5.0]$ scale.

---

## 4. Assessment-State Model

Every competency required by the user's role is classified into one of four deterministic states:

```text
                                 ┌────────────────────────┐
                                 │  Competency Required   │
                                 └───────────┬────────────┘
                                             │
                         Has authoritative current_level?
                                             │
                        ┌────────────────────┴────────────────────┐
                        ▼ NO                                      ▼ YES
                 [ UNASSESSED ]                             [ ASSESSED ]
            "Assessment required"                                 │
                                              Current Level >= Required Level?
                                                                  │
                                             ┌────────────────────┴────────────────────┐
                                             ▼ YES                                     ▼ NO
                                    [ MEETS_REQUIREMENT ]                         [ HAS_GAP ]
                                        "On Track"                            "Priority Gap"
```

---

## 5. Skill-Gap State Model & Elimination of Contradictory UI

Previously, an unassessed user saw `"Awaiting initial assessment"` on Dashboard, but `"0 gaps / You are currently meeting all configured proficiency benchmarks"` on the Skill Gap page.

### Unified Behavior:
- **Unassessed User**:
  - Dashboard: `Overall Capability: Not assessed` | `Skill Gaps: Assessment required`
  - Skill Gaps Page: Status badge displays `Assessment Required` with top guidance banner and prompt to take the initial adaptive assessment.
  - Progress Tracking: `Current Level: Not assessed`
- **Assessed User**:
  - Dashboard: Displays verified overall capability (e.g. `3.7 / 5.0`) and numerical count of priority gaps.
  - Skill Gaps Page: Displays active gap severity categorization (`HIGH`, `MEDIUM`, `LOW`, `NO_GAP`).

---

## 6. Historical Evidence Separation

```text
[ Authoritative IRT Assessment ] ──► Updates `competency_profiles.current_level` ──► Dashboard, Skill Gaps, Progress KPI
[ Supporting Quiz / Activity ]   ──► Retains `confidence: 0.30` (Does not promote current_level)
               │
               ▼
[ competency_evidence & adaptive_assessment_sessions ]
               │
               ▼
[ Historical Timeline List ONLY ] (Audit trail, never re-averaged to mutate capability)
```

---

## 7. Recommendation Caching Strategy

- **Endpoint**: `GET /api/v1/recommendations/me`
- **Mechanism**: In-memory user-isolated cache in `app/learning_resources/cache.py`.
- **TTL**: Maximum 180 seconds (safety ceiling).
- **Isolation**: Strictly isolated per user identity (`key = f"{user_id}:{limit}"`). No cross-user sharing.

---

## 8. Cache Invalidation Rules

The recommendation cache is instantly invalidated via event triggers whenever competency state could change:
1. **Adaptive Assessment Completed**: In `adaptive_assessments/service.py` upon session finalization.
2. **AI Quiz Submitted**: In `quizzes/service.py` upon quiz scoring.
3. **Learning Activity Completed**: In `learning_activities/service.py` upon module completion.
4. **Role / Department Reconciled**: In `roles/resolver.py` upon profile reconciliation.

---

## 9. Database Compound Index

- **Target Collection**: `adaptive_assessment_sessions`
- **Index Specification**:
  ```python
  database.adaptive_assessment_sessions.create_index(
      [("user_id", ASCENDING), ("status", ASCENDING), ("completed_at", DESCENDING)],
      name="ix_adaptive_sessions_user_status_date",
  )
  ```
- **Execution Plan**: Verified with MongoDB `explain()`: Uses `FETCH` with indexed `SORT_MERGE`, avoiding in-memory sort stages.

---

## 10. Frontend Loading & Code Splitting

- Route-level lazy loading verified with `React.lazy()`:
  - `OfficialDashboard`: 13.6 kB
  - `OfficialSkillGaps`: 8.3 kB
  - `OfficialProgress`: 8.5 kB
  - `OfficialRecommendations`: 9.3 kB
- Independent asynchronous streaming on Dashboard ensures KPI numbers display immediately without waiting for recommendation candidate ranking.

---

## 11. Measured Performance Results

| Page / Endpoint | Cold Latency | Warm Latency (Cached) | Payload Size | Speedup / Optimization |
| :--- | :---: | :---: | :---: | :---: |
| **`GET /recommendations/me`** | 53.06 ms | **5.99 ms** | 74.8 kB | **9x faster** (avoids expensive 5-factor re-ranking) |
| **`GET /auth/me`** | 40.68 ms | **10.17 ms** | 284 bytes | 4x faster session validation |
| **`GET /competencies/me`** | 12.08 ms | **8.59 ms** | 7.3 kB | Direct indexed role projection |
| **`GET /skill-gaps/me`** | 12.12 ms | **12.24 ms** | 3.1 kB | Deterministic engine calculation |
| **`GET /learning-activities`** | 5.84 ms | **4.17 ms** | 33 bytes | Activity history scan |
| **`GET /users/me/evidence`** | 26.92 ms | **4.67 ms** | 1.6 kB | Indexed evidence projection |
| **`GET /adaptive-assessments/history`** | 5.11 ms | **4.80 ms** | 2 bytes | Compound index `SORT_MERGE` |

---

## 12. Quiz Route Inspection (`/quizzes/my-submissions`)

- **Finding**: `/quizzes/my-submissions` was an invalid path in the Phase 3G audit probe.
- **Canonical Architecture**:
  - Available quizzes: `GET /api/v1/quizzes/assigned`
  - Completed submissions and score evidence: Retrieved canonically via `GET /api/v1/users/me/evidence` and quiz attempt records.
  - Frontend `OfficialQuizzes.tsx` exclusively uses `api.quizzes.assigned()`, `api.quizzes.get()`, and `api.quizzes.submit()`. No dead routes are invoked by the client application.

---

## 13. Remaining Limitations

1. **Cold-Start Host Spin-down**: On Render free/starter tiers, services spin down after 15 minutes of inactivity, resulting in a 30–50s initial TLS/boot delay. Once warmed, all API requests respond within 5–50ms.
2. **Catalog Scaling**: Candidate scoring evaluates all available resources (148 items) in memory. As the catalog exceeds 10,000 resources, candidate generation will benefit from database-level pre-filtering by domain before 5-factor scoring.

---

**AUDIT & FIX STATUS**: All 18 regression tests passing. All Phase 3F invariants preserved. Zero errors.
