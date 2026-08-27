from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import get_current_user
from app.auth.router import public_user
from app.auth.schemas import UserProfileUpdate, UserResponse
from app.users import repository

router = APIRouter(prefix="/users", tags=["users"])


def update_profile(request: Request, current_user: dict, payload: UserProfileUpdate) -> dict:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return public_user(current_user)
    updates["updated_at"] = datetime.now(UTC)
    try:
        updated_user = repository.update_user(database, str(current_user["_id"]), updates)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Profile update could not be completed") from None
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return public_user(updated_user)


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return public_user(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    request: Request,
    payload: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return update_profile(request, current_user, payload)
