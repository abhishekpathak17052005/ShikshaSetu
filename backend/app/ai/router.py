"""API router for AI document processing and MCQ generation."""
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from bson import ObjectId

from app.auth.dependencies import get_current_user, require_trainer
from app.core.config import get_settings
from app.core.limiter import limiter

from .models import LearningMaterial, DocumentChunk
from .repository import LearningMaterialRepository, DocumentChunkRepository
from .schemas import (
    GenerationRequest,
    GenerationResponse,
    LearningMaterialResponse,
    UploadResponse,
    GeneratedMCQ,
)
from .providers.factory import get_llm_provider
from .embeddings.factory import get_embedding_provider
from .embeddings.base import EmbeddingProvider
from .extraction.pdf import PDFExtractor
from .extraction.docx import DOCXExtractor
from .extraction.pptx import PPTXExtractor
from .extraction.txt import TXTExtractor
from .cleaning import TextCleaner
from .chunking import TextChunker
from .retrieval import VectorStore, RetrieverService
from .generation import MCQGenerator
from .validation import GroundingValidator

# Create router
router = APIRouter(prefix="/learning-materials", tags=["ai"])


class MaterialProcessingError(Exception):
    """A processing failure with an observable pipeline stage."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        super().__init__(message)

# In-memory vector stores per material (Round 1 simplification)
_vector_stores: dict = {}


def _get_material_dir() -> str:
    """Get or create materials storage directory."""
    mat_dir = os.path.join(os.path.dirname(__file__), "../../uploads/materials")
    os.makedirs(mat_dir, exist_ok=True)
    return mat_dir


def _get_supported_extractors() -> dict:
    """Get extractors by file extension."""
    return {
        ".pdf": PDFExtractor,
        ".docx": DOCXExtractor,
        ".pptx": PPTXExtractor,
        ".txt": TXTExtractor,
    }


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_trainer),
) -> UploadResponse:
    """
    Upload a learning material document (PDF, DOCX, PPTX).

    Args:
        file: Uploaded file.
        current_user: Authenticated user.
        request: FastAPI request object.

    Returns:
        Upload response with material ID and status.

    Raises:
        HTTPException: If validation fails or upload fails.
    """
    database = request.app.state.database
    settings = getattr(request.app.state, "settings", None) or get_settings()
    user_id = str(current_user["_id"])

    # Validate filename and extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in _get_supported_extractors():
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Supported: PDF, DOCX, PPTX, TXT"
        )

    disallowed_mimes = {
        "application/x-executable",
        "application/x-dosexec",
        "application/x-msdos-program",
        "application/x-sh",
        "application/javascript",
        "text/javascript",
        "text/html",
        "text/xml",
        "application/xml",
    }
    if file.content_type and file.content_type.lower() in disallowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Disallowed file MIME type: {file.content_type}"
        )

    try:
        # Read file content safely in chunks to avoid unbounded RAM consumption
        content_chunks = []
        bytes_read = 0
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        chunk_read_size = 64 * 1024

        while True:
            chunk = await file.read(chunk_read_size)
            if not chunk:
                break
            bytes_read += len(chunk)
            if bytes_read > max_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Max size: {settings.max_upload_size_mb}MB"
                )
            content_chunks.append(chunk)

        content = b"".join(content_chunks)
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        # Sanitize original_filename: strip path traversal, null bytes, control characters
        raw_name = os.path.basename(file.filename or "document").replace("\x00", "")
        safe_original_name = re.sub(r'[^\w\s\.-]', '_', raw_name).strip() or f"document{file_ext}"

        # Generate storage filename
        material_id = str(ObjectId())
        stored_filename = f"{material_id}{file_ext}"
        file_path = os.path.join(_get_material_dir(), stored_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        # Create material record
        material = LearningMaterial(
            user_id=user_id,
            filename=stored_filename,
            original_filename=safe_original_name,
            content_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            storage_reference=file_path,
            status="PROCESSING",
            extraction_status=None,
        )

        # Save to database
        material_id = LearningMaterialRepository.create(database, material)

        # Process document (synchronous despite async signature — acceptable for single-worker deployment)
        processing_failed = False
        failure_stage = None
        failure_message = None
        try:
            await _process_document(database, material_id, file_path, file_ext, settings)
        except Exception as e:
            processing_failed = True
            # Mark as failed but keep the upload record observable to the client.
            failure_stage = e.stage if isinstance(e, MaterialProcessingError) else "PROCESSING"
            failure_message = str(e)
            LearningMaterialRepository.update_status(
                database,
                material_id,
                "FAILED",
                "FAILURE",
                str(e),
                failure_stage,
            )
            logger.exception("Material %s failed during %s", material_id, failure_stage)

        from app.core.analytics_cache import invalidate_trainer_cache
        invalidate_trainer_cache(user_id)

        # B4 FIX: Return the actual status from DB, not a hardcoded "PROCESSING"
        actual_status = "FAILED" if processing_failed else "READY"
        return UploadResponse(
            material_id=material_id,
            filename=stored_filename,
            status=actual_status,
            message=(
                "Document processed and indexed successfully."
                if not processing_failed
                else "Document upload recorded but processing failed."
            ),
            processing_stage=failure_stage or "READY",
            error_message=failure_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Document upload processing failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Document upload processing failed due to an internal server error."
        )


async def _process_document(
    database,
    material_id: str,
    file_path: str,
    file_ext: str,
    settings,
) -> None:
    """
    Process a document: extract, clean, chunk, embed, and index.
    Note: Uses sync PyMongo despite async signature for FastAPI.

    Args:
        database: MongoDB database instance.
        material_id: Material ID.
        file_path: Path to stored file.
        file_ext: File extension (.pdf, .docx, .pptx).
        settings: Configuration settings.
    """
    try:
        # Update status to PROCESSING
        LearningMaterialRepository.update_status(database, material_id, "PROCESSING", processing_stage="EXTRACTION")

        # Extract text
        extractor = _get_supported_extractors()[file_ext]
        try:
            full_text, pages_metadata = extractor.extract(file_path)
        except Exception as exc:
            raise MaterialProcessingError("EXTRACTION", str(exc)) from exc

        # Clean text
        cleaner = TextCleaner()
        full_text = cleaner.clean(full_text)
        if not full_text.strip():
            raise MaterialProcessingError("EXTRACTION", "Document contains no extractable text")

        MAX_EXTRACTED_CHARS = 2_000_000
        if len(full_text) > MAX_EXTRACTED_CHARS:
            full_text = full_text[:MAX_EXTRACTED_CHARS]

        LearningMaterialRepository.update_status(database, material_id, "PROCESSING", "SUCCESS", processing_stage="CHUNKING")

        # Chunk text
        chunker = TextChunker()
        chunks = chunker.chunk_document(
            text=full_text,
            material_id=material_id,
            pages_metadata=pages_metadata,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        if not chunks:
            raise MaterialProcessingError("CHUNKING", "No chunks created from document")

        MAX_ALLOWED_CHUNKS = 500
        if len(chunks) > MAX_ALLOWED_CHUNKS:
            logger.warning("Material %s generated %d chunks; capping at %d", material_id, len(chunks), MAX_ALLOWED_CHUNKS)
            chunks = chunks[:MAX_ALLOWED_CHUNKS]

        # Persist chunks WITHOUT embeddings (embedding_status defaults to PENDING)
        chunk_count = DocumentChunkRepository.create_many(database, chunks)

        # Embed chunks and persist each vector to MongoDB (Task 5/6 upgrade)
        # Removes the old in-memory-only VectorStore approach and the SHA-256 fallback.
        embedding_count = 0
        LearningMaterialRepository.update_status(database, material_id, "PROCESSING", "SUCCESS", processing_stage="EMBEDDING")
        try:
            from app.rag.embedding_index import embed_and_persist_chunks, EmbeddingIndexManager
            embedding_provider = get_embedding_provider(settings)
            if not embedding_provider.is_available():
                raise MaterialProcessingError("EMBEDDING", "Embedding provider is unavailable")
            embedded, failed = embed_and_persist_chunks(
                database=database,
                chunks=chunks,
                embedding_provider=embedding_provider,
                model_name=settings.embedding_model,
            )
            embedding_count = embedded
            if failed or embedded != chunk_count:
                raise MaterialProcessingError(
                    "EMBEDDING",
                    f"Embedding failed for {failed} of {chunk_count} chunks",
                )
        except Exception as emb_exc:
            if isinstance(emb_exc, MaterialProcessingError):
                raise
            raise MaterialProcessingError("EMBEDDING", str(emb_exc)) from emb_exc

        # Keep _vector_stores dict populated for backward compatibility with
        # existing unit tests that use the old VectorStore API directly.
        try:
            from .embeddings.mock_provider import MockEmbeddingProvider
            vs = VectorStore(MockEmbeddingProvider(dimension=settings.embedding_dimension))
            # Only add chunks that actually have embeddings in memory
            embedded_chunks = [c for c in chunks if c.embedding_status == "EMBEDDED"]
            if embedded_chunks:
                vs.chunks = embedded_chunks
                import numpy as np
                vecs = [np.array(c.embedding, dtype=np.float32) for c in embedded_chunks]
                vs.embeddings = np.stack(vecs) if vecs else None
            _vector_stores[material_id] = vs
        except Exception as exc:
            raise MaterialProcessingError("INDEXING", str(exc)) from exc

        LearningMaterialRepository.update_status(database, material_id, "PROCESSING", "SUCCESS", processing_stage="INDEXING")
        if not EmbeddingIndexManager.get_instance().rebuild(database, material_id):
            raise MaterialProcessingError("INDEXING", "Vector index rebuild failed")

        if not LearningMaterialRepository.update_chunk_counts(
            database, material_id, chunk_count, embedding_count
        ):
            raise MaterialProcessingError("INDEXING", "Material counts could not be persisted")

        # Update material status only after extraction, chunks, embeddings, and index succeed.
        LearningMaterialRepository.update_status(
            database,
            material_id,
            "READY",
            "SUCCESS",
            processing_stage="READY",
        )

    except MaterialProcessingError:
        raise
    except Exception as e:
        raise MaterialProcessingError("PROCESSING", str(e)) from e


@router.get("/{material_id}", response_model=LearningMaterialResponse)
async def get_material_metadata(
    material_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> LearningMaterialResponse:
    """
    Get metadata about a learning material (with ownership check).

    Args:
        material_id: Material ID.
        current_user: Authenticated user.
        request: FastAPI request object.

    Returns:
        Material metadata.

    Raises:
        HTTPException: If not found or not owned by user.
    """
    database = request.app.state.database
    user_id = str(current_user["_id"])

    material = LearningMaterialRepository.get_by_id(database, material_id, user_id)

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    return LearningMaterialResponse(
        id=str(material.id),
        filename=material.filename,
        original_filename=material.original_filename,
        content_type=material.content_type,
        file_size=material.file_size,
        status=material.status,
        extraction_status=material.extraction_status,
        processing_stage=material.processing_stage,
        error_message=material.error_message,
        chunk_count=material.chunk_count,
        embedding_count=material.embedding_count,
        created_at=material.created_at.isoformat(),
        updated_at=material.updated_at.isoformat(),
    )


@router.post("/{material_id}/reprocess", response_model=LearningMaterialResponse)
@limiter.limit("10/minute")
async def reprocess_material(
    material_id: str,
    request: Request,
    current_user: dict = Depends(require_trainer),
) -> LearningMaterialResponse:
    """Idempotently rebuild extraction, chunks, embeddings, and the vector index."""
    database = request.app.state.database
    user_id = str(current_user["_id"])
    settings = getattr(request.app.state, "settings", None) or get_settings()
    material = LearningMaterialRepository.get_by_id(database, material_id, user_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    file_path = material.storage_reference
    if not os.path.isfile(file_path):
        LearningMaterialRepository.update_status(
            database, material_id, "FAILED", "FAILURE", "Stored material file does not exist", "STORAGE"
        )
        raise HTTPException(status_code=409, detail="Stored material file does not exist")

    file_ext = os.path.splitext(material.original_filename or material.filename)[1].lower()
    if file_ext not in _get_supported_extractors():
        raise HTTPException(status_code=400, detail="Material file type is no longer supported")

    try:
        await _process_document(database, material_id, file_path, file_ext, settings)
    except MaterialProcessingError as exc:
        LearningMaterialRepository.update_status(
            database, material_id, "FAILED", "FAILURE", str(exc), exc.stage
        )
        raise HTTPException(status_code=422, detail={"status": "FAILED", "stage": exc.stage, "message": str(exc)}) from exc

    return await get_material_metadata(material_id, request, current_user)


@router.post(
    "/{material_id}/generate-questions",
    response_model=GenerationResponse
)
@limiter.limit("15/minute")
async def generate_questions(
    material_id: str,
    request_body: GenerationRequest,
    request: Request,
    current_user: dict = Depends(require_trainer),
) -> GenerationResponse:
    """
    Generate grounded MCQs from a learning material.

    Args:
        material_id: Material ID.
        request_body: Generation request with competency and question count.
        current_user: Authenticated user.
        request: FastAPI request object.

    Returns:
        Generated questions with source traceability.

    Raises:
        HTTPException: If material not found, not ready, or generation fails.
    """
    database = request.app.state.database
    user_id = str(current_user["_id"])
    settings = get_settings()

    # Check material exists and is ready
    material = LearningMaterialRepository.get_by_id(database, material_id, user_id)

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.status != "READY":
        raise HTTPException(
            status_code=400,
            detail=f"Material not ready for generation (status: {material.status})"
        )

    try:
        # Get or rebuild vector store (lazy load with proper fallback)
        if material_id not in _vector_stores:
            # Reload from database
            chunks = DocumentChunkRepository.get_by_material(database, material_id)

            if not chunks:
                raise HTTPException(
                    status_code=500,
                    detail="Material has no chunks — reprocess the document."
                )

            # Try real embedding provider, fall back to mock (B4 fix: mirror the upload-time fallback)
            try:
                embedding_provider = get_embedding_provider()
            except Exception:
                from .embeddings.mock_provider import MockEmbeddingProvider
                embedding_provider = MockEmbeddingProvider(dimension=settings.embedding_dimension)

            try:
                vector_store = VectorStore(embedding_provider)
                vector_store.add_chunks(chunks)
            except Exception:
                from .embeddings.mock_provider import MockEmbeddingProvider
                vector_store = VectorStore(MockEmbeddingProvider(dimension=settings.embedding_dimension))
                vector_store.add_chunks(chunks)

            _vector_stores[material_id] = vector_store
        else:
            vector_store = _vector_stores[material_id]

        # Initialize generation pipeline
        llm_provider = get_llm_provider()
        if not llm_provider.is_available():
            raise HTTPException(
                status_code=503,
                detail="LLM provider not configured"
            )

        retriever = RetrieverService(vector_store)
        generator = MCQGenerator(llm_provider, retriever)

        # Generate questions
        query = request_body.competency_code
        max_allowed = max(getattr(settings, "max_questions_per_generation", 20) or 20, 10)
        target_count = min(request_body.question_count, max_allowed)

        questions = generator.generate_questions(
            query=query,
            competency_code=request_body.competency_code,
            question_count=target_count,
            difficulty=request_body.difficulty,
            material_id=material_id,
            bloom_level=request_body.bloom_level,
        )

        # Validate questions (structural + basic grounding)
        chunk_repo = DocumentChunkRepository()
        valid_questions, invalid_questions = GroundingValidator.validate_batch(
            questions,
            chunk_repo,
            material_id,
            database
        )

        if not valid_questions:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate valid questions: {len(invalid_questions)} invalid"
            )

        # Duplicate detection — filter out near-duplicates against existing question bank
        from .validation import filter_duplicate_questions
        existing_q_docs = list(database.question_bank.find(
            {"competency_code": request_body.competency_code},
            {"question": 1, "_id": 0},
            limit=500,
        ))
        unique_questions, dup_questions = filter_duplicate_questions(
            valid_questions, existing_q_docs, similarity_threshold=0.80
        )
        if dup_questions:
            import logging as _log
            _log.getLogger(__name__).info(
                "Filtered %d near-duplicate question(s) from generation batch",
                len(dup_questions),
            )
        if not unique_questions:
            raise HTTPException(
                status_code=500,
                detail="All generated questions were near-duplicates of existing content. Try regenerating.",
            )

        final_questions = unique_questions

        # Get chunks used for source traceability
        retrieved_chunks = set()
        for q in final_questions:
            retrieved_chunks.update(q.source_chunks)

        # Persist questions into Trainer Review Studio
        try:
            from app.trainer.service import TrainerService
            TrainerService(database).save_generated_questions(
                trainer_id=user_id,
                material_id=material_id,
                competency_code=request_body.competency_code,
                questions=[
                    q.model_dump() if isinstance(q, GeneratedMCQ) else dict(q)
                    for q in final_questions
                ],
            )
        except Exception as exc:
            logger.exception("Question persistence failed for material %s", material_id)
            raise HTTPException(status_code=500, detail="Validated questions could not be persisted") from exc

        return GenerationResponse(
            material_id=material_id,
            competency_code=request_body.competency_code,
            questions=final_questions,
            retrieved_chunk_count=len(retrieved_chunks),
            generation_timestamp=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("AI MCQ generation failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail="AI question generation failed due to an internal server error."
        )
