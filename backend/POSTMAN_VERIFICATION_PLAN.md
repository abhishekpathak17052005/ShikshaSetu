# Postman Verification Plan

## Status: Ready to Freeze Backend

**Backend Architecture:** FROZEN ❄️
- No more feature development
- Bug fixes only if discovered during Postman testing
- All changes must be documented

---

## Phase 1: Loop 1 Verification (Skill Intelligence)

### Objective
Prove: Employee Registration → Assessment → Competency Profile → Skill Gap → Recommendation

### Tests (In Order)

#### Test 1: Registration
```
POST /api/v1/auth/register
{
  "email": "testuser@example.com",
  "password": "Test@123",
  "full_name": "Test Employee",
  "role_id": "6a8fe8048524f6da8ebb9881",
  "designation": "Data Analyst",
  "department": "Analytics",
  "employee_id": "EMP001"
}

Expected: 201 Created
Verify: User ID returned
```

#### Test 2: Login
```
POST /api/v1/auth/login
{
  "email": "testuser@example.com",
  "password": "Test@123"
}

Expected: 200 OK
Verify: JWT token in response
Store: Token for subsequent requests
```

#### Test 3: Get Competencies
```
GET /api/v1/competencies
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify: 33 competencies returned
Verify: Each has code, name, domain, definition
```

#### Test 4: Take Assessment
```
POST /api/v1/capability-assessments/competencies/{competency_code}
Headers: Authorization: Bearer {token}
{
  "answers": [
    {"question_id": "q1", "selected_answer": "option_a"},
    {"question_id": "q2", "selected_answer": "option_b"},
    ...
  ]
}

Expected: 200 OK
Verify: Score calculated
Verify: Evidence created
```

#### Test 5: Check Competency Profile Updated
```
GET /api/v1/competencies/me
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify: Updated competency levels reflect assessment
```

#### Test 6: Calculate Skill Gaps
```
GET /api/v1/skill-gaps/me
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify: Gap list returned
Verify: Priority scores calculated
Verify: Gap categories (LOW, MEDIUM, HIGH, CRITICAL)
```

#### Test 7: Get Recommendations
```
GET /api/v1/recommendations/me
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify: Recommendations returned
Verify: Each has:
  - resource_id
  - title
  - provider (IGOT or NSSTA)
  - score (0.0-1.0)
  - explanation with score_breakdown
```

#### Test 8: Verify Score Breakdown
```
Check first recommendation's explanation.score_breakdown

Expected: 5 components
Verify:
  - competency_match: weight=0.4, score=0-1, value=0-0.4
  - gap_priority: weight=0.25, score=0-1, value=0-0.25
  - role_match: weight=0.2, score=0-1, value=0-0.2
  - difficulty_match: weight=0.1, score=0-1, value=0-0.1
  - prerequisite_match: weight=0.05, score=0-1, value=0-0.05
  
Total value = sum of all values ≈ score
```

#### Test 9: Determinism
```
Call GET /api/v1/recommendations/me twice (no changes)

Expected: Identical results
Verify:
  - Same resources in same order
  - Same scores
  - Same explanations
```

#### Test 10: Provider Separation
```
Examine recommendations

Expected:
  - Some recommendations from IGOT
  - Some recommendations from NSSTA
  - Provider field always populated
  - No mixed providers in single resource
```

---

## Phase 2: Loop 2 Verification (Continuous Learning)

### Objective
Prove: Learning Material → MCQs → Quiz → Evidence → Competency Update

### Tests (Sequential)

#### Test 11: Upload Learning Material
```
POST /api/v1/materials/upload
Headers: Authorization: Bearer {token}
Body: multipart/form-data with PDF/DOCX

Expected: 200 OK
Verify: Material ID returned
Verify: Status = "PROCESSING"
```

#### Test 12: Generate MCQs
```
POST /api/v1/ai/generate
Headers: Authorization: Bearer {token}
{
  "material_id": "{material_id}",
  "competency_code": "TECH_PYTHON",
  "num_questions": 5
}

Expected: 200 OK
Verify: 5 MCQs generated
Verify: Each has question, options, correct_answer, difficulty
```

