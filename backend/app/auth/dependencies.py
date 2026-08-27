from typing import Annotated

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.database import Database

from app.auth.schemas import AccessRole
from app.auth.security import decode_access_token
from app.users.repository import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        settings = getattr(request.app.state, "settings", None)
        if settings is None:
            raise ValueError("Authentication settings are unavailable")
        user_id = decode_access_token(credentials.credentials, settings)
    except ValueError:
        raise authentication_error() from None

    database: Database | None = getattr(request.app.state, "database", None)
    user = get_user_by_id(database, user_id) if database is not None else None
    if user is None or user.get("status") != "active":
        raise authentication_error()
    return user


def require_admin(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if current_user.get("access_role") != AccessRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
