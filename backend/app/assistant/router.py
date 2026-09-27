"""FastAPI router for the AI Virtual Capability Assistant."""

from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.limiter import limiter
from .service import AssistantService
from .schemas import AssistantChatRequest, AssistantChatResponse

router = APIRouter(prefix="/assistant", tags=["Virtual Capability Assistant"])


def _get_db(request: Request) -> Database:
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return db


def get_assistant_service(request: Request) -> AssistantService:
    database = _get_db(request)
    settings = getattr(request.app.state, "settings", None) or get_settings()
    return AssistantService(database, settings)


@router.post("/chat", response_model=AssistantChatResponse)
@limiter.limit("30/minute")
def chat_with_copilot(
    request: Request,
    payload: AssistantChatRequest,
    current_user: dict = Depends(get_current_user),
    service: AssistantService = Depends(get_assistant_service),
) -> AssistantChatResponse:
    """
    Conversational capability advisor grounded in user's real competency state,
    skill gaps, recommended courses, and curriculum RAG chunks.
    Deterministic queries (gaps, recommendations) use fast backend data.
    """
    user_id = str(current_user["_id"])
    return service.process_chat(user_id=user_id, request=payload)


@router.post("/chat/stream")
@limiter.limit("30/minute")
def stream_chat_with_copilot(
    request: Request,
    payload: AssistantChatRequest,
    current_user: dict = Depends(get_current_user),
    service: AssistantService = Depends(get_assistant_service),
) -> StreamingResponse:
    """
    Server-Sent Events (SSE) streaming endpoint for the Karmayogi AI Co-Pilot.
    Yields progressive status events, text chunk deltas, and the final response.
    """
    user_id = str(current_user["_id"])
    return StreamingResponse(
        service.stream_chat(user_id=user_id, request=payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class FeedbackRequest(BaseModel):
    """User-scoped feedback for improving retrieved assistant answers."""

    session_id: str = Field(..., description="The chat session or message identifier")
    query: str = Field(..., description="The original user query")
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    final_answer: str = Field(default="")
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)
    thumbs_up: Optional[bool] = Field(default=None)
    flagged_hallucination: bool = Field(default=False)
    flagged_reason: Optional[str] = Field(default=None)


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Append bounded, user-scoped assistant feedback to the retrieval log."""
    db = _get_db(request)
    doc = {
        "user_id": str(current_user["_id"]),
        "session_id": payload.session_id,
        "query": payload.query,
        "retrieved_chunk_ids": payload.retrieved_chunk_ids,
        "final_answer": payload.final_answer[:500],
        "user_rating": payload.user_rating,
        "thumbs_up": payload.thumbs_up,
        "flagged_hallucination": payload.flagged_hallucination,
        "flagged_reason": payload.flagged_reason,
        "timestamp": datetime.now(UTC),
        "resolved": False,
        "resolution_notes": None,
    }
    try:
        result = db.rag_feedback.insert_one(doc)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record feedback",
        ) from exc
    return {"status": "recorded", "feedback_id": str(result.inserted_id)}