#### Test 13: Create Quiz
```
POST /api/v1/quizzes
Headers: Authorization: Bearer {token}
{
  "material_id": "{material_id}",
  "competency_code": "TECH_PYTHON",
  "questions": [{...generated MCQs...}]
}

Expected: 201 Created
Verify: Quiz ID returned
Verify: Status = "IN_PROGRESS"
```

#### Test 14: Submit Quiz
```
POST /api/v1/quizzes/{quiz_id}/submit
Headers: Authorization: Bearer {token}
{
  "answers": [
    {"question_id": "q1", "selected_answer": "option_a"},
    ...
  ]
}

Expected: 200 OK
Verify:
  - Score calculated
  - Percentage computed
  - Competency level updated
  - Evidence created
```

#### Test 15: Verify Competency Updated
```
GET /api/v1/competencies/me
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify: TECH_PYTHON competency level increased
```

#### Test 16: Verify Skill Gap Reduced
```
GET /api/v1/skill-gaps/me
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify:
  - TECH_PYTHON gap decreased
  - Or gap removed if now >= required_level
  - Priority scores recalculated
```

#### Test 17: Get Updated Recommendations
```
GET /api/v1/recommendations/me
Headers: Authorization: Bearer {token}

Expected: 200 OK
Verify:
  - Different recommendations than before (gap closed)
  - TECH_PYTHON may no longer be top priority
  - New gaps may be recommended
```

---

## Phase 3: Security & Edge Cases

### Test 18: Unauthenticated Access
```
GET /api/v1/recommendations/me
(No Authorization header)

Expected: 401 Unauthorized
```

### Test 19: Invalid Token
```
GET /api/v1/recommendations/me
Headers: Authorization: Bearer invalid_token

Expected: 401 Unauthorized
```

### Test 20: User Isolation
```
Create two users (user_a, user_b)
User A: Get /recommendations/me (with user_a token)
User B: Get /recommendations/me (with user_b token)

Expected: Different recommendations
Verify: No cross-user data leakage
```

### Test 21: NULL current_level Handling
```
Get skill gaps for new user (unassessed)

Expected: 200 OK
Verify:
  - Gap calculation works with NULL current_level
  - Treated as 0.0 for gap size
  - Recommendations still generated
```

### Test 22: Resource Verification Status
```
Check first recommendation resource

Expected: verification_status = "VERIFIED" or "TENTATIVE"
Verify: No null values
Verify: Explanation notes if TENTATIVE
```

---

## Checklist (Complete Before Postman)

### Documentation
- [ ] List all 33 active competencies
- [ ] List all 88 active mappings
- [ ] List all 26 skipped iGOT mappings (with reason)
- [ ] List all 9 unrepresented competencies (with reason)
- [ ] Update README.md with real counts
- [ ] Add SIH_SUBMISSION_NOTES.md to repo

### Environment Setup
- [ ] Backend running on port 8001 ✅
- [ ] MongoDB with seeded data ✅
- [ ] Postman collection created (all tests listed above)

### Test Execution
- [ ] Phase 1: Loop 1 (Tests 1-10) ⏳
- [ ] Phase 2: Loop 2 (Tests 11-17) ⏳
- [ ] Phase 3: Security (Tests 18-22) ⏳

### Results Documentation
- [ ] Export Postman results as JSON
- [ ] Screenshot each successful test
- [ ] Document any failures discovered
- [ ] Create test report with summary

---

## Success Criteria

✅ All 22 tests pass
✅ All HTTP responses have correct status codes
✅ All data validations pass
✅ Determinism confirmed
✅ Security controls verified
✅ Provider separation working
✅ Cross-user isolation working
✅ Competency updates propagating correctly
✅ Skill gaps recalculating correctly
✅ Recommendations changing based on updated gaps

---

## Action Plan

1. **Freeze Backend** - No more code changes (this document approved)
2. **Create Postman Collection** - Add all 22 tests from this document
3. **Execute Phase 1** - Tests 1-10 (basic workflow)
4. **Fix Issues** - Bug fixes only, no features
5. **Execute Phase 2** - Tests 11-17 (learning path)
6. **Execute Phase 3** - Tests 18-22 (security/edge cases)
7. **Document Results** - Create verification report
8. **SIH Submission** - Include Postman results + documentation

---

**Status:** Ready to begin Postman verification
**Next:** Create Postman collection and execute Phase 1
**Timeline:** 1-2 hours per phase (manual testing)
