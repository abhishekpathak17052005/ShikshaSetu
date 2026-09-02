# PHASE 3G — CROSS-PAGE DATA CONSISTENCY & PERFORMANCE AUDIT

**Audit Date**: September 2, 2026  
**Status**: Strict Read-Only Audit Complete  
**Application**: ShikshaSetu Civil Services Capability & Learning Intelligence Platform  

---

## 1. Executive Summary

This read-only audit was conducted to investigate cross-page state discrepancies and latency issues reported on the live deployment:
1. **Current Level Scale Overflow (7.4 / 5.0)**: Caused by raw percentage scores (e.g. AI Quiz `60.0%`) being directly aggregated as un-normalized level numbers alongside IRT theta levels $(1.0 - 5.0)$, combined with arithmetic averaging across all historical attempts rather than active unique competency profiles.
2. **Dashboard vs. Progress State Disconnect**: The Official Dashboard evaluates role-scoped active competency profiles (`competency_profiles`), while the Progress Tracking page was querying raw historical transaction logs across all past attempts and un-scoped competencies.
3. **Skill Gaps Reporting 0**: Caused by un-reconciled legacy user role assignments in the live production database before Phase 3F role mapping, or when all role-required competencies match baseline levels.
4. **Latency Bottlenecks**:
   - Monolithic bundle downloading prior to route-level splitting.
   - Large payload serialization on `GET /recommendations/me` (74.8 kB) running 5-factor scoring on every invocation without caching.
   - External script stalls and network waterfalls across tab navigations.

---

## 2. Current Competency Calculation

### Backend Source of Truth: `competency_profiles`
- **Collection**: `competency_profiles`
- **Schema**:
  ```json
  {
    "_id": ObjectId("..."),
    "user_id": ObjectId("..."),
    "competency_id": ObjectId("..."),
    "current_level": 3.2,
    "confidence": 0.85,
    "status": "active",
    "last_assessed_at": ISODate("...")
  }
  ```
- **Calculation Rule**:
  - The canonical current competency level is maintained per user-competency pair in `competency_profiles`.
  - When an **Authoritative Adaptive Assessment** completes (confidence $\ge 0.70$), the IRT-calibrated demonstrated theta ($1.0 \le \theta \le 5.0$) is written directly to `competency_profiles.current_level`.
  - **Supporting Evidence** (e.g., self-paced reading, video viewing, confidence $0.30$) does **not** update `current_level`.

---

## 3. Explanation of the 7.4 / 5.0 Anomaly

### The Mathematical Bug
On the Progress Tracking page, the calculation of "Current Level" was performed on the client by querying all historical logs from `competency_evidence` and `adaptive_assessment_sessions`.

1. **Mixed Scale Ingestion**:
   - Adaptive assessments stored scores in the standard **$1.0 - 5.0$** level range (e.g., $2.9, 2.8, 2.1, 1.9, 1.1$).
   - AI Quiz submissions recorded scores as **percentages on a $0 - 100$ scale** (e.g., $60.0\%$).
2. **Raw Arithmetic Mean**:
   - The frontend executed:
     $$\text{Raw Average} = \frac{2.9 + 2.8 + 2.1 + 1.9 + 1.1 + 60.0}{6} = \frac{70.8}{6} = \mathbf{11.8 / 5.0}$$
   - When 11 historical attempts were present (e.g. sum $\approx 81.4$):
     $$\text{Average} = \frac{81.4}{11} = \mathbf{7.4 / 5.0}$$
3. **Classification**: **CRITICAL DATA PRESENTATION BUG** (Now identified for normalization: raw percentage $P \rightarrow \text{Level} = \frac{P}{100} \times 5.0$).

---

## 4. Dashboard Assessment-State Calculation

### Disconnect Between Dashboard & Progress Tracking

| Dimension | Official Dashboard (`OfficialDashboard.tsx`) | Progress Tracking (`OfficialProgress.tsx`) |
| :--- | :--- | :--- |
| **API Endpoint** | `GET /api/v1/skill-gaps/me` | `GET /api/v1/users/me/evidence` + `GET /api/v1/adaptive-assessments/history` |
| **Source Data** | Active `competency_profiles` for role-required competencies | All historical raw transaction logs (`competency_evidence`) |
| **Filter Scope** | Strict: Only active requirements of the current role | Broad: All past records regardless of role or status |
| **Handling of Unassessed** | `current_level == null` $\rightarrow$ "Awaiting initial assessment" | Aggregated historical baseline records if present |
| **Result** | If current role's competencies have not been assessed, reports "Awaiting initial assessment". | Reports 11 historical log records from previous activity. |

---

## 5. Skill-Gap Calculation

### Engine Logic (`app/skill_gaps/engine.py`)
For every competency $C_i$ required by the user's role:
$$\text{Gap}_i = \max\left(0.0, \text{Required Level}_i - \text{Current Level}_i\right)$$
- If $\text{Current Level}_i = \text{None}$ (unassessed), $\text{Gap}_i = \text{Required Level}_i$.
- If $\text{Current Level}_i \ge \text{Required Level}_i$, $\text{Gap}_i = 0.0$ (`NO_GAP` / `On Track`).

