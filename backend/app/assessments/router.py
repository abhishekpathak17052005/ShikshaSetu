from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.assessments import service
from app.assessments.schemas import AssessmentAttemptResponse, AssessmentSubmissionResponse, StartAssessmentRequest, SubmitAssessmentRequest
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])
CurrentUser = Annotated[dict, Depends(get_current_user)]


@router.post("", response_model=AssessmentAttemptResponse, status_code=201)
def start_assessment(request: Request, payload: StartAssessmentRequest, current_user: CurrentUser) -> dict:
    return service.start_assessment(getattr(request.app.state, "database", None), str(current_user["_id"]), payload.assessment_key)


@router.get("/{attempt_id}", response_model=AssessmentAttemptResponse)
def get_assessment_attempt(request: Request, attempt_id: str, current_user: CurrentUser) -> dict:
    return service.get_attempt(getattr(request.app.state, "database", None), str(current_user["_id"]), attempt_id)


@router.post("/{attempt_id}/submit", response_model=AssessmentSubmissionResponse)
def submit_assessment(request: Request, attempt_id: str, payload: SubmitAssessmentRequest, current_user: CurrentUser) -> dict:
    return service.submit_assessment(getattr(request.app.state, "database", None), str(current_user["_id"]), attempt_id, payload)
