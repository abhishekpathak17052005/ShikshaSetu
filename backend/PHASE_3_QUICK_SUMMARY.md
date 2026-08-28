# PHASE 3: QUICK SUMMARY

## What We Have ✅

```
Users → Roles → Role Requirements (competency + level)
         ↓
Competency Profiles (current level)
         ↓
Skill Gap Engine (calculates gap, priority, categories)
         ↓
Learning Materials (documents, quizzes, chunks)
```

All existing: **139/139 tests passing. No changes needed.**

---

## What's Missing ❌

```
Skill Gap → ??? → Learning Resources
              ???
              
- No formal learning_resources collection (only generic materials)
- No competency-to-resource mapping
- No iGOT/NSSTA data (no models, no integration)
- No recommendation engine
- No resource ranking/scoring
- No user learning history tracking
```

---

## What Phase 3 Adds ✅

### 1. Three New Collections

**learning_resources**
- iGOT courses + NSSTA programmes
- Metadata: title, difficulty, duration, target_roles, prerequisites
- Competency linkage: which competencies it covers
- Provenance: source URL, verification status

**learning_resource_mappings**
- Explicit competency → resource link
- Quality scores: content_alignment (0-1), accuracy_score (0-1)
- Ranking factors (populated at recommendation time)

**user_learning_history**
- Who took what resource
- Completion status, time spent, rating
- Links to competency evidence (coming later)

### 2. Recommendation Engine

**Input:** Skill gaps (already sorted by priority)

**Output:** Ranked resources with explanations

**Formula:** 6-component scoring
```
Score = (competency_match × 0.35) +
        (gap_priority × 0.25) +
        (difficulty_match × 0.15) +
        (role_match × 0.15) +
        (prerequisite_coverage × 0.05) +
        (engagement_quality × 0.05)
```

**Result:** 0.0-1.0 score (higher = better recommendation)

### 3. Provider Architecture

**PrototypeIGOTProvider** → Query learning_resources (provider="IGOT")  
**PrototypeNSSTAProvider** → Query learning_resources (provider="NSSTA")

Later: Replace with live APIs.

### 4. API Endpoints

```
GET /api/v1/recommendations/me
    → Personalized recommendations for current user

GET /api/v1/learning-resources?competency={code}&difficulty={BEGINNER}
    → Browse all resources

GET /api/v1/learning-resources/{resource_id}
    → Resource details

POST /api/v1/learning-resources/{resource_id}/rate
    → Rate resource after using
```

---

## Data Flow Example

```
User: Statistical Officer (demo-statistical-officer@...)

1. GET /skill-gaps
   ↓
   [
     {competency: STAT_SAMPLING, gap: 1.45, priority_score: 0.75},
     {competency: TECH_SQL, gap: 1.70, priority_score: 0.70}
   ]

2. GET /recommendations/me
   ↓
   [
     {
       rank: 1,
       resource: "SQL Fundamentals (IGOT)",
       gap_addressed: TECH_SQL,
       score: 0.860,
       explanation: "Resource covers SQL at BEGINNER level, appropriate for your current skill (1.8/5)"
     },
     {
       rank: 2,
       resource: "Statistical Sampling Methods (NSSTA TPAC)",
       gap_addressed: STAT_SAMPLING,
       score: 0.845,
       explanation: "Official training programme for Statistical Officer role"
     }
   ]

3. POST /learning-resources/{resource_id}/rate
   ↓
   {rating: 5, feedback: "Great course"}
   
4. Competency updated based on completion → Skill gap reduced ✓
```

---

## Prototype Data Strategy

**Round 1 (Phase 3):**
- Manually curate 50+ iGOT courses (from igot.gov.in public catalog)
- Manually curate 20+ NSSTA programmes (from MoSPI official publications)
- Map to ShikshaSetu competency framework
- Store full provenance: source_url, source_document, last_verified_at

**Honesty:**
- ✅ Recommend resources
- ✅ Map to competencies
- ❌ Don't claim live enrollment (no actual API)
- ❌ Don't show fake seat availability
- ✅ Mark as "PROTOTYPE" in metadata

**Round 2 (Phase 4+):**
- Replace PrototypeIGOTProvider with LiveIGOTProvider (call real API)
- Replace PrototypeNSSTAProvider with LiveNSSTAProvider (call real API)
- No data model changes needed (same learning_resources schema)

---

## Test Plan

### Unit Tests
- Scoring formula: verify 6 components calculate correctly
- Provider: mock search_by_competency returns filtered results
- Engine: verify candidate generation and ranking

### Integration Tests
- User → Skill Gap → Recommendation flow
- iGOT and NSSTA resources searchable by competency
- Resources ranked consistently (same input = same output)

### E2E Tests
- GET /recommendations/me for demo user
- Verify explanations are generated
- Verify no breaking changes to existing 139 tests

**Target:** 150+ total tests (139 existing + 11 new)

---

## Timeline

**Week 1:** Collections + schemas + indexes + seeding (foundation)  
**Week 2:** Providers + recommendation engine + API endpoints  
**Week 3:** Tests + verification + documentation

**Not in Phase 3:**
- ❌ Live iGOT/NSSTA APIs (Phase 4)
- ❌ Semantic/LLM search (Phase 3.5)
- ❌ Learning paths (Phase 4)
- ❌ A/B testing recommendations (Phase 4)

---

## Key Differences from Phase 1-2

| Aspect | Phase 1-2 | Phase 3 |
|--------|-----------|---------|
| **Purpose** | Assess current competency | Find learning to close gaps |
| **Evidence Type** | SELF_ASSESSMENT, KNOWLEDGE_TEST, SCENARIO_TEST | (same - evidence feeds skill gaps) |
| **Query Pattern** | User → Competency → Gap | User → Gap → Resource → Recommendation |
| **Collections** | competency_profiles, evidence, assessments | learning_resources, resource_mappings, history |
| **Scoring** | Binary (MCQ/SCENARIO) | 6-component ranking |
| **Testing** | Deterministic scoring + aggregation | Search + ranking determinism |

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| iGOT/NSSTA data becomes stale | Provenance tracking; verification_status; quarterly review |
| Live API integration breaks prototype | Use provider abstraction; prototype != live |
| Recommendation weights wrong | Start conservative; data collection Phase 4 for tuning |
| Semantic search needed sooner | Add Phase 3.5; non-blocking (structured search works) |
| Performance with large resource DB | Indexes on competency_code; pagination; filtering |

---

## Success Criteria

✅ 150+ tests passing (139 + Phase 3 tests)  
✅ Recommendations generated for demo users  
✅ All scoring components auditable  
✅ iGOT + NSSTA data properly sourced  
✅ Provider pattern extensible  
✅ No breaking changes  

---

## Ready for Review

1. **Architecture:** Collection schemas + relationships
2. **Algorithm:** 6-component scoring formula
3. **Data:** iGOT + NSSTA seeding strategy
4. **API:** Endpoint design
5. **Timeline:** 3-week implementation

**User Approval Needed:**
- [ ] Proceed with Phase 3 foundation
- [ ] Recommend weights for scoring formula
- [ ] Approve prototype data approach (manual curation)

