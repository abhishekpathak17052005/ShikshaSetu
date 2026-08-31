# Phase 1D: Closed-Loop E2E Verification

**Objective**: Prove the complete learning loop works end-to-end with correct competency semantics.

## Test Scenario

User journey that demonstrates ShikshaSetu's original vision:

```
┌─────────────────────────────────────────────────────────────┐
│ Complete Learning Loop: Gap → Recommend → Learn → Assess   │
└─────────────────────────────────────────────────────────────┘

1. INITIAL STATE
   User: Test Employee
   Role: Statistical Officer
   Competency: PA01 (Planning & Analysis)
   Current Level: 2.0
   Required Level: 4.0
   Gap: 2.0 levels ✗ CRITICAL

2. GET RECOMMENDATION
   GET /api/v1/skill-gaps
   → Gap in PA01 (priority: critical)
   
   GET /api/v1/learning-resources/recommendations
   → Recommended: "Advanced Statistical Planning" (igot_course_123)

3. START LEARNING
   POST /api/v1/learning-activities
   {
     "resource_id": "igot_course_123",
     "competency_id": "PA01"
   }
   → Activity created (status: in_progress)
   → Competency: PA01 still 2.0 (unchanged) ✓

4. TRACK PROGRESS
   PUT /api/v1/learning-activities/{activity_id}
   {
     "progress_percent": 50,
     "duration_minutes": 45
   }
   → Activity updated (progress: 50%)
   → Competency: PA01 still 2.0 (unchanged) ✓

   PUT /api/v1/learning-activities/{activity_id}
   {
     "progress_percent": 100,
     "duration_minutes": 120
   }
   → Activity complete (100%)
   → Competency: PA01 still 2.0 (unchanged) ✓

5. COMPLETE LEARNING
   POST /api/v1/learning-activities/{activity_id}/complete
   {
     "final_score": 95,
     "notes": "Completed all modules successfully"
   }
   
   Response:
   {
     "activity": {
       "status": "completed",
       "progress_percent": 100
     },
     "evidence_created": true,
     "evidence_type": "LEARNING_ACTIVITY",
     "evidence_confidence": 0.3,
     "note": "Learning completion recorded as supporting evidence...",
     "current_competency_level": 2.0,    ← UNCHANGED ✓
     "current_skill_gap": 2.0,            ← UNCHANGED ✓
     "next_step": "Complete an assessment or capability quiz..."
   }
   
   → Evidence recorded (type: LEARNING_ACTIVITY, confidence: 0.3)
   → Competency: PA01 still 2.0 (unchanged) ✓
   → Gap: still 2.0 (unchanged) ✓

6. VERIFY LEARNING EVIDENCE CREATED
   GET /api/v1/competency-evidence?competency_id=PA01&user_id=...
   → Evidence entry found:
     - type: "LEARNING_ACTIVITY"
     - confidence: 0.3
     - score: 95
     - source.resource_id: "igot_course_123"
   ✓

7. TAKE CAPABILITY ASSESSMENT
   POST /api/v1/capability-assessments
   {
     "competency_id": "PA01"
   }
   → Assessment created (10 questions)
   
   POST /api/v1/capability-assessments/{assessment_id}/submit
   {
     "answers": {...}  // 80% correct (8/10)
   }
   
   Response:
   {
     "score": 80,
     "evidence_id": "...",
     "competency_updated": true,
     "gap_recalculated": true
   }

8. VERIFY COMPETENCY UPDATED
   GET /api/v1/competencies/profiles/PA01
   {
     "competency_id": "PA01",
     "current_level": 3.2,           ← UPDATED from 2.0 ✓
     "confidence": 0.8,              ← From assessment
     "last_evidence_type": "CAPABILITY_ASSESSMENT",
     "evidence_count": 2
   }
   
   → Competency increased by 1.2 levels (80% assessment score)
   → Confidence now 0.8 (assessment evidence is authoritative)

9. VERIFY GAP RECALCULATED
   GET /api/v1/skill-gaps
   {
     "competency_id": "PA01",
     "current_level": 3.2,
     "required_level": 4.0,
     "gap": 0.8,                    ← IMPROVED from 2.0 ✓
     "priority": "high"             ← Changed from "critical"
   }

10. VERIFY UPDATED RECOMMENDATION
    GET /api/v1/learning-resources/recommendations
    {
      "competencies": [
        {
          "competency_id": "PA01",
          "gap": 0.8,
          "priority": "high",
          "resources": [
            {
              "id": "igot_course_456",
              "title": "Advanced Statistical Planning (Level 4)",
              "provider": "IGOT",
              "difficulty": "high"
            }
          ]
        }
      ]
    }
    → New recommendation for remaining 0.8 levels ✓

11. VERIFY EVIDENCE CHAIN
    GET /api/v1/competency-evidence?competency_id=PA01
    [
      {
        "type": "LEARNING_ACTIVITY",
        "confidence": 0.3,
        "score": 95,
        "recorded_at": "2025-01-15T12:00:00Z"
      },
      {
        "type": "CAPABILITY_ASSESSMENT",
        "confidence": 0.8,
        "score": 80,
        "recorded_at": "2025-01-15T14:00:00Z"
      }
    ]
    → Full evidence trail shows:
      - Learning → Supporting evidence (0.3)
      - Assessment → Authoritative evidence (0.8)
      - Competency updated by assessment only ✓
```

