"""FastAPI router for Trainer Assessment Studio & Question Review."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.ai.chunking import TextChunker
from app.ai.cleaning import TextCleaner
from app.ai.embeddings.factory import get_embedding_provider
from app.ai.generation import MCQGenerator
from app.ai.models import LearningMaterial
from app.ai.providers.factory import get_llm_provider
from app.ai.repository import DocumentChunkRepository, LearningMaterialRepository
from app.ai.retrieval import RetrieverService, VectorStore
from app.ai.validation import GroundingValidator
from app.auth.dependencies import require_trainer
from app.core.config import get_settings
from app.trainer.repository import create_trainer_indexes
from app.trainer.schemas import (
    TrainerDashboardResponse,
    TrainerFeedbackRequest,
    TrainerGenerateQuestionsRequest,
    TrainerLearnerAttemptResponse,
    TrainerLearnerSummary,
    TrainerMaterialResponse,
    TrainerQuestionResponse,
    TrainerQuestionReviewRequest,
    TrainerQuestionUpdateRequest,
    TrainerQuizAssignRequest,
    TrainerQuizAssignResponse,
    TrainerQuizCreateRequest,
    TrainerQuizResponse,
)
from app.trainer.service import TrainerService, TrainerServiceError

router = APIRouter(prefix="/trainer", tags=["trainer"])
CurrentTrainer = Annotated[dict, Depends(require_trainer)]


def _get_service(request: Request) -> TrainerService:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available",
        )
    create_trainer_indexes(database)
    return TrainerService(database)


# =============================================================================
# Dashboard & Materials
# =============================================================================

@router.get("/dashboard", response_model=TrainerDashboardResponse)
def get_trainer_dashboard(
    request: Request,
    current_user: CurrentTrainer,
) -> dict:
    """Retrieve aggregated trainer metrics and recent activity."""
    service = _get_service(request)
    return service.get_dashboard(str(current_user["_id"]))


@router.get("/materials", response_model=list[TrainerMaterialResponse])
def list_trainer_materials(
    request: Request,
    current_user: CurrentTrainer,
) -> list[dict]:
    """List all learning materials uploaded by the trainer with question counts."""
    service = _get_service(request)
    return service.list_materials(str(current_user["_id"]))


@router.get("/materials/{material_id}", response_model=TrainerMaterialResponse)
def get_trainer_material(
    request: Request,
    material_id: str,
    current_user: CurrentTrainer,
) -> dict:
    """Get metadata for a specific learning material."""
    service = _get_service(request)
    try:
        return service.get_material_detail(str(current_user["_id"]), material_id)
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =============================================================================
# AI Question Generation & Review Studio
# =============================================================================

@router.post("/materials/{material_id}/generate", response_model=list[TrainerQuestionResponse])
def generate_questions_for_review(
    request: Request,
    material_id: str,
    payload: TrainerGenerateQuestionsRequest,
    current_user: CurrentTrainer,
) -> list[dict]:
    """
    Trigger RAG question generation from uploaded material and persist into
    the review studio in GENERATED state.
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=500, detail="Database not available")

    settings = get_settings()
    trainer_id = str(current_user["_id"])

    # Check material ownership
    material = LearningMaterialRepository.get_by_id(database, material_id, trainer_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found or not owned by trainer")

    if material.status != "READY":
        raise HTTPException(status_code=400, detail=f"Material not ready for generation (status: {material.status})")

    try:
        # Load chunks & vector store
        chunks = DocumentChunkRepository.get_by_material(database, material_id)
        if not chunks:
            raise HTTPException(status_code=500, detail="Material has no chunks")

        settings = getattr(request.app.state, "settings", None) or get_settings()
        embedding_provider = get_embedding_provider(settings)
        vector_store = VectorStore(embedding_provider)
        vector_store.add_chunks(chunks)

        llm_provider = get_llm_provider(settings)
        if not llm_provider.is_available():
            raise HTTPException(status_code=503, detail="LLM provider not configured")

        retriever = RetrieverService(vector_store)
        generator = MCQGenerator(llm_provider, retriever)

        # Generate questions
        raw_questions = generator.generate_questions(
            query=payload.competency_code,
            competency_code=payload.competency_code,
            question_count=min(payload.question_count, settings.max_questions_per_generation),
            difficulty=payload.difficulty,
        )

        chunk_repo = DocumentChunkRepository()
        valid_questions, _ = GroundingValidator.validate_batch(
            raw_questions,
            chunk_repo,
            material_id,
            database,
        )

        if not valid_questions:
            valid_questions = raw_questions

        # Persist questions into review studio
        service = _get_service(request)
        saved = service.save_generated_questions(
            trainer_id=trainer_id,
            material_id=material_id,
            competency_code=payload.competency_code,
            questions=[q.dict() if hasattr(q, "dict") else q for q in valid_questions],
        )

        return [service._format_question(q) for q in saved]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.get("/questions", response_model=list[TrainerQuestionResponse])
def list_all_trainer_questions(
    request: Request,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: CurrentTrainer = None,
) -> list[dict]:
    """List all questions generated/reviewed across all trainer materials."""
    service = _get_service(request)
    return service.list_all_questions(
        trainer_id=str(current_user["_id"]),
        status_filter=status_filter,
    )


@router.get("/materials/{material_id}/questions", response_model=list[TrainerQuestionResponse])
def list_questions_for_material(
    request: Request,
    material_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: CurrentTrainer = None,
) -> list[dict]:
    """List all generated/reviewed questions for a material."""
    service = _get_service(request)
    return service.list_questions_for_material(
        trainer_id=str(current_user["_id"]),
        material_id=material_id,
        status_filter=status_filter,
    )


@router.get("/questions/{question_id}", response_model=TrainerQuestionResponse)
def get_trainer_question(
    request: Request,
    question_id: str,
    current_user: CurrentTrainer,
) -> dict:
    """View question detail with full answer key, explanation, and grounding score."""
    service = _get_service(request)
    try:
        return service.get_question(str(current_user["_id"]), question_id)
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/questions/{question_id}", response_model=TrainerQuestionResponse)
def edit_trainer_question(
    request: Request,
    question_id: str,
    payload: TrainerQuestionUpdateRequest,
    current_user: CurrentTrainer,
) -> dict:
    """Edit question content and transition review status to EDITED."""
    service = _get_service(request)
    try:
        return service.edit_question(
            trainer_id=str(current_user["_id"]),
            question_id=question_id,
            updates=payload.model_dump(exclude_unset=True),
        )
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/questions/{question_id}/approve", response_model=TrainerQuestionResponse)
def approve_trainer_question(
    request: Request,
    question_id: str,
    payload: Optional[TrainerQuestionReviewRequest] = None,
    current_user: CurrentTrainer = None,
) -> dict:
    """Approve a question, making it eligible for inclusion in published quizzes."""
    service = _get_service(request)
    notes = payload.review_notes if payload else None
    try:
        return service.review_question(
            trainer_id=str(current_user["_id"]),
            question_id=question_id,
            action="APPROVE",
            notes=notes,
        )
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/questions/{question_id}/reject", response_model=TrainerQuestionResponse)
def reject_trainer_question(
    request: Request,
    question_id: str,
    payload: Optional[TrainerQuestionReviewRequest] = None,
    current_user: CurrentTrainer = None,
) -> dict:
    """Reject a question so it will not be used in quizzes."""
    service = _get_service(request)
    notes = payload.review_notes if payload else None
    try:
        return service.review_question(
            trainer_id=str(current_user["_id"]),
            question_id=question_id,
            action="REJECT",
            notes=notes,
        )
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# Quiz Studio (Create, Publish, Assign)
# =============================================================================

@router.post("/quizzes", response_model=TrainerQuizResponse, status_code=status.HTTP_201_CREATED)
def create_trainer_quiz(
    request: Request,
    payload: TrainerQuizCreateRequest,
    current_user: CurrentTrainer,
) -> dict:
    """
    Create a new quiz draft from APPROVED questions.
    Rejects any unapproved or rejected questions.
    """
    service = _get_service(request)
    try:
        return service.create_quiz_draft(
            trainer_id=str(current_user["_id"]),
            title=payload.title,
            description=payload.description,
            material_id=payload.material_id,
            competency_code=payload.competency_code,
            question_ids=payload.question_ids,
        )
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/quizzes", response_model=list[TrainerQuizResponse])
def list_trainer_quizzes(
    request: Request,
    current_user: CurrentTrainer,
) -> list[dict]:
    """List all quizzes created by the trainer."""
    service = _get_service(request)
    return service.list_quizzes(str(current_user["_id"]))


@router.get("/quizzes/{quiz_id}", response_model=TrainerQuizResponse)
def get_trainer_quiz(
    request: Request,
    quiz_id: str,
    current_user: CurrentTrainer,
) -> dict:
    """Get details for a specific quiz owned by the trainer."""
    service = _get_service(request)
    try:
        return service.get_quiz_details(str(current_user["_id"]), quiz_id)
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/quizzes/{quiz_id}/publish", response_model=TrainerQuizResponse)
def publish_trainer_quiz(
    request: Request,
    quiz_id: str,
    current_user: CurrentTrainer,
) -> dict:
    """Publish a quiz draft to make it accessible to assigned learners."""
    service = _get_service(request)
    try:
        return service.publish_quiz(str(current_user["_id"]), quiz_id)
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/quizzes/{quiz_id}/assign", response_model=TrainerQuizAssignResponse)
def assign_trainer_quiz(
    request: Request,
    quiz_id: str,
    payload: TrainerQuizAssignRequest,
    current_user: CurrentTrainer,
) -> dict:
    """Assign a published quiz to one or more learners."""
    service = _get_service(request)
    try:
        return service.assign_quiz(
            trainer_id=str(current_user["_id"]),
            quiz_id=quiz_id,
            learner_ids=payload.learner_ids,
        )
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =============================================================================
# Learner Evaluation & Feedback
# =============================================================================

@router.get("/quizzes/{quiz_id}/attempts", response_model=list[TrainerLearnerAttemptResponse])
def list_quiz_attempts(
    request: Request,
    quiz_id: str,
    current_user: CurrentTrainer,
) -> list[dict]:
    """List all learner attempts and scores for a specific quiz."""
    service = _get_service(request)
    try:
        return service.list_quiz_attempts(str(current_user["_id"]), quiz_id)
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/learners", response_model=list[TrainerLearnerSummary])
def list_assigned_learners(
    request: Request,
    current_user: CurrentTrainer,
) -> list[dict]:
    """List all learners assigned to trainer's quizzes with summary progress."""
    service = _get_service(request)
    return service.list_assigned_learners(str(current_user["_id"]))


@router.get("/learners/{learner_id}/results")
def get_learner_evaluation(
    request: Request,
    learner_id: str,
    current_user: CurrentTrainer,
) -> dict:
    """View complete history and understanding for a specific learner."""
    service = _get_service(request)
    try:
        return service.get_learner_results(str(current_user["_id"]), learner_id)
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/attempts/{attempt_id}/feedback")
def submit_learner_feedback(
    request: Request,
    attempt_id: str,
    payload: TrainerFeedbackRequest,
    current_user: CurrentTrainer,
) -> dict:
    """Submit qualitative feedback and strengths/improvement notes on a learner's quiz attempt."""
    service = _get_service(request)
    try:
        return service.submit_feedback(
            trainer_id=str(current_user["_id"]),
            attempt_id=attempt_id,
            feedback_text=payload.feedback_text,
            strengths=payload.strengths,
            areas_for_improvement=payload.areas_for_improvement,
            rating=payload.rating,
        )
    except TrainerServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
