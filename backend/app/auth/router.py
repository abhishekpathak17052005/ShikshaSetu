from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import get_current_user
from app.auth.schemas import AccessRole, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.users import repository

router = APIRouter(prefix="/auth", tags=["authentication"])


def public_user(document: dict) -> dict:
    result = {key: value for key, value in document.items() if key != "password_hash"}
    result["id"] = str(result.pop("_id"))
    result["role_id"] = str(result["role_id"])
    return result


def database_or_error(request: Request):
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    return database


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, payload: RegisterRequest) -> dict:
    database = database_or_error(request)
    from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies

    # If role_id explicitly provided, validate it exists; otherwise resolve from department + designation
    if payload.role_id:
        role_oid = repository.object_id(payload.role_id)
        if not role_oid or not repository.role_exists(database, payload.role_id):
            raise HTTPException(status_code=422, detail="role_id must reference an active role")
    else:
        role_oid = resolve_role_for_user(database, payload.department, payload.designation)
        if not role_oid:
            raise HTTPException(status_code=422, detail="Unable to resolve an active role for the specified department and designation")


    if repository.get_user_by_email(database, str(payload.email)) is not None:
        raise HTTPException(status_code=409, detail="Registration could not be completed")

    if payload.access_role == AccessRole.ADMIN or str(payload.access_role).strip().upper() == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin registration is restricted and must be provisioned by an administrator",
        )

    if payload.access_role == AccessRole.TRAINER or str(payload.access_role).strip().upper() == "TRAINER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trainer registration is restricted and must be provisioned by an administrator",
        )

    access_role_value = AccessRole.OFFICIAL.value

    timestamp = datetime.now(UTC)
    document = {
        "email": str(payload.email),
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "role_id": role_oid,
        "designation": payload.designation,
        "department": payload.department,
        "employee_id": payload.employee_id,
        "status": "active",
        "access_role": access_role_value,
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_login_at": None,
    }
    try:
        inserted_id = repository.insert_user(database, document)
        reconcile_user_competencies(database, inserted_id, role_oid)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Registration could not be completed") from None
    return public_user(document)



@router.post("/login", response_model=TokenResponse)
def login(request: Request, payload: LoginRequest) -> dict:
    database = database_or_error(request)
    user = repository.get_user_by_email(database, str(payload.email))
    if user is None or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.get("status") != "active":
        raise HTTPException(status_code=401, detail="Invalid email or password")

    from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies
    resolved_role_oid = resolve_role_for_user(database, user.get("department"), user.get("designation"))
    if resolved_role_oid and resolved_role_oid != user.get("role_id"):
        repository.update_user(database, str(user["_id"]), {"role_id": resolved_role_oid})
        reconcile_user_competencies(database, user["_id"], resolved_role_oid)
        user["role_id"] = resolved_role_oid

    updated_user = repository.update_last_login(database, str(user["_id"]), datetime.now(UTC)) or user
    token = create_access_token(str(updated_user["_id"]), request.app.state.settings)
    return {"access_token": token, "token_type": "bearer", "user": public_user(updated_user)}



@router.get("/me", response_model=UserResponse)
def current_user(current_user: dict = Depends(get_current_user)) -> dict:
    return public_user(current_user)
