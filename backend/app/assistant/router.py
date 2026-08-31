"""FastAPI router for the AI Virtual Capability Assistant."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
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
def chat_with_copilot(
    payload: AssistantChatRequest,
    current_user: dict = Depends(get_current_user),
    service: AssistantService = Depends(get_assistant_service),
) -> AssistantChatResponse:
    """
    Conversational capability advisor grounded in user's real competency state,
    skill gaps, recommended courses, and curriculum RAG chunks.
    """
    user_id = str(current_user["_id"])
    return service.process_chat(user_id=user_id, request=payload)
