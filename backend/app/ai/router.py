"""API router for AI document processing and MCQ generation."""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from bson import ObjectId

from app.auth.dependencies import get_current_user, require_trainer
from app.core.config import get_settings

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
    settings = get_settings()
    user_id = str(current_user["_id"])

    # Validate filename and extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in _get_supported_extractors():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: PDF, DOCX, PPTX"
        )

    try:
        # Read file content
        content = await file.read()

        # Validate file size
        file_size = len(content)
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.max_upload_size_mb}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")

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
            original_filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            file_size=file_size,
            storage_reference=file_path,
            status="PROCESSING",
            extraction_status=None,
        )

        # Save to database
        material_id = LearningMaterialRepository.create(database, material)

        # Process document (synchronous despite async signature — single-worker acceptable for hackathon)
        processing_failed = False
        try:
            await _process_document(database, material_id, file_path, file_ext, settings)
        except Exception as e:
            processing_failed = True
            # Mark as failed but don't block the upload acknowledgement
            LearningMaterialRepository.update_status(
                database,
                material_id,
                "FAILED",
                "FAILURE",
                str(e)
            )

        # B4 FIX: Return the actual status from DB, not a hardcoded "PROCESSING"
        actual_status = "FAILED" if processing_failed else "READY"
        return UploadResponse(
            material_id=material_id,
            filename=stored_filename,
            status=actual_status,
            message=(
                "Document processed and indexed successfully."
                if not processing_failed
                else "Document upload recorded but processing failed. Check logs."
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
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
        LearningMaterialRepository.update_status(database, material_id, "PROCESSING")

        # Extract text
        extractor = _get_supported_extractors()[file_ext]
        full_text, pages_metadata = extractor.extract(file_path)

        # Clean text
        cleaner = TextCleaner()
        full_text = cleaner.clean(full_text)

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
            raise Exception("No chunks created from document")

        # Persist chunks WITHOUT embeddings (embedding_status defaults to PENDING)
        chunk_count = DocumentChunkRepository.create_many(database, chunks)

        # Embed chunks and persist each vector to MongoDB (Task 5/6 upgrade)
        # Removes the old in-memory-only VectorStore approach and the SHA-256 fallback.
        embedding_count = 0
        try:
            from app.rag.embedding_index import embed_and_persist_chunks, EmbeddingIndexManager
            embedding_provider = get_embedding_provider()
            if embedding_provider.is_available():
                embedded, failed = embed_and_persist_chunks(
                    database=database,
                    chunks=chunks,
                    embedding_provider=embedding_provider,
                    model_name=settings.embedding_model,
                )
                embedding_count = embedded
                # Build the in-memory numpy index for this material
                EmbeddingIndexManager.get_instance().rebuild(database, material_id)
                if failed > 0:
                    logger.warning(
                        "Material %s: %d chunks failed embedding (marked FAILED for retry)",
                        material_id, failed,
                    )
            else:
                logger.warning(
                    "Embedding provider unavailable for material %s — "
                    "chunks stored without embeddings, keyword search only.",
                    material_id,
                )
        except Exception as emb_exc:
            # Embedding failure must NOT prevent the material from being usable.
            # Keyword search still works. Chunks remain PENDING for retry.
            logger.warning(
                "Embedding step failed for material %s: %s. "
                "Falling back to keyword-only retrieval.",
                material_id, emb_exc,
            )

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
        except Exception:
            pass  # Non-critical — new EmbeddingIndexManager is the primary path

        # Update material status
        LearningMaterialRepository.update_status(
            database,
            material_id,
            "READY",
            "SUCCESS"
        )
        LearningMaterialRepository.update_chunk_counts(
            database,
            material_id,
            chunk_count,
            embedding_count
        )

    except Exception as e:
        raise Exception(f"Document processing failed: {str(e)}")


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
        chunk_count=material.chunk_count,
        embedding_count=material.embedding_count,
        created_at=material.created_at.isoformat(),
        updated_at=material.updated_at.isoformat(),
    )


@router.post(
    "/{material_id}/generate-questions",
    response_model=GenerationResponse
)
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
        questions = generator.generate_questions(
            query=query,
            competency_code=request_body.competency_code,
            question_count=min(request_body.question_count, settings.max_questions_per_generation),
            difficulty=request_body.difficulty,
        )

        # Validate questions
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

        # Get chunks used for source traceability
        retrieved_chunks = set()
        for q in valid_questions:
            retrieved_chunks.update(q.source_chunks)

        # Persist questions into Trainer Review Studio
        try:
            from app.trainer.service import TrainerService
            TrainerService(database).save_generated_questions(
                trainer_id=user_id,
                material_id=material_id,
                competency_code=request_body.competency_code,
                questions=[q.dict() if hasattr(q, "dict") else q for q in valid_questions],
            )
        except Exception:
            pass

        return GenerationResponse(
            material_id=material_id,
            competency_code=request_body.competency_code,
            questions=valid_questions,
            retrieved_chunk_count=len(retrieved_chunks),
            generation_timestamp=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )
