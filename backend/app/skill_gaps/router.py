"""
API router for skill gaps.

Endpoints:
  GET /api/v1/skill-gaps/me
"""

from fastapi import APIRouter, Depends, Request

from app.auth.dependencies import get_current_user
from app.skill_gaps import service
from app.skill_gaps.schemas import SkillGapResponse

router = APIRouter(prefix="/skill-gaps", tags=["skill-gaps"])


@router.get("/me", response_model=SkillGapResponse)
def get_my_skill_gaps(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> SkillGapResponse:
    """
    Get skill gaps for authenticated employee.
    
    Returns:
        SkillGapResponse with role, summary, and sorted gaps
    
    Raises:
        422: User does not have a professional role
        404: Role has no competency requirements
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    return service.calculate_skill_gaps(database, str(current_user["_id"]))
