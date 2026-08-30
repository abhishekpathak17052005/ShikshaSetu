# PHASE 6 VERIFICATION CHECKLIST

**Status:** ⚠️ IMPLEMENTATION COMPLETE → VERIFICATION NEEDED

**Goal:** Confirm the real AI pipeline works end-to-end before proceeding to Phase 7.

---

## PRE-VERIFICATION SETUP

- [ ] Fix NumPy build environment issue
  - Option A: Install C++ build tools (Visual Studio Build Tools)
  - Option B: Use pre-built wheel
  - [ ] Confirm: `pip install -r requirements.txt` succeeds

- [ ] Set up test environment variables
  ```bash
  LLM_PROVIDER=mock              # Start with mock
  EMBEDDING_PROVIDER=mock
  ```

- [ ] Prepare real OpenAI credentials (for later)
  - [ ] Get valid `LLM_API_KEY=sk-...`
  - [ ] Test OpenAI API key is valid
  - [ ] Confirm account has credits

---

## PHASE 1: MOCK PROVIDER VERIFICATION

### Run All Tests
```bash
pytest tests/test_ai_unit.py -v
pytest tests/test_ai_security.py -v
pytest tests/test_health.py -v              # Ensure Phase 1-5 still works
```

**Checklist:**
- [ ] All AI unit tests pass
- [ ] All security tests pass
- [ ] Phase 1-5 regression tests pass (60/60)
- [ ] No import errors
- [ ] Manual verification script runs successfully

---

## PHASE 2: REAL DOCUMENT PIPELINE (with Mock LLM)

### Test with Sample PDF
1. [ ] Create or use test PDF: `backend/tests/fixtures/sample_sql.pdf`
   - Content: 2-3 pages of SQL tutorial text
   - Size: <1 MB
   - Ensure extractable text (not scanned)

2. [ ] Test extraction standalone
   ```python
   from app.ai.extraction.pdf import PDFExtractor
   text, pages = PDFExtractor.extract("path/to/sample_sql.pdf")
   assert len(text) > 100
   assert len(pages) >= 1
   ```

3. [ ] Test full pipeline without API
   ```bash
   python manual_verification_phase6.py
   # Should show all 7 tests passing
   ```

**Checklist:**
- [ ] PDF extraction produces clean text
- [ ] Page metadata preserved
- [ ] Chunks created deterministically
- [ ] Mock embeddings generated
- [ ] Vector retrieval works
- [ ] Mock MCQs generated
- [ ] Source chunks referenced

### Test with DOCX
- [ ] Extract `backend/tests/fixtures/sample_python.docx`
- [ ] Verify text extraction
- [ ] Verify paragraph structure preserved

### Test with PPTX
- [ ] Extract `backend/tests/fixtures/sample_intro.pptx`
- [ ] Verify slide numbers preserved
- [ ] Verify notes extracted if present

---

## PHASE 3: API INTEGRATION TEST (with Mock LLM, Real DB)

### Start Backend Server
```bash
uvicorn app.main:app --reload
```

### Test Upload Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/learning-materials/upload \
  -H "Authorization: Bearer <valid_jwt_token>" \
  -F "file=@tests/fixtures/sample_sql.pdf"
```

**Expected Response:**
```json
{
  "material_id": "507f1f77...",
  "filename": "507f1f77...pdf",
  "status": "PROCESSING",
  "message": "Document uploaded..."
}
```

**Checklist:**
- [ ] HTTP 200 OK
- [ ] material_id returned
- [ ] Document stored on filesystem
- [ ] Entry in learning_materials collection
- [ ] Status is PROCESSING

### Poll Material Status
```bash
curl http://localhost:8000/api/v1/learning-materials/507f1f77... \
  -H "Authorization: Bearer <token>"
```

**Expected:** Eventually status = "READY", chunk_count > 0

**Checklist:**
- [ ] Status transitions: PROCESSING → READY
- [ ] chunk_count correct (>0)
- [ ] embedding_count correct
- [ ] extraction_status = SUCCESS

### Test Generation Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/learning-materials/507f1f77.../generate-questions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "competency_code": "TECH_SQL",
    "question_count": 3,
    "difficulty": "MEDIUM"
  }'
```

**Expected Response:**
```json
{
  "material_id": "507f1f77...",
  "competency_code": "TECH_SQL",
  "questions": [
    {
      "question": "...",
      "options": ["...", "...", "...", "..."],
      "correct_answer": "B",
      "explanation": "...",
      "difficulty": "MEDIUM",
      "source_chunks": ["chunk_1", "chunk_2"]
    }
  ],
  "retrieved_chunk_count": 5,
  "generation_timestamp": "..."
}
```