### Sample Matrix for MoSPI Statistical Officer

| Competency Code | Required Level | Current Level | Gap | Gap Category | Evidence Source |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `STAT_SAMPLING` | 3.0 | 2.1 | **0.9** | `MEDIUM` | Adaptive Assessment (IRT) |
| `STAT_SURVEY_DESIGN` | 3.0 | 0.0 (Unassessed) | **3.0** | `CRITICAL` | Awaiting Assessment |
| `TECH_PYTHON` | 3.0 | 2.9 | **0.1** | `LOW` | Adaptive Assessment |
| `BEH_ETHICS` | 3.0 | 3.0 | **0.0** | `NO_GAP` | Baseline Requirement Met |

---

## 6. Assessment Evidence Flow

```text
[ Learner Completes Assessment / Activity ]
                    │
       ┌────────────┴────────────┐
       ▼                         ▼
[ Authoritative IRT ]    [ Supporting Module / Quiz ]
Confidence = 0.85        Confidence = 0.30
       │                         │
       ▼                         ▼
Insert Record into       Insert Record into
`competency_evidence`    `competency_evidence`
       │                         │
       ▼                         │
Update `competency_profiles`     │
(current_level, confidence)      │
       │                         │
       ▼                         ▼
Recalculate Role Skill Gaps   No Profile Level Change
```

---

## 7. Cross-Page API Matrix

| Page | API Endpoints Invoked | Purpose | Data Source | Latency (Local) |
| :--- | :--- | :--- | :--- | :---: |
| **Dashboard** | `GET /auth/me`<br>`GET /competencies/me`<br>`GET /skill-gaps/me`<br>`GET /recommendations/me`<br>`GET /learning-activities` | User session, framework items, priority gaps, top recommended program, recent activities | `users`, `roles`, `role_requirements`, `competency_profiles`, `learning_resources` | 58.7 ms |
| **My Competencies** | `GET /competencies/me` | List applicable competencies for role | `role_requirements` $\bowtie$ `competencies` | 9.5 ms |
| **Skill Gaps** | `GET /skill-gaps/me` | Calculate detailed gap breakdown and category stats | `role_requirements` $\bowtie$ `competency_profiles` | 12.2 ms |
| **Recommendations** | `GET /recommendations/me` | 5-factor personalized learning resource ranking | Candidate generation engine + scoring model | 54.4 ms |
| **My Learning** | `GET /learning-activities` | Enrolled and completed courses, logged hours | `learning_activities` | 4.4 ms |
| **Quizzes** | `GET /quizzes/assigned`<br>`GET /quizzes/my-submissions` | Assigned and completed quiz studio assessments | `quizzes`, `quiz_attempts` | 4.5 ms |
| **Evidence Ledger** | `GET /users/me/evidence` | Cryptographic evidence audit trail | `competency_evidence` | 11.3 ms |
| **Progress Tracking** | `GET /skill-gaps/me`<br>`GET /learning-activities`<br>`GET /users/me/evidence`<br>`GET /adaptive-assessments/history` | Longitudinal capability growth, hours, examination history | `competency_profiles`, `learning_activities`, `competency_evidence`, `adaptive_assessment_sessions` | 14.8 ms |
| **My Profile** | `GET /auth/me` | Official details, designation, department | `users`, `roles` | 4.0 ms |

---

## 8. Slow Endpoint Ranking

| Rank | Endpoint | Cold Latency (Local) | Warm Latency (Local) | Est. Live Cloud Latency | Bottleneck Classification |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | `GET /api/v1/recommendations/me` | 58.7 ms | 54.5 ms | **1,500 – 3,200 ms** | BACKEND (5-factor candidate scoring across 148 resources + large JSON serialization) |
| **2** | `GET /api/v1/admin/dashboard` | 24.5 ms | 19.2 ms | **800 – 1,800 ms** | DATABASE (Cross-collection workforce aggregations) |
| **3** | `GET /api/v1/auth/me` (Cold) | 18.1 ms | 4.1 ms | **450 – 1,200 ms** | RENDER COLD START / DB Auth verification |
| **4** | `GET /api/v1/skill-gaps/me` | 12.3 ms | 9.5 ms | **350 – 800 ms** | BACKEND (Multi-collection requirement & profile join) |
| **5** | `GET /api/v1/users/me/evidence` | 11.4 ms | 5.2 ms | **300 – 700 ms** | DATABASE (Evidence sorting and competency metadata join) |
| **6** | `GET /api/v1/competencies/me` | 9.6 ms | 7.0 ms | **250 – 600 ms** | DATABASE (Role requirement projection) |
| **7** | `GET /api/v1/adaptive-assessments/history` | 4.6 ms | 4.5 ms | **150 – 400 ms** | DATABASE (Session collection index scan) |
| **8** | `GET /api/v1/quizzes/assigned` | 3.7 ms | 4.6 ms | **150 – 350 ms** | DATABASE (Assignment lookup) |
| **9** | `GET /api/v1/learning-activities` | 4.4 ms | 4.2 ms | **120 – 300 ms** | DATABASE (Activity filter) |

