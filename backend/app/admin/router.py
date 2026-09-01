from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pymongo.database import Database

from app.admin import schemas, service
from app.auth.dependencies import require_admin_role

router = APIRouter(
    prefix="/admin",
    tags=["Admin Organizational Intelligence"],
    dependencies=[Depends(require_admin_role)],
)


def _get_db(request: Request) -> Database:
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return db


@router.get(
    "/dashboard",
    response_model=schemas.AdminDashboardResponse,
    summary="Get executive admin dashboard metrics",
)
def get_dashboard(
    request: Request,
    department: Optional[str] = Query(None, description="Filter metrics by department"),
) -> schemas.AdminDashboardResponse:
    db = _get_db(request)
    return service.get_admin_dashboard(db, department=department)


@router.get(
    "/workforce",
    response_model=schemas.WorkforceOverviewResponse,
    summary="Get workforce breakdown and capability distribution",
)
def get_workforce(
    request: Request,
    department: Optional[str] = Query(None, description="Filter workforce by department"),
) -> schemas.WorkforceOverviewResponse:
    db = _get_db(request)
    return service.get_workforce_overview(db, department=department)


@router.get(
    "/competencies",
    response_model=schemas.CompetencyAnalyticsResponse,
    summary="Get organization-wide competency analytics",
)
def get_competencies(
    request: Request,
    department: Optional[str] = Query(None, description="Filter competency analytics by department"),
) -> schemas.CompetencyAnalyticsResponse:
    db = _get_db(request)
    return service.get_competency_analytics(db, department=department)


@router.get(
    "/skill-gaps",
    response_model=schemas.SkillGapAnalyticsResponse,
    summary="Get organization-wide skill gap analytics",
)
def get_skill_gaps(
    request: Request,
    department: Optional[str] = Query(None, description="Filter skill gap analytics by department"),
) -> schemas.SkillGapAnalyticsResponse:
    db = _get_db(request)
    return service.get_skill_gap_analytics(db, department=department)


@router.get(
    "/training-effectiveness",
    response_model=schemas.TrainingEffectivenessResponse,
    summary="Get training effectiveness and evidence metrics",
)
def get_training_effectiveness(request: Request) -> schemas.TrainingEffectivenessResponse:
    db = _get_db(request)
    return service.get_training_effectiveness(db)


@router.get(
    "/emerging-skills",
    response_model=schemas.EmergingSkillsResponse,
    summary="Get emerging skill requirements and strategic capability needs",
)
def get_emerging_skills(request: Request) -> schemas.EmergingSkillsResponse:
    db = _get_db(request)
    return service.get_emerging_skills(db)


@router.get(
    "/capacity-planning",
    response_model=schemas.CapacityPlanningResponse,
    summary="Get organizational capacity planning recommendations",
)
def get_capacity_planning(request: Request) -> schemas.CapacityPlanningResponse:
    db = _get_db(request)
    return service.get_capacity_planning(db)


@router.get(
    "/users",
    response_model=schemas.AdminUserListResponse,
    summary="Get organizational user directory",
)
def get_users(
    request: Request,
    department: Optional[str] = Query(None, description="Filter users by department"),
) -> schemas.AdminUserListResponse:
    db = _get_db(request)
    return service.get_admin_users(db, department=department)


@router.get(
    "/reports",
    response_model=schemas.AdminReportsResponse,
    summary="Get consolidated intelligence reports",
)
def get_reports(request: Request) -> schemas.AdminReportsResponse:
    db = _get_db(request)
    return service.get_admin_reports(db)

