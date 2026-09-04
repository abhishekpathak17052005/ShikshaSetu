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


@router.get("/{session_id}/status")
def get_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    service: AdaptiveAssessmentService = Depends(get_service),
) -> dict:
    """
    Returns the current status of an assessment session.
    Used for resume-on-refresh support.
    """
    from bson import ObjectId
    user_id = str(current_user["_id"])
    db = service.db
    user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
    sess_oid = ObjectId(session_id) if ObjectId.is_valid(session_id) else None
    if not user_oid or not sess_oid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid IDs")

    session = db.adaptive_assessment_sessions.find_one(
        {"_id": sess_oid, "user_id": user_oid}
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    current_q = session.get("current_question")
    q_item = None
    if current_q and session.get("status") == "IN_PROGRESS":
        from .service import AdaptiveAssessmentService as S
        svc = service
        q_item = svc._format_question_item(current_q)

    from .calibration import map_theta_to_difficulty, map_theta_to_level_label
    theta = session.get("current_estimated_level", 2.5)
    return {
        "session_id": str(session["_id"]),
        "status": session.get("status", "IN_PROGRESS"),
        "competency_code": session.get("competency_code", ""),
        "competency_name": session.get("competency_name", ""),
        "estimated_level": theta,
        "difficulty": map_theta_to_difficulty(theta),
        "proficiency_tier": map_theta_to_level_label(theta),
        "questions_completed": session.get("questions_attempted", 0),
        "total_questions_planned": session.get("max_questions", 5),
        "current_question_number": session.get("questions_attempted", 0) + 1,
        "current_question": q_item.model_dump() if q_item else None,
    }



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


