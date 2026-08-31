# Phase 1D: E2E Closed-Loop Testing

## Objective
Build a **real E2E test** proving the complete ShikshaSetu product loop in one integrated test, validating that:
1. Assessment creates evidence and calculates competency
2. Skill gap is identified from competency gap
3. Personalized recommendation is created for that gap
4. User starts learning activity from recommendation
5. Learning completion creates supporting evidence (confidence 0.3)
6. Competency level does NOT change from learning alone
7. Taking assessment creates authoritative evidence (confidence 0.8)
8. Competency level updates from assessment
9. Skill gap decreases after assessment

## Test Scenario

### Setup
- User: Ananya Mehta (existing test user)
- Competency: Python (PA01)
- Initial competency: 2.5/5.0
- Role requirement: 4.0/5.0
- Initial gap: 1.5

### Expected Flow

```
1. TAKE INITIAL ASSESSMENT
   ├─ Assessment created (if needed)
   ├─ Questions answered
   ├─ Score: 70%
   └─ Evidence created (confidence 0.8)

2. CHECK COMPETENCY UPDATE
   ├─ Competency should reflect new assessment score
   ├─ Expected: ~3.2/5.0
   └─ Gap reduced to ~0.8

3. FETCH RECOMMENDATIONS
   ├─ API call to GET /learning-resources/recommendations
   ├─ Should return Python-focused resources
   └─ Match score should be high

4. START LEARNING ACTIVITY
   ├─ POST /learning-activities
   ├─ resource_id: python-course
   ├─ competency_id: PA01
   └─ status: not_started

5. TRACK PROGRESS
   ├─ PUT /learning-activities/{id}
   ├─ progress_percent: 100
   ├─ Test updating multiple times
   └─ Verify not_started → in_progress → completed

6. COMPLETE LEARNING ACTIVITY
   ├─ POST /learning-activities/{id}/complete
   ├─ Supporting evidence should be created
   ├─ Evidence type: LEARNING_ACTIVITY
   ├─ Confidence: 0.3
   ├─ **CRITICAL**: Competency should NOT change
   └─ Skill gap should remain at ~0.8

7. VERIFY EVIDENCE PAGE
   ├─ Fetch completed learning activities
   ├─ Show in Evidence component
   ├─ Display confidence 0.3
   └─ Guide to assessment

8. TAKE ASSESSMENT QUIZ
   ├─ Assessment of learned material
   ├─ Score: 85%
   ├─ Evidence type: CAPABILITY_ASSESSMENT
   ├─ Confidence: 0.8
   └─ **CRITICAL**: This should update competency

9. VERIFY FINAL STATE
   ├─ Competency moved to ~3.5/5.0
   ├─ Skill gap reduced to ~0.5
   ├─ Evidence shows both learning (0.3) and assessment (0.8)
   ├─ Learning evidence only (no competency change)
   └─ Assessment evidence (competency updated)
```

## Test Implementation

### Backend Tests
**File**: `backend/tests/test_e2e_closed_loop.py`

```python
class TestE2EClosedLoop:
    """E2E test proving the complete learning-to-competency loop"""
    
    async def test_complete_learning_loop(self):
        """
        Test flow:
        1. Take initial assessment
        2. Get recommendations
        3. Start learning activity
        4. Complete learning (no competency change)
        5. Take assessment quiz
        6. Verify competency updated
        7. Verify gap reduced
        """
        
    async def test_learning_evidence_does_not_inflate_competency(self):
        """Verify that learning completion does NOT update competency"""
        
    async def test_assessment_evidence_updates_competency(self):
        """Verify that assessments DO update competency levels"""
        
    async def test_skill_gap_recalculation_after_learning(self):
        """Verify gap remains same after learning, decreases after assessment"""
        
    async def test_evidence_confidence_levels(self):
        """Verify learning evidence has confidence 0.3, assessment has 0.8"""
```

### Frontend Integration Tests
**File**: `frontend/client/src/__tests__/e2e-closed-loop.test.ts`

```typescript
describe('E2E: Closed Loop Learning Journey', () => {
  it('should complete full journey: assess → gap → learn → evidence → assess → update', async () => {
    // 1. User takes assessment
    // 2. Verify competency updated
    // 3. Verify gap identified
    // 4. Get recommendations
    // 5. Start learning activity
    // 6. Complete learning
    // 7. Verify evidence created (confidence 0.3)
    // 8. Verify competency NOT changed
    // 9. Take assessment quiz
    // 10. Verify competency updated (confidence 0.8)
    // 11. Verify gap decreased
  });
});
```

## Success Criteria

### Must Have
- ✅ Learning completion creates evidence (confidence 0.3)
- ✅ Learning completion does NOT update competency
- ✅ Assessment completion creates evidence (confidence 0.8)
- ✅ Assessment completion DOES update competency
- ✅ Skill gap decreases after assessment
- ✅ Skill gap unchanged after learning
- ✅ Full journey completes without errors

### Nice to Have
- ✅ Metrics: time from learning start to completion
- ✅ Metrics: time from assessment to competency update
- ✅ Evidence chain visible in Evidence page
- ✅ Learning activity linked to competency

## API Endpoints Involved

### Assessments
- `POST /assessments` - Create assessment
- `POST /assessments/{id}/submit` - Submit assessment answers
- `GET /assessments/{id}/results` - Get assessment results

### Learning Activities
- `POST /learning-activities` - Start activity
- `PUT /learning-activities/{id}` - Update progress
- `POST /learning-activities/{id}/complete` - Mark complete

### Recommendations
- `GET /learning-resources/recommendations` - Get recommendations
- `GET /learning-resources/recommendations?competency_id=PA01` - By competency

### Evidence
- `GET /competency-evidence` - Get all evidence
- `GET /competency-evidence?competency_id=PA01` - Get by competency

### Competency
- `GET /competencies/profile` - Get profile before/after
- `GET /skill-gaps` - Get gaps before/after

## Implementation Checklist

- [ ] Create `test_e2e_closed_loop.py` in backend/tests
- [ ] Create E2E integration test in frontend
- [ ] Mock or setup real test user (Ananya Mehta)
- [ ] Define assertions for each step
- [ ] Run test locally against backend
- [ ] Run test in CI/CD pipeline
- [ ] Document any issues found
- [ ] Add to regression test suite

## Key Assertions

```python
# Before learning
assert initial_competency == 2.5
assert initial_gap == 1.5

# After learning completion
assert competency_after_learning == 2.5  # NO CHANGE
assert gap_after_learning == 1.5  # NO CHANGE
assert learning_evidence_confidence == 0.3

# After assessment
assert competency_after_assessment == 3.5  # UPDATED
assert gap_after_assessment < initial_gap  # REDUCED
assert assessment_evidence_confidence == 0.8
```

## Timeline
- Design: Day 1 ✅ (completed)
- Backend Test: Day 1-2
- Frontend Test: Day 2-3
- Full Integration: Day 3
- Validation: Day 4

---

**Goal**: Make the complete product loop **visible, testable, and real**.
