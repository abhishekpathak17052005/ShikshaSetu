"""API router for learning activities."""

from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException

from app.auth.dependencies import get_current_user
from app.learning_activities import service
from app.learning_activities.schemas import (
    LearningActivityCreate,
    LearningActivityUpdate,
    LearningActivityComplete,
    LearningActivityResponse,
    LearningActivityListResponse,
    LearningActivityCompleteResponse,
)

router = APIRouter(prefix="/learning-activities", tags=["learning-activities"])


@router.post("", response_model=LearningActivityResponse)
def start_learning_activity(
    request: Request,
    body: LearningActivityCreate,
    current_user: dict = Depends(get_current_user),
) -> LearningActivityResponse:
    """
    Start a new learning activity for the authenticated user.

    Request Body:
        resource_id: ID of the learning resource to start
        competency_id: Competency this resource addresses

    Returns:
        LearningActivityResponse with activity details

    Raises:
        401: Not authenticated
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_id = str(current_user["_id"])
    
    activity = service.start_learning_activity(
        database,
        user_id=user_id,
        resource_id=body.resource_id,
        competency_id=body.competency_id,
    )
    
    return activity


@router.get("", response_model=LearningActivityListResponse)
def list_learning_activities(
    request: Request,
    status: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
) -> LearningActivityListResponse:
    """
    List authenticated user's learning activities.

    Query Parameters:
        status: Filter by status (in_progress, completed, abandoned)
        limit: Maximum number to return (default: 100)

    Returns:
        List of user's learning activities

    Raises:
        401: Not authenticated
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_id = str(current_user["_id"])
    
    activities = service.list_user_activities(
        database,
        user_id=user_id,
        status=status,
        limit=limit,
    )
    
    return LearningActivityListResponse(
        activities=activities,
        total_count=len(activities),
    )


@router.get("/{activity_id}", response_model=LearningActivityResponse)
def get_learning_activity(
    request: Request,
    activity_id: str,
    current_user: dict = Depends(get_current_user),
) -> LearningActivityResponse:
    """
    Get details of a specific learning activity.

    Path Parameters:
        activity_id: The activity ID

    Returns:
        Activity details

    Raises:
        401: Not authenticated
        404: Activity not found
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_id = str(current_user["_id"])
    
    try:
        activity = service.get_learning_activity_details(
            database,
            activity_id=activity_id,
            user_id=user_id,
        )
        return activity
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Activity {activity_id} not found or unauthorized",
        )


@router.put("/{activity_id}", response_model=LearningActivityResponse)
def update_learning_activity(
    request: Request,
    activity_id: str,
    body: LearningActivityUpdate,
    current_user: dict = Depends(get_current_user),
) -> LearningActivityResponse:
    """
    Update progress on a learning activity.

    Path Parameters:
        activity_id: The activity ID

    Request Body:
        progress_percent: Learning progress (0-100)
        duration_minutes: Time spent learning
        notes: Optional notes

    Returns:
        Updated activity details

    Raises:
        401: Not authenticated
        404: Activity not found
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_id = str(current_user["_id"])
    
    try:
        activity = service.update_learning_activity(
            database,
            activity_id=activity_id,
            user_id=user_id,
            progress_percent=body.progress_percent,
            duration_minutes=body.duration_minutes,
            notes=body.notes,
        )
        return activity
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{activity_id}/complete", response_model=LearningActivityCompleteResponse)
def complete_learning_activity(
    request: Request,
    activity_id: str,
    body: LearningActivityComplete,
    current_user: dict = Depends(get_current_user),
) -> LearningActivityCompleteResponse:
    """
    Mark a learning activity as complete and generate evidence.

    Path Parameters:
        activity_id: The activity ID

    Request Body:
        final_score: Optional final assessment score (0-100)
        notes: Optional completion notes

    Returns:
        Completion result with competency and gap updates

    Raises:
        401: Not authenticated
        404: Activity not found
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user_id = str(current_user["_id"])
    
    try:
        result = service.complete_learning_activity(
            database,
            activity_id=activity_id,
            user_id=user_id,
            final_score=body.final_score,
            notes=body.notes,
        )
        
        return LearningActivityCompleteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
