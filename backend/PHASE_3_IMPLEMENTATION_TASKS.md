# PHASE 3: IMPLEMENTATION TASK LIST

**Status:** Ready to implement  
**Baseline:** 139/139 tests passing  
**Target:** 159+ tests passing (139 existing + 20 new)  
**Timeline:** 3 weeks  

---

## WEEK 1: FOUNDATION

### Day 1-2: Collections & Indexes

**Tasks:**
- [ ] Create `learning_resources` collection schema (Pydantic model)
- [ ] Create `learning_resource_mappings` collection schema
- [ ] Create `user_learning_history` collection schema
- [ ] Add all three to `app/core/framework_indexes.py` with proper indexes:
  - `learning_resources`: (provider, status), (competencies.competency_code)
  - `learning_resource_mappings`: (resource_id, competency_id), (competency_code)
  - `user_learning_history`: (user_id, resource_id), (interaction_type)

**Files to Create:**
- `app/learning_resources/__init__.py`
- `app/learning_resources/models.py` (Pydantic schemas only)

**No Data Yet** - Just schema validation.

---

### Day 3-4: Repository Layer

**Tasks:**
- [ ] Create repository functions:
  - `insert_learning_resource(resource_doc)` → ObjectId
  - `get_learning_resource(resource_id)` → dict | None
  - `find_resources_by_competency(competency_code, limit=10)` → List[dict]
  - `find_resources_by_provider(provider, limit=10)` → List[dict]
  - `create_mapping(resource_id, competency_id, quality_scores)` → ObjectId
  - `get_mapping(resource_id, competency_id)` → dict | None
  - `record_user_history(user_id, resource_id, interaction_type)` → ObjectId

**File to Create:**
- `app/learning_resources/repository.py`

**No Logic** - Just database operations.

---

### Day 5: Seed Small Prototype Data

**Tasks:**
- [ ] Research and manually enter 5 iGOT courses
  - SQL Fundamentals → TECH_SQL
  - Python Basics → TECH_PYTHON
  - (3 more covering demo competencies)
  
- [ ] Research and manually enter 3 NSSTA programmes
  - Statistical Sampling Methods → STAT_SAMPLING
  - (2 more covering demo competencies)

- [ ] For each resource, create mapping entries with verified quality scores:
  - content_alignment: 0.8-0.95 (only if verified)
  - accuracy_score: 0.9-1.0 (only if verified)

**No Automation** - Manual, verified entries only.

**Test:** Verify 8 resources queryable by competency_code.

---

### Week 1 Verification

```bash
# Test collections created
pytest tests/test_learning_resources_models.py -v

# Test repository CRUD
pytest tests/test_learning_resources_repository.py -v

# Verify 139 existing tests still pass
pytest tests/ -v --ignore=tests/test_learning_resources* -x
```

**Exit Criteria:**
- ✅ 8 resources seedable and queryable
- ✅ 139 tests still passing
- ✅ No schema validation errors

---

## WEEK 2: ENGINE & API

### Day 1: Provider Abstraction

**Tasks:**
- [ ] Create `LearningResourceProvider` abstract base class
  - `search_by_competency(competency_code, filters)` → List[dict]
  - `get_resource_details(resource_id)` → dict | None
  - `check_availability(resource_id)` → dict

- [ ] Implement `PrototypeIGOTProvider`
  - Query `learning_resources` (provider="IGOT")
  - Return results with no fake availability data

- [ ] Implement `PrototypeNSSTAProvider`
  - Query `learning_resources` (provider="NSSTA")
  - Return results with no fake availability data

- [ ] Create `ProviderFactory`
  - `get_provider(provider_name, database, mode="prototype")` → Provider

**Files to Create:**
- `app/learning_resources/providers/__init__.py`
- `app/learning_resources/providers/base.py` (abstract class)
- `app/learning_resources/providers/igot_provider.py`
- `app/learning_resources/providers/nssta_provider.py`
- `app/learning_resources/providers/factory.py`

**Tests:**
- [ ] `test_igot_provider_search_by_competency()`
- [ ] `test_nssta_provider_search_by_competency()`
- [ ] `test_provider_factory_get_provider()`

