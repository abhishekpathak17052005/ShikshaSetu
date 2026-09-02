"""FastAPI Router for the Adaptive Capability Assessment Engine."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.database import Database

from app.auth.dependencies import get_current_user
from .schemas import (
    AdaptiveStartRequest,
    AdaptiveStartResponse,
    AdaptiveAnswerRequest,
    AdaptiveAnswerResponse,
    AdaptiveFinalizeResponse,
)
from .service import AdaptiveAssessmentService

router = APIRouter(prefix="/adaptive-assessments", tags=["Adaptive Capability Assessments"])


def _get_db(request: Request) -> Database:
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return db


def get_service(request: Request) -> AdaptiveAssessmentService:
    database = _get_db(request)
    return AdaptiveAssessmentService(database)


@router.post("/start", response_model=AdaptiveStartResponse)
def start_adaptive_assessment(
    payload: AdaptiveStartRequest,
    current_user: dict = Depends(get_current_user),
    service: AdaptiveAssessmentService = Depends(get_service),
) -> AdaptiveStartResponse:
    """Initializes an adaptive assessment session calibrated against the civil services competency taxonomy."""
    user_id = str(current_user["_id"])
    return service.start_session(user_id=user_id, request=payload)


@router.post("/{session_id}/answer", response_model=AdaptiveAnswerResponse)
def submit_adaptive_answer(
    session_id: str,
    payload: AdaptiveAnswerRequest,
    current_user: dict = Depends(get_current_user),
    service: AdaptiveAssessmentService = Depends(get_service),
) -> AdaptiveAnswerResponse:
    """Processes an answer, computes calibrated step-up/down capability theta, and returns the next adaptive question."""
    user_id = str(current_user["_id"])
    return service.submit_answer(user_id=user_id, session_id=session_id, request=payload)


@router.get("/history")
def get_adaptive_assessment_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Retrieves all completed adaptive assessments for the current user."""
    db = _get_db(request)
    from bson import ObjectId
    user_oid = current_user["_id"] if isinstance(current_user["_id"], ObjectId) else ObjectId(str(current_user["_id"]))
    user_str = str(current_user["_id"])

    cursor = db.adaptive_assessment_sessions.find({
        "$or": [{"user_id": user_oid}, {"user_id": user_str}],
        "status": "COMPLETED",
    }).sort("completed_at", -1)

    comp_docs = list(db.competencies.find())
    comp_map = {str(c["_id"]): c.get("name", "") for c in comp_docs}
    comp_code_map = {c.get("code", ""): c.get("name", "") for c in comp_docs}

    results = []
    for doc in cursor:
        c_code = doc.get("competency_code", "")
        c_name = doc.get("competency_name") or comp_code_map.get(c_code) or comp_map.get(str(doc.get("competency_id")), c_code)
        results.append({
            "session_id": str(doc["_id"]),
            "competency_code": c_code,
            "competency_name": c_name,
            "final_score": float(doc.get("final_score", 3.0)),
            "accuracy_pct": float(doc.get("accuracy_pct", 100.0)),
            "completed_at": doc.get("completed_at"),
            "status": doc.get("status", "COMPLETED"),
        })
    return results


@router.post("/{session_id}/finalize", response_model=AdaptiveFinalizeResponse)
def finalize_adaptive_assessment(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: AdaptiveAssessmentService = Depends(get_service),
) -> AdaptiveFinalizeResponse:
    """
    Finalizes the adaptive assessment:
    1. Records Authoritative Evidence (0.85).
    2. Updates official Competency Profile.
    3. Recalculates Skill Gaps.
    """
    user_id = str(current_user["_id"])
    return service.finalize_session(user_id=user_id, session_id=session_id)


