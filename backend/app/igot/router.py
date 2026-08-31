from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from .service import IGOTEcosystemService
from .schemas import (
    IGOTEcosystemStatusResponse,
    IGOTCourseListResponse,
)

router = APIRouter(prefix="/igot", tags=["iGOT Karmayogi Ecosystem"])


def _get_db(request: Request):
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return db


def get_service(request: Request) -> IGOTEcosystemService:
    database = _get_db(request)
    settings = getattr(request.app.state, "settings", None) or get_settings()
    return IGOTEcosystemService(database, settings)


@router.get("/status", response_model=IGOTEcosystemStatusResponse)
def get_igot_status(
    service: IGOTEcosystemService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
) -> IGOTEcosystemStatusResponse:
    """Get the connection and indexing health of the iGOT Karmayogi ecosystem."""
    return service.get_ecosystem_status()


@router.get("/courses", response_model=IGOTCourseListResponse)
def list_igot_courses(
    competency: Optional[str] = Query(None, description="Filter by competency code (e.g., TECH_PYTHON)"),
    search: Optional[str] = Query(None, description="Search courses by keyword in title"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: IGOTEcosystemService = Depends(get_service),
    current_user: dict = Depends(get_current_user),
) -> IGOTCourseListResponse:
    """List indexed iGOT courses mapped to the National Competency Framework."""
    return service.list_courses(
        competency_code=competency,
        search_query=search,
        page=page,
        limit=limit,
    )