**Checklist:**
- [ ] HTTP 200 OK
- [ ] questions array non-empty
- [ ] Each question has all required fields
- [ ] source_chunks list non-empty (mandatory)
- [ ] retrieved_chunk_count > 0

### Test User Isolation
- [ ] Create User A with token_a
- [ ] Create User B with token_b
- [ ] User A uploads document → material_id_a
- [ ] User B tries: `GET /learning-materials/material_id_a` with token_b
- [ ] Expected: HTTP 404 (not found)

**Checklist:**
- [ ] User B cannot see User A's material
- [ ] User B cannot generate questions from User A's material
- [ ] API returns 404, not 403 (implies not owned, not just unauthorized)

---

## PHASE 4: REAL LLM INTEGRATION TEST

### Switch to OpenAI Provider
```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-...
export EMBEDDING_PROVIDER=openai
```

### Restart Backend
```bash
uvicorn app.main:app --reload
```

### Repeat Full Pipeline
1. [ ] Upload real PDF via API
2. [ ] Wait for PROCESSING → READY
3. [ ] Generate questions
4. [ ] Verify response format
5. [ ] Verify questions make sense (semantic validation)
6. [ ] Verify source chunks are valid

### Checklist for Real LLM
- [ ] OpenAI API call succeeds (no auth errors)
- [ ] Questions are coherent (not gibberish)
- [ ] Explanations are factual and grounded
- [ ] source_chunks exist in database
- [ ] source_chunks belong to the material
- [ ] No hallucinations (questions directly support by source text)
- [ ] Response time <5 seconds

### Edge Cases
- [ ] Generate 5 questions from small document (2 pages)
- [ ] Generate questions for different competency codes
- [ ] Generate with EASY difficulty
- [ ] Generate with HARD difficulty

**Checklist:**
- [ ] All edge cases return valid MCQs
- [ ] No crashes or 500 errors
- [ ] Questions quality consistent

---

## PHASE 5: REGRESSION & SECURITY

### Full Test Suite
```bash
pytest tests/ -v --tb=short
```

**Expected:** All 60+ tests pass

**Checklist:**
- [ ] Phase 1-5 tests: 60 passing
- [ ] Phase 6 security tests: 11 passing
- [ ] Phase 6 unit tests: 40+ passing
- [ ] Zero failures

### Database Cleanup
```bash
# Verify no leftover materials in prod DB
# Confirm indexes exist
db.learning_materials.getIndexes()
db.document_chunks.getIndexes()
```

**Checklist:**
- [ ] Indexes created
- [ ] No stray test data in production
- [ ] Collections have proper schema

### Security Audit
- [ ] No API keys in response bodies
- [ ] No filesystem paths exposed
- [ ] No original filenames in URLs
- [ ] JWT required on all AI endpoints
- [ ] User_id scoped to all queries

**Checklist:**
- [ ] All security checks pass
- [ ] No secrets leaked
- [ ] User isolation intact

---

## PHASE 6: DOCUMENTATION & HANDOFF

- [ ] Update PHASE_6_REPORT.md with:
  - [ ] Real LLM test results (PASSED/FAILED)
  - [ ] Performance metrics (actual numbers)
  - [ ] Sample MCQ output
  - [ ] Full pipeline trace

- [ ] Create test fixtures in `backend/tests/fixtures/`
  - [ ] sample_sql.pdf
  - [ ] sample_python.docx
  - [ ] sample_intro.pptx

- [ ] Document known issues (if any)

- [ ] Prepare deployment instructions

**Checklist:**
- [ ] Report updated
- [ ] Test fixtures committed
- [ ] README updated with Phase 6 info
- [ ] Deployment guide finalized

---

## SIGN-OFF

| Phase | Status | Date | Notes |
|-------|--------|------|-------|
| Mock Provider | — | — | Pending env fix |
| Document Pipeline | — | — | Pending env fix |
| API Integration | — | — | Pending env fix |
| Real LLM | — | — | Pending API credentials |
| Regression | — | — | Pending full test run |
| Documentation | — | — | Pending verification |

---

## WHEN COMPLETE

Once all checklist items are ✅:

1. Update PHASE_6_REPORT.md: `LIVE LLM TEST: PASSED`
2. Tag version `v0.4.0-phase6` in git
3. Commit to branch `phase-6-verified`
4. Proceed to Phase 7 implementation

---

**DO NOT proceed to Phase 7 until this checklist is 100% complete.**
