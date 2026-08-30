# PHASE 3: RECOMMENDATION ENGINE — APPROVED SUMMARY

**Status:** ✅ Approved for implementation  
**Changes Made:** 5 based on user feedback  
**Baseline:** 139/139 tests passing  
**Timeline:** 3 weeks  

---

## CHANGES FROM INITIAL AUDIT

### ❌ Removed: Engagement Quality (5%)
- Don't use completion rates, ratings, popularity
- We don't have reliable real learner telemetry yet
- Can be added later when actual usage data exists

### ✅ Revised: Scoring Formula
**Before (6 components):**
- competency_match: 35%
- gap_priority: 25%
- role_match: 15%
- difficulty_match: 15%
- prerequisite_match: 5%
- **engagement_quality: 5%** ❌ Removed

**After (5 components) - FINAL:**
- competency_match: **40%**
- gap_priority: **25%**
- role_match: **20%**
- difficulty_match: **10%**
- prerequisite_match: **5%**

**Total: 100%** ✅

---

### ✅ Made Configurable
```python
class RecommendationScoringConfig:
    competency_match_weight: float = 0.40
    gap_priority_weight: float = 0.25
    role_match_weight: float = 0.20
    difficulty_match_weight: float = 0.10
    prerequisite_match_weight: float = 0.05
```

Weights can be tuned later without code changes (A/B testing in Phase 4).

---

### ✅ NO Invented Metadata
**Before:** If data missing, assume optimistic (1.0)  
**After:** If data missing, use neutral (0.5)

**Examples:**
- Unknown difficulty → 0.5 (not 1.0)
- Unknown target_roles → 0.5 (not 1.0)
- Missing prerequisites → 1.0 (no barrier, not 0.5)

---

### ✅ Smaller Prototype Dataset
**Before:** 50+ iGOT + 20+ NSSTA (large ambition)  
**After:** 20-30 iGOT + 10-15 NSSTA (high-quality proof of concept)

**Strategy:** Get engine working first, expand data volume after verification.

---

### ✅ Verified Reuse of Existing Collections
**Checked:** Do learning_resources, learning_resource_mappings, user_learning_history already exist?

**Answer:** No. These are genuinely new collections needed for recommendation engine.

**Decision:** CREATE NEW (not duplicating anything).

---

### ✅ Provider Abstraction KEPT
```
Recommendation Engine
        ↓
LearningResourceProvider (abstract)
    ↙              ↘
PrototypeIGOT    PrototypeNSSTA  (Round 1)
    ↓              ↓
 Database       Database

Future (Phase 4):
LiveIGOT       LiveNSSTA        (Call real APIs)
```

Engine doesn't depend on HTTP/API implementation details. Easy to swap providers.

---

### ✅ Deterministic Ranking
Same input → Same output (always).

No randomness, no LLM selection, no synthetic data.

**Test:** Same user, called 3 times → identical recommendations.

---

### ✅ Multi-Gap Support
For users with 2, 3, 4+ skill gaps:

1. Find candidates for each gap
2. Score each candidate against its gap
3. Deduplicate (keep highest score if resource appears in multiple gaps)
4. Rank all by score
5. Return top N (e.g., top 5 recommendations covering multiple gaps)

**Example:** Statistical Officer gets 3 recommendations for 3 different gaps.

---

### ✅ Deterministic Explanation
Every recommendation includes:
```
{
  resource: {title, provider, difficulty, duration}
  gap_addressed: {competency, current, required, gap}
  score: {
    overall: 0.86,
    components: {
      competency_match: 0.85,
      gap_priority: 0.75,
      role_match: 1.0,
      difficulty_match: 0.8,
      prerequisite_match: 1.0
    }
  },
  explanation: {
    summary: "...",
    matching_factors: [...],
    next_steps: [...]
  }
}
```

Explanation uses scoring components, not LLM-generated.

---

### ✅ API Endpoints

```
GET /api/v1/recommendations/me
  → Personalized recommendations for current user

GET /api/v1/learning-resources?competency=TECH_SQL&difficulty=BEGINNER
  → Browse resources

GET /api/v1/learning-resources/{resource_id}
  → Resource details

All endpoints:
  - Require JWT authentication
  - Validate user ownership
  - Return deterministic results
```

---

## WHAT PHASE 3 DELIVERS

### End of Week 1: Foundation ✅
- 3 new collections with indexes
- 8-15 seed resources (iGOT + NSSTA)
- Repository CRUD functions
- All data verified, no invented fields

**Baseline:** Still 139 tests passing

---

### End of Week 2: Engine & API ✅
- Provider abstraction (IGOT + NSSTA)
- Recommendation engine (5-component scoring)
- 3 API endpoints
- Multi-gap support
- Deduplication logic

**New Tests:** 15+

---

### End of Week 3: Verification ✅
- 159+ total tests (139 existing + 20 new)
- Example recommendations for Statistical Officer
- Scoring breakdown explained
- Determinism verified
- No regressions

**Final State:** Ready for Phase 4 (live APIs, semantic search).

---

## KEY NUMBERS

| Metric | Value |
|--------|-------|
| Scoring components | 5 (no engagement) |
| Configurable weights | Yes |
| Prototype resources (initial) | 20-30 iGOT + 10-15 NSSTA |
| New collections | 3 |
| New API endpoints | 3 |
| New tests | 20+ |
| Total tests after Phase 3 | 159+ |
| Breaking changes | 0 |
| Invented metadata fields | 0 |

---

## WHAT'S NOT IN PHASE 3

❌ Live iGOT API (Phase 4)  
❌ Live NSSTA API (Phase 4)  
❌ Semantic/LLM search (Phase 3.5)  
❌ Learning paths (Phase 4)  
❌ A/B testing (Phase 4)  
❌ Frontend UI (After backend complete)  
❌ Engagement metrics (Wait for real data)  

---

## SUCCESS CRITERIA

By end of Week 3:

- [ ] **159+ tests passing** (139 existing + 20 new)
- [ ] **Recommendations generated** for Statistical Officer example
- [ ] **Deterministic ranking** verified (same input = same output)
- [ ] **Multi-gap support** working (2+ gaps handled)
- [ ] **Unknown data handled** gracefully (no invented fields)
- [ ] **Provider abstraction** ready for live APIs
- [ ] **All 139 existing tests passing** (no regressions)
- [ ] **Code documented** + decisions explained

---

## DECISION POINTS FOR YOU

1. **Approve the 5-component scoring formula?** ✅ (Ready to implement)

2. **Approve small prototype dataset approach** (20-30 iGOT + 10-15 NSSTA)? ✅

3. **Ready to start Week 1** (collections + indexes + seed data)? 

---

## READY TO BEGIN

All architecture decisions finalized:
- ✅ Data models defined (no invented fields)
- ✅ Scoring formula set (5 components, configurable)
- ✅ Provider pattern approved (abstraction ready)
- ✅ API design approved
- ✅ Testing strategy defined
- ✅ Implementation order specified

**Next Step:** Approve to start Week 1 implementation.

