from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.assessments import service
from app.assessments.schemas import (
    AssessmentAttemptResponse,
    AssessmentConfigurationResponse,
    AssessmentSubmissionResponse,
    CapabilityAssessmentRequest,
    StartAssessmentRequest,
    SubmitAssessmentRequest,
)
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])
CurrentUser = Annotated[dict, Depends(get_current_user)]


# Capability Assessment Configuration Endpoints (MUST come before /{attempt_id} to avoid ambiguity)

@router.get("/configs", response_model=list[AssessmentConfigurationResponse])
def list_assessment_configurations(request: Request) -> list[dict]:
    """List all active assessment configurations."""
    return service.get_all_assessment_configurations(getattr(request.app.state, "database", None))


@router.get("/configs/{competency_code}", response_model=AssessmentConfigurationResponse)
def get_assessment_configuration(request: Request, competency_code: str) -> dict:
    """Get assessment configuration for a specific competency."""
    return service.get_assessment_configuration(getattr(request.app.state, "database", None), competency_code)


# Assessment Attempt Endpoints

@router.post("", response_model=AssessmentAttemptResponse, status_code=201)
def start_assessment(request: Request, payload: StartAssessmentRequest, current_user: CurrentUser) -> dict:
    return service.start_assessment(getattr(request.app.state, "database", None), str(current_user["_id"]), payload.assessment_key)


@router.get("/{attempt_id}", response_model=AssessmentAttemptResponse)
def get_assessment_attempt(request: Request, attempt_id: str, current_user: CurrentUser) -> dict:
    return service.get_attempt(getattr(request.app.state, "database", None), str(current_user["_id"]), attempt_id)


@router.post("/{attempt_id}/submit", response_model=AssessmentSubmissionResponse)
def submit_assessment(request: Request, attempt_id: str, payload: SubmitAssessmentRequest, current_user: CurrentUser) -> dict:
    return service.submit_assessment(getattr(request.app.state, "database", None), str(current_user["_id"]), attempt_id, payload)
