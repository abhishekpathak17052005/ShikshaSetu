"""Router for capability assessment endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.capability_assessments import service
from app.capability_assessments.schemas import (
    CapabilityAssessmentCreateRequest,
    CapabilityAssessmentListResponse,
    CapabilityAssessmentResponse,
    CapabilityAssessmentResultsResponse,
    CapabilityAssessmentSubmitRequest,
    CapabilityAssessmentSubmitResponse,
)

router = APIRouter(prefix="/api/v1/assessments/capability", tags=["Capability Assessments"])


@router.post(
    "",
    response_model=CapabilityAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a capability assessment",
    description="Create a new capability assessment for a competency. Loads questions from question bank based on configuration.",
)
def create_capability_assessment(
    request: Request,
    payload: CapabilityAssessmentCreateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Create a new capability assessment.
    
    Requires:
    - JWT authentication
    - Valid competency_code
    - Assessment configuration exists for competency
    
    Returns:
    - Assessment with questions (no answer keys)
    - Status IN_PROGRESS
    """
    database = request.app.state.database
    return service.create_capability_assessment(
        database,
        str(current_user["_id"]),
        payload.competency_code
    )


@router.get(
    "/{assessment_id}",
    response_model=CapabilityAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a capability assessment",
    description="Retrieve an in-progress or submitted assessment. Does not expose answer keys.",
)
def get_capability_assessment(
    request: Request,
    assessment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Retrieve a capability assessment.
    
    Requires:
    - JWT authentication
    - User owns the assessment
    
    Returns:
    - Assessment details (questions without answers)
    - Current status and scores (if submitted)
    """
    database = request.app.state.database
    return service.get_capability_assessment(
        database,
        str(current_user["_id"]),
        assessment_id
    )


@router.post(
    "/{assessment_id}/submit",
    response_model=CapabilityAssessmentSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit assessment answers",
    description="Submit answers for a capability assessment. Server-side scoring, evidence creation, and competency profile update.",
)
def submit_capability_assessment(
    request: Request,
    assessment_id: str,
    payload: CapabilityAssessmentSubmitRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Submit answers for a capability assessment.
    
    Requires:
    - JWT authentication
    - User owns the assessment
    - Assessment status is IN_PROGRESS
    
    Operations:
    - Validates all answers provided
    - Server-side scoring (no client scores trusted)
    - Creates evidence record (append-only)
    - Updates competency profile
    - Prevents duplicate submission (atomic check)
    
    Returns:
    - Final scores and normalized competency level
    - Confidence in result
    - Before/after competency comparison available via GET results
    """
    database = request.app.state.database
    
    # Convert payload to list of dicts
    answers = [
        {
            "question_id": a.question_id,
            "selected_answer": a.selected_answer,
        }
        for a in payload.answers
    ]
    
    return service.submit_capability_assessment(
        database,
        str(current_user["_id"]),
        assessment_id,
        answers
    )


@router.get(
    "/{assessment_id}/results",
    response_model=CapabilityAssessmentResultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get assessment results",
    description="Retrieve detailed results of a submitted assessment.",
)
def get_capability_assessment_results(
    request: Request,
    assessment_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """
    Get results of a submitted assessment.
    
    Requires:
    - JWT authentication
    - User owns the assessment
    - Assessment has been submitted
    
    Returns:
    - Full results including scores, answers summary, competency impact
    """
    database = request.app.state.database
    return service.get_capability_assessment_results(
        database,
        str(current_user["_id"]),
        assessment_id
    )


@router.get(
    "",
    response_model=list[CapabilityAssessmentListResponse],
    status_code=status.HTTP_200_OK,
    summary="List user's capability assessments",
    description="List all capability assessments for the current user.",
)
def list_user_capability_assessments(
    request: Request,
    competency_code: str | None = None,
    status_filter: str | None = None,
    limit: int = 100,
    current_user: Annotated[dict, Depends(get_current_user)] = ...,
) -> list[dict]:
    """
    List capability assessments for current user.
    
    Requires:
    - JWT authentication
    
    Query Parameters:
    - competency_code: Filter by competency (optional)
    - status_filter: Filter by status IN_PROGRESS|SUBMITTED (optional)
    - limit: Maximum results (default 100)
    
    Returns:
    - List of assessment summaries sorted by creation date (newest first)
    """
    database = request.app.state.database
    return service.list_user_capability_assessments(
        database,
        str(current_user["_id"]),
        competency_code,
        status_filter,
        limit
    )
