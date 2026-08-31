# ShikshaSetu RAG/LLM Debugging Guide

**Issue:** Document upload fails with "Material not ready for generation (status: FAILED)" and "0 text chunks indexed"

**Impact:** Learning materials cannot be processed, MCQ generation unavailable

---

## Problem Analysis

### What's Happening

When a user uploads a document (PDF/DOCX/PPTX):

1. ✅ File is saved to disk
2. ✅ Material record is created in MongoDB (status: PROCESSING)
3. ❌ **FAILS during extraction or embedding** (status: FAILED)
4. ❌ No error is visible in UI (just "Material not ready for generation")
5. ❌ 0 chunks indexed (embedding failed)

### What We Know from Code

From `backend/app/ai/router.py` line 162-230:

```python
async def _process_document():
    # 1. Extract text ← LIKELY FAILING HERE
    extractor = _get_supported_extractors()[file_ext]
    full_text, pages_metadata = extractor.extract(file_path)
    
    # 2. Clean text
    cleaner = TextCleaner()
    full_text = cleaner.clean(full_text)
    
    # 3. Chunk text
    chunker = TextChunker()
    chunks = chunker.chunk_document(...)
    
    # 4. Persist chunks
    chunk_count = await DocumentChunkRepository.create_many(database, chunks)
    
    # 5. Embed chunks ← OR FAILING HERE
    vector_store = VectorStore(embedding_provider)
    vector_store.add_chunks(chunks)
```

### The Catch Block (Line 228-236)

```python
except Exception as e:
    LearningMaterialRepository.update_status(
        database,
        material_id,
        "FAILED",
        "FAILURE",
        str(e)
    )
```

**The error message IS stored in DB but NOT shown in UI.**

---

## Step 1: Find the Actual Error

### Access MongoDB directly

```bash
# Connect to MongoDB
mongosh "mongodb://localhost:27017"

# Switch to database
use shikshasetu

# Find failed materials
db.learning_materials.find({ status: "FAILED" }, { _id: 1, original_filename: 1, status: 1, extraction_status: 1, error_message: 1 })
```

**What to look for:**
- `error_message` field (contains the actual error)
- `extraction_status` field (shows which stage failed)

### Or check backend logs

If running with logging enabled:

```bash
cd backend
python -m uvicorn app.main:app --reload --log-level debug
```

Upload a document and **check console for error messages.**

---

## Step 2: Identify the Root Cause

### Most Common Issues

#### Issue A: Gemini API Key is Invalid

**Check:**
```bash
# Verify API key in .env
grep LLM_API_KEY backend/.env

# Test Gemini API directly
python -c "
from google import genai
client = genai.Client(api_key='YOUR_API_KEY_HERE')
response = client.models.embed_content(
    model='text-embedding-004',
    contents='test'
)
print(response)
"
```

**Fix if invalid:**
1. Get valid API key from: https://aistudio.google.com/app/apikey
2. Update `.env`
3. Restart backend

---

#### Issue B: Text Extraction Failed (PDF/DOCX/PPTX)

**Check in database:**
```bash
db.learning_materials.findOne({ status: "FAILED" })
# Look for: extraction_status field
# If says "EXTRACTION_FAILED" → extractor broke
```

**Test extraction directly:**
```bash
cd backend

python -c "
from app.ai.extraction.pdf import PDFExtractor
from app.ai.extraction.docx import DOCXExtractor
from app.ai.extraction.pptx import PPTXExtractor

# Test PDF
pdf = PDFExtractor()
try:
    text, metadata = pdf.extract('path/to/TechnicalApproach.pptx')
    print(f'Extracted {len(text)} chars')
except Exception as e:
    print(f'PDF extraction failed: {e}')

# Test DOCX
docx = DOCXExtractor()
try:
    text, metadata = docx.extract('path/to/file.docx')
    print(f'Extracted {len(text)} chars')
except Exception as e:
    print(f'DOCX extraction failed: {e}')
"
```