## Test Implementation

### Backend E2E Test
**File**: `backend/tests/test_closed_loop_e2e.py`

```python
def test_complete_learning_loop():
    """
    E2E test verifying:
    1. Gap exists (user below required level)
    2. Recommendation generated
    3. Learning activity started
    4. Learning completed (competency UNCHANGED)
    5. Supporting evidence recorded
    6. Assessment completed
    7. Competency updated (from assessment evidence)
    8. Gap reduced
    9. New recommendation generated
    """
    # Setup: Create user, competency profile
    user = create_test_user()
    set_competency_level(user_id=user["_id"], competency_id="PA01", level=2.0)
    
    # Step 1-2: Verify gap and get recommendation
    gaps = get_skill_gaps(user["_id"])
    assert gaps[0]["competency_id"] == "PA01"
    assert gaps[0]["gap"] == 2.0
    
    # Step 3: Start learning
    activity = start_learning_activity(
        user_id=user["_id"],
        resource_id="igot_course_123",
        competency_id="PA01"
    )
    assert activity["status"] == "in_progress"
    
    # Verify competency unchanged
    profile = get_competency_profile(user["_id"], "PA01")
    assert profile["current_level"] == 2.0
    
    # Step 4-5: Complete learning
    result = complete_learning_activity(
        user_id=user["_id"],
        activity_id=activity["activity_id"],
        final_score=95
    )
    
    # CRITICAL: Verify competency NOT changed by learning
    assert result["current_competency_level"] == 2.0
    assert result["current_skill_gap"] == 2.0
    
    # Verify evidence created (supporting only)
    evidence = get_evidence(user["_id"], "PA01")
    learning_evidence = [e for e in evidence if e["type"] == "LEARNING_ACTIVITY"]
    assert len(learning_evidence) > 0
    assert learning_evidence[0]["confidence"] == 0.3
    
    # Step 6-7: Take assessment
    assessment = create_capability_assessment(
        user_id=user["_id"],
        competency_id="PA01"
    )
    
    # Submit with 80% score
    submit_assessment(
        user_id=user["_id"],
        assessment_id=assessment["assessment_id"],
        answers=[correct answers for 8/10]
    )
    
    # Step 8: Verify competency UPDATED by assessment
    profile = get_competency_profile(user["_id"], "PA01")
    assert profile["current_level"] > 2.0  # Increased
    assert profile["current_level"] <= 4.0  # Bounded by max
    assert profile["confidence"] == 0.8     # Assessment confidence
    
    # Step 9: Verify gap recalculated
    gaps = get_skill_gaps(user["_id"])
    pa01_gap = next(g for g in gaps if g["competency_id"] == "PA01")
    assert pa01_gap["gap"] < 2.0  # Improved
    
    # Step 10: Verify updated recommendation
    recommendations = get_learning_resources_recommendations(user["_id"])
    pa01_rec = next(r for r in recommendations if r["competency_id"] == "PA01")
    assert len(pa01_rec["resources"]) > 0
    
    # Step 11: Verify evidence chain
    all_evidence = get_evidence(user["_id"], "PA01")
    assert any(e["type"] == "LEARNING_ACTIVITY" for e in all_evidence)
    assert any(e["type"] == "CAPABILITY_ASSESSMENT" for e in all_evidence)
```

### Test Assertions (Key Validation)

```python
# LEARNING COMPLETION MUST NOT CHANGE COMPETENCY
assert competency_before == competency_after

# LEARNING EVIDENCE MUST HAVE LOW CONFIDENCE
assert learning_evidence["confidence"] == 0.3

# ASSESSMENT EVIDENCE MUST HAVE HIGH CONFIDENCE
assert assessment_evidence["confidence"] == 0.8

# GAP MUST IMPROVE AFTER ASSESSMENT
assert gap_after < gap_before

# EVIDENCE TRAIL MUST SHOW BOTH TYPES
assert "LEARNING_ACTIVITY" in evidence_types
assert "CAPABILITY_ASSESSMENT" in evidence_types

# ONLY ASSESSMENT UPDATES COMPETENCY
assert competency_updated_by == "CAPABILITY_ASSESSMENT"
```

## Files to Create

**Create**:
- `backend/tests/test_closed_loop_e2e.py` (400 lines)
  - test_complete_learning_loop()
  - test_learning_evidence_does_not_update_competency()
  - test_assessment_evidence_updates_competency()
  - test_gap_recalculation_after_assessment()
  - test_recommendation_updates_after_competency()
  - test_evidence_chain_recorded()

## Success Criteria

✅ Learning completion does NOT update competency
✅ Learning evidence recorded with confidence 0.3
✅ Assessment evidence recorded with confidence 0.8
✅ Only assessment evidence updates competency levels
✅ Gap recalculated correctly after assessment
✅ New recommendations generated based on reduced gap
✅ Full evidence trail preserved
✅ All existing tests continue to pass
✅ New E2E tests added (6+ tests)

## Why This Matters for SIH

**Before Phase 1D**: "The platform creates learning activities" ✓
**After Phase 1D**: "The platform correctly implements a closed learning loop where learning is supporting evidence, not fake competency inflation" ✓

This distinction is what makes ShikshaSetu defensible to evaluation committee.
