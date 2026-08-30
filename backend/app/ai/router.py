"""API router for AI document processing and MCQ generation."""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request
from bson import ObjectId

from app.auth.dependencies import get_current_user
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
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
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

        # Process document asynchronously (for now, synchronous for Round 1)
        try:
            await _process_document(database, material_id, file_path, file_ext, settings)
        except Exception as e:
            # Mark as failed but don't block upload
            LearningMaterialRepository.update_status(
                database,
                material_id,
                "FAILED",
                "FAILURE",
                str(e)
            )

        return UploadResponse(
            material_id=material_id,
            filename=stored_filename,
            status="PROCESSING",
            message="Document uploaded successfully and queued for processing"
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

    Args:
        database: MongoDB database instance.
        material_id: Material ID.
        file_path: Path to stored file.
        file_ext: File extension (.pdf, .docx, .pptx).
        settings: Configuration settings.
    """
    try:
        # Update status to PROCESSING
        await LearningMaterialRepository.update_status(database, material_id, "PROCESSING")

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

        # Persist chunks
        chunk_count = await DocumentChunkRepository.create_many(database, chunks)

        # Embed and index chunks
        embedding_provider = get_embedding_provider()
        vector_store = VectorStore(embedding_provider)
        embedding_count = vector_store.add_chunks(chunks)

        # Store vector store in memory
        _vector_stores[material_id] = vector_store

        # Update material status
        await LearningMaterialRepository.update_status(
            database,
            material_id,
            "READY",
            "SUCCESS"
        )
        await LearningMaterialRepository.update_chunk_counts(
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

    material = await LearningMaterialRepository.get_by_id(database, material_id, user_id)

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
    current_user: dict = Depends(get_current_user),
    request: Request,
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
    material = await LearningMaterialRepository.get_by_id(database, material_id, user_id)

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.status != "READY":
        raise HTTPException(
            status_code=400,
            detail=f"Material not ready for generation (status: {material.status})"
        )

    try:
        # Get or load vector store
        if material_id not in _vector_stores:
            # Reload from database
            chunks = await DocumentChunkRepository.get_by_material(database, material_id)

            if not chunks:
                raise HTTPException(
                    status_code=500,
                    detail="Material has no chunks"
                )

            embedding_provider = get_embedding_provider()
            vector_store = VectorStore(embedding_provider)
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
        valid_questions, invalid_questions = await GroundingValidator.validate_batch(
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