**Common PDF/DOCX extraction issues:**
- File is corrupt
- Library not installed (PyPDF2, python-docx, python-pptx)
- File permissions (can't read temp file)
- Encoding issues (special characters)

**Fix:**
```bash
cd backend
pip install PyPDF2 python-docx python-pptx
```

---

#### Issue C: Chunking Failed (Very Rare)

**Check:**
- Text extraction worked but chunking broke
- Usually means text cleaning caused issues

**Test directly:**
```bash
python -c "
from app.ai.chunking import TextChunker

chunker = TextChunker()
text = 'Your extracted text here'
chunks = chunker.chunk_document(
    text=text,
    material_id='test_id',
    chunk_size=500,
    chunk_overlap=100
)
print(f'Created {len(chunks)} chunks')
"
```

---

#### Issue D: Embedding Failed (Most Likely)

**Check:**
- Text extracted, chunks created, BUT embedding provider fails
- Gemini API call times out or returns error

**Look for in error message:**
- "Gemini embedding failed"
- "API request failed"
- "Rate limit exceeded"
- "Invalid API key"

**Test Gemini embedding directly:**
```bash
python -c "
from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider
import os

api_key = os.getenv('LLM_API_KEY')
provider = GeminiEmbeddingProvider(api_key=api_key)

# Test single embedding
try:
    embedding = provider.embed_text('This is a test')
    print(f'Success: got {len(embedding)}-dim embedding')
except Exception as e:
    print(f'Embedding failed: {e}')

# Test batch embedding
try:
    texts = ['Text 1', 'Text 2', 'Text 3']
    embeddings = provider.embed_texts(texts)
    print(f'Success: got {len(embeddings)} embeddings')
except Exception as e:
    print(f'Batch embedding failed: {e}')
"
```

---

## Step 3: Fix the Issue

### Fix A: Invalid Gemini API Key

1. Get valid key: https://aistudio.google.com/app/apikey
2. Update `.env`:
   ```
   LLM_API_KEY=your_valid_key_here
   ```
3. Restart backend
4. Re-upload document

---

### Fix B: Missing Extraction Libraries

```bash
cd backend
pip install --upgrade PyPDF2 python-docx python-pptx
```

Restart backend and re-upload.

---

### Fix C: PPTX vs PPTX Extension Issue

The file shows as **"TechnicalApproach.pptx"** but extraction might be using wrong extractor.

**Check:**
```bash
python -c "
import os
filename = 'TechnicalApproach.pptx'
ext = os.path.splitext(filename)[1].lower()
print(f'Extension: {ext}')
# Should print: .pptx
"
```

**If it's not recognized, add mapping** in `backend/app/ai/router.py` line 48:

```python
def _get_supported_extractors() -> dict:
    from app.ai.extraction.pdf import PDFExtractor
    from app.ai.extraction.docx import DOCXExtractor
    from app.ai.extraction.pptx import PPTXExtractor
    
    return {
        ".pdf": PDFExtractor(),
        ".docx": DOCXExtractor(),
        ".pptx": PPTXExtractor(),  # ← Make sure this exists
    }
```

---

### Fix D: Slow/Unreliable Gemini API

If Gemini API is timing out or rate-limiting:

**Option 1: Switch to Mock Provider (for testing)**

Update `.env`:
```
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock
```

This will generate fake but functional embeddings (for testing).

Restart and re-upload.

---

**Option 2: Use OpenAI Instead**

If you have OpenAI API key:

```
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-3.5-turbo

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

Restart and re-upload.

---

## Step 4: Improve Error Visibility

### Add Error Endpoint to Show Why Upload Failed

**File:** `backend/app/ai/router.py`

**Add this endpoint:**

```python
@router.get("/{material_id}/status")
async def get_material_status(
    material_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed status of material processing.
    Shows error message if failed.
    """
    database = request.app.state.database
    user_id = str(current_user["_id"])
    
    material = await LearningMaterialRepository.get_by_id(database, material_id, user_id)
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return {
        "material_id": str(material.id),
        "status": material.status,
        "extraction_status": material.extraction_status,
        "error_message": material.error_message,  # ← This shows the actual error
        "chunk_count": material.chunk_count,
        "embedding_count": material.embedding_count,
    }
```

**Then frontend can call:**

```
GET /api/v1/learning-materials/{material_id}/status
```

And display `error_message` to user.

---

### Frontend Improvement

**File:** `frontend/client/src/pages/LearningPage.tsx`

**After upload, poll for status:**

```typescript
const pollMaterialStatus = async (materialId: string) => {
  const response = await fetch(`/api/v1/learning-materials/${materialId}/status`);
  const data = await response.json();
  
  if (data.status === "READY") {
    // Success
    setMaterialReady(true);
  } else if (data.status === "FAILED") {
    // Show error to user
    setError(data.error_message);
  } else {
    // Still processing
    setTimeout(() => pollMaterialStatus(materialId), 2000);
  }
};
```

This way users see **"Embedding failed: Gemini API key invalid"** instead of just "Material not ready".

---

## Step 5: Recovery

### Clear Failed Materials

If you want to clean up failed uploads:

```bash
mongo
use shikshasetu

# Delete failed materials
db.learning_materials.deleteMany({ status: "FAILED" })

# Delete associated chunks
db.document_chunks.deleteMany({ material_id: ObjectId("...") })
```

---

## Complete Diagnostic Checklist

```
[ ] 1. Check MongoDB for error_message in failed material
[ ] 2. Test Gemini API key directly (valid and working?)
[ ] 3. Test PDF/DOCX/PPTX extraction libraries (installed?)
[ ] 4. Test embedding provider (can embed sample text?)
[ ] 5. Check backend logs for detailed error traces
[ ] 6. Verify file extension is recognized (.pptx = pptx?)
[ ] 7. Check API key is not rate-limited or expired
[ ] 8. Try with Mock provider to isolate embedding issue
[ ] 9. Add error endpoint to show detailed failure reason
[ ] 10. Re-upload document and verify status
```

---

## Recommended Next Actions

### Immediate (This Session)

1. **Find the actual error:**
   ```bash
   mongo
   use shikshasetu
   db.learning_materials.findOne({ status: "FAILED" }, { error_message: 1 })
   ```

2. **Based on error, fix:**
   - Invalid API key? → Update `.env` with valid key
   - Missing library? → `pip install` dependencies
   - Timeout? → Switch to Mock provider temporarily
   - Unknown? → Enable debug logging and re-run

3. **Verify fix:**
   - Re-upload document
   - Check status changes to "READY"
   - Attempt MCQ generation

### Short-term (Today)

4. **Add error visibility endpoint** so UI shows why uploads fail
5. **Test with Mock provider** to isolate embedding from extraction
6. **Document the working setup** (which API provider, which libraries)

### Future (Phase 2)

7. **Add async task queue** (Celery/Redis) so document processing doesn't block upload
8. **Add progress webhook** so frontend gets real-time updates
9. **Implement retry logic** for transient API failures
10. **Add document validation** (check file integrity before processing)

---

## If You're Still Stuck

Share:
1. Output of: `db.learning_materials.findOne({ status: "FAILED" })`
2. Your `.env` file (redact API keys): especially `LLM_PROVIDER`, `EMBEDDING_PROVIDER`
3. Console output when you upload a document (with `--log-level debug`)
4. Which file you're trying to upload (PDF/DOCX/PPTX)

This diagnostic guide will help you pinpoint the exact failure point.