---

### Day 2: Recommendation Engine Core

**Tasks:**
- [ ] Create `RecommendationEngine` class with:
  - `generate_recommendations(request)` → List[RecommendationItem]
  - `_find_candidates_for_gap(gap, providers, limit)` → List[dict]
  - `_score_candidate(candidate, gap, user_profiles)` → float

- [ ] Implement 5-component scoring:
  - `_calculate_competency_match(candidate, competency_code)` → float
  - `_calculate_gap_priority(gap)` → float (reuse gap.priority_score)
  - `_calculate_role_match(candidate, gap)` → float
  - `_calculate_difficulty_match(candidate, current_level)` → float
  - `_calculate_prerequisite_match(candidate, user_profiles)` → float

- [ ] Implement deduplication logic (same resource across gaps)

- [ ] Implement multi-gap support

**Files to Create:**
- `app/recommendations/__init__.py`
- `app/recommendations/engine.py`
- `app/recommendations/schemas.py` (RecommendationRequest, RecommendationResponse, etc.)

**Tests:**
- [ ] `test_competency_match_scoring()`
- [ ] `test_gap_priority_scoring()`
- [ ] `test_role_match_scoring()`
- [ ] `test_difficulty_match_scoring()`
- [ ] `test_prerequisite_match_scoring()`
- [ ] `test_combined_score_calculation()`
- [ ] `test_recommendation_determinism()`
- [ ] `test_multi_gap_deduplication()`

---

### Day 3-4: API Endpoints

**Tasks:**
- [ ] Create `recommendations/router.py` with:
  - `GET /api/v1/recommendations/me` → RecommendationResponse
  - `GET /api/v1/learning-resources` → Paginated list
  - `GET /api/v1/learning-resources/{resource_id}` → Full resource details

- [ ] Add JWT authentication + user ownership validation
- [ ] Add error handling (404, 422, 503)
- [ ] Register router in `app/main.py`

**Files to Modify:**
- `app/recommendations/router.py` (new)
- `app/main.py` (add router registration)

**Tests:**
- [ ] `test_recommendations_endpoint_me()`
- [ ] `test_learning_resources_list_endpoint()`
- [ ] `test_learning_resources_detail_endpoint()`
- [ ] `test_unauthorized_access()`

---

### Day 5: E2E Integration

**Tasks:**
- [ ] Test full flow: User → Skill Gaps → Recommendations
- [ ] Test with demo user (Statistical Officer)
- [ ] Verify explanations are generated
- [ ] Verify deterministic ranking

**Tests:**
- [ ] `test_e2e_statistical_officer_recommendations()`
- [ ] `test_e2e_multiple_gaps()`
- [ ] `test_e2e_no_gaps()`

---

### Week 2 Verification

```bash
# Test recommendation engine
pytest tests/test_recommendations_engine.py -v

# Test API endpoints
pytest tests/test_recommendations_api.py -v

# Test providers
pytest tests/test_provider_factory.py -v

# Verify 139 existing tests still pass
pytest tests/ -v --ignore=tests/test_recommendations* --ignore=tests/test_learning_resources* -x
```

**Exit Criteria:**
- ✅ 15+ new tests passing
- ✅ Recommendations generated for demo users
- ✅ Deterministic ranking verified
- ✅ 139 existing tests still passing

---

## WEEK 3: TESTING & VERIFICATION

### Day 1-2: Comprehensive Testing

**Tasks:**
- [ ] Write comprehensive test suite:
  - Single gap recommendation
  - Multiple gaps (2, 3, 4+)
  - No gap user
  - Competency match scoring
  - Role matching
  - Difficulty matching
  - Prerequisite checking
  - Unknown metadata handling
  - iGOT provider search
  - NSSTA provider search
  - Provider fallback (one fails)
  - Deduplication
  - Empty resource database
  - Cross-user access prevention

- [ ] Run full test suite
- [ ] Verify all 139 existing tests still pass
- [ ] Document any failures + fixes

**Target:** 159+ tests passing (139 + 20 new)

---

### Day 3: Expand Prototype Data (Optional)

**Tasks:**
- [ ] Add 5-10 more iGOT resources (optional, if time allows)
- [ ] Add 2-5 more NSSTA resources (optional, if time allows)
- [ ] Verify all new resources queryable and rankable

**Note:** Don't block verification on this. Core engine is more important than data volume.

---

### Day 4-5: Final Verification & Documentation

**Tasks:**
- [ ] Create example recommendations for:
  - Statistical Officer (demo user)
  - Data Analyst (another role)
  
- [ ] For each example, show:
  - Input: Current competency profile + skill gaps
  - Processing: Candidate search + scoring breakdown
  - Output: Ranked recommendations with explanations

- [ ] Document:
  - Scoring formula (5 components + weights)
  - Implementation decisions
  - What's working + what's deferred
  - Next phase recommendations

- [ ] Create final verification report

---

### Week 3 Verification

```bash
# Run ALL tests
pytest tests/ -v

# Verify output
# - 159+ tests passing
# - No existing test regressions
# - Recommendations generated + explained

# Document decisions
# - Why these 5 components?
# - Why these weights?
# - What happens if data is missing?
```

**Exit Criteria:**
- ✅ 159+ tests passing
- ✅ Example recommendations working
- ✅ All scoring components auditable
- ✅ Multi-gap support verified
- ✅ Unknown metadata handled gracefully
- ✅ No breaking changes to 139 existing tests
- ✅ Implementation documented

---

## DELIVERABLES (END OF PHASE 3)

### Code

```
app/learning_resources/
  ├── __init__.py
  ├── models.py          (schemas)
  ├── repository.py      (CRUD)
  └── providers/
      ├── __init__.py
      ├── base.py        (abstract)
      ├── igot_provider.py
      ├── nssta_provider.py
      └── factory.py

app/recommendations/
  ├── __init__.py
  ├── engine.py          (recommendation logic)
  ├── schemas.py         (request/response)
  └── router.py          (API endpoints)

app/core/
  └── framework_indexes.py  (updated with new indexes)

app/
  └── main.py            (updated with router registration)
```

### Data

- 20-30 iGOT resources (learning_resources collection)
- 10-15 NSSTA resources (learning_resources collection)
- Mappings for all resources (learning_resource_mappings collection)
- All resources verified and no invented data

### Tests

- 20+ new tests in:
  - `tests/test_recommendations_engine.py`
  - `tests/test_recommendations_api.py`
  - `tests/test_provider_factory.py`

### Documentation

- `PHASE_3_FINAL_ARCHITECTURE.md` (this document)
- `PHASE_3_IMPLEMENTATION_TASKS.md` (task list - this file)
- Example recommendations with scoring breakdown
- Final verification report

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Scoring formula not right | Can be tuned later (configurable weights) |
| Not enough prototype data | Start with 8, expand as needed - don't block engine |
| Performance with many resources | Indexes in place, pagination in API |
| Unknown metadata causes problems | Use neutral (0.5) not invented value |
| Live API needed immediately | Provider abstraction ready for Phase 4 |
| LLM explanations needed | Use templates in Phase 3, LLM in Phase 3.5 |

---

## SUCCESS CHECKLIST

At end of Week 3, verify:

- [ ] All 159+ tests passing
- [ ] `GET /recommendations/me` returns ranked recommendations
- [ ] Recommendations have explanation + scoring breakdown
- [ ] Same user, multiple calls = same recommendations (deterministic)
- [ ] User with 3+ gaps gets recommendations for multiple gaps
- [ ] No invented metadata (missing fields = neutral)
- [ ] Provider abstraction extensible (ready for live APIs)
- [ ] All 139 existing tests still passing (no regressions)
- [ ] Code documented + decisions explained
- [ ] Ready for user review

**STOP after verification. Do NOT start frontend or advanced questions.**

---

## NEXT PHASE (Phase 4)

- Live iGOT API integration (if access available)
- Live NSSTA API integration (if access available)
- Semantic search enhancement
- Learning path generation
- A/B testing recommendation weights

