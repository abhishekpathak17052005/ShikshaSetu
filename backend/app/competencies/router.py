from fastapi import APIRouter, Request

from app.competencies import service
from app.competencies.schemas import CompetencyResponse

router = APIRouter(prefix="/competencies", tags=["competencies"])


@router.get("", response_model=list[CompetencyResponse])
def get_competencies(request: Request) -> list[dict]:
    return service.list_competencies(getattr(request.app.state, "database", None))


@router.get("/{competency_id}", response_model=CompetencyResponse)
def get_competency(request: Request, competency_id: str) -> dict:
    return service.get_competency(getattr(request.app.state, "database", None), competency_id)
