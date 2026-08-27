from fastapi import APIRouter, Request

from app.competencies import service
from app.competencies.schemas import RoleRequirementResponse, RoleResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
def get_roles(request: Request) -> list[dict]:
    return service.list_roles(getattr(request.app.state, "database", None))


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(request: Request, role_id: str) -> dict:
    return service.get_role(getattr(request.app.state, "database", None), role_id)


@router.get("/{role_id}/requirements", response_model=list[RoleRequirementResponse])
def get_role_requirements(request: Request, role_id: str) -> list[dict]:
    return service.list_role_requirements(getattr(request.app.state, "database", None), role_id)