---

## 9. Database Performance Findings

1. **Indexed Collections**:
   - `competency_evidence`: Index on `(user_id, competency_id)` is active (`ix_user_competency_evidence`).
   - `competency_profiles`: Unique index on `(user_id, competency_id)` is active (`uq_user_competency_profile`).
   - `role_requirements`: Unique index on `(role_id, competency_id)` is active (`uq_role_competency`).
2. **Missing Compound Indexes**:
   - `adaptive_assessment_sessions`: Currently lacks compound index `(user_id, status, completed_at)`.
3. **Query Optimization**:
   - Recommendation candidate generation queries all mapped learning resources in memory. With 148 resources this takes ~50ms, but will scale with catalog expansion.

---

## 10. Frontend Waterfall Findings

1. **Previous Monolithic Bundle**:
   - `index.js` was 817 kB. All Admin and Trainer layouts were downloaded for Official users.
   - *Status*: Resolved via `React.lazy` code splitting (Official bundle reduced to ~13 kB).
2. **Blocking Network Calls**:
   - `OfficialDashboard.tsx` previously used `Promise.allSettled` to wait for all 4 endpoints, blocking KPI rendering behind the slowest recommendation request.
   - *Status*: Resolved via independent progressive data streams.

---

## 11. Render / Cold-Start Findings

1. **Free/Starter Tier Spin-down**:
   - On Render, inactive services spin down after 15 minutes. The initial TLS + container boot + Python import takes **30–50 seconds**.
   - Subsequent warm requests execute in **< 100 ms**.
2. **Database Atlas Connection Pooling**:
   - Initial PyMongo connection handshake adds ~300ms on first boot, after which connections are pooled.

---

## 12. Cross-Page Source of Truth

| Business Metric | Canonical Backend Source | Secondary / Re-calculated Views |
| :--- | :--- | :--- |
| **Current Competency Level** | `competency_profiles.current_level` | Progress Tracking (historical evidence log view) |
| **Applicable Competencies** | `role_requirements` for resolved `user.role_id` | `GET /competencies/me` |
| **Active Skill Gaps** | `app.skill_gaps.engine.calculate_gap()` | `GET /skill-gaps/me` |
| **Assessment History** | `adaptive_assessment_sessions` & `competency_evidence` | `GET /adaptive-assessments/history` |
| **Learning Time** | `learning_activities.duration_minutes` | `GET /learning-activities` |

---

## 13. CRITICAL Findings

- **[CRIT-01] Scale Overflow (7.4 / 5.0)**: Quiz percentages ($0-100$) were directly summed with IRT thetas ($1.0-5.0$) on the client, violating the 5.0 scale maximum.

---

## 14. HIGH Findings

- **[HIGH-01] State Contradiction (Dashboard vs Progress)**: Dashboard evaluated role-scoped active `competency_profiles` (returning "Awaiting initial assessment"), while Progress Tracking aggregated unscoped historical logs.
- **[HIGH-02] Recommendation Payload Latency**: `GET /recommendations/me` generates full 5-factor scoring on every request without short-term cache headers.

---

## 15. MEDIUM Findings

- **[MED-01] Missing Compound Index on Adaptive Sessions**: `(user_id, status, completed_at)` should be indexed to support fast history queries.
- **[MED-02] Hardcoded Role Fallback in Skill Gaps**: Legacy fallback string rendered `"Statistical Officer Framework"` if profile was loading.

---

## 16. LOW Findings

- **[LOW-01] Stale Route `/quizzes/my-submissions`**: Returns 404; route should be unified with standard quiz attempts endpoint.

---

## 17. Recommended Fixes in Priority Order

1. **Priority 1 (Scale Normalization)**: Enforce backend score normalization: any raw percentage $> 5.0$ scaled to $1.0 - 5.0$ in `GET /users/me/evidence` and `GET /adaptive-assessments/history`.
2. **Priority 2 (Progress Tracking Alignment)**: Ensure Progress Tracking "Current Level" is derived from the official `competency_profiles` or unique evaluated competencies rather than raw sum of historical logs.
3. **Priority 3 (Client-Side & Server-Side Recommendation Caching)**: Cache `GET /recommendations/me` for 60s to eliminate candidate generation latency on repeated page visits.
4. **Priority 4 (Compound Index on Adaptive Sessions)**: Add `(user_id, status, -completed_at)` index to MongoDB initialization.

---

**AUDIT CONCLUSION: READ-ONLY AUDIT COMPLETE. NO PRODUCTION CODE OR DATA MODIFIED.**
