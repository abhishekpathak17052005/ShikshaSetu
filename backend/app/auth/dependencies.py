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


def require_role(*roles: AccessRole | str):
    """Dependency factory enforcing that current_user has one of the allowed access_roles."""
    allowed_values = set()
    for r in roles:
        val = r.value if isinstance(r, AccessRole) else str(r)
        allowed_values.add(val)
        if val in ("OFFICIAL", AccessRole.OFFICIAL.value):
            allowed_values.add("EMPLOYEE")

    def dependency(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
        user_role = current_user.get("access_role")
        if user_role not in allowed_values:
            role_names = [r.value if isinstance(r, AccessRole) else str(r) for r in roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: required role in {role_names}",
            )
        return current_user

    return dependency


def require_official(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """Allows OFFICIAL (and legacy EMPLOYEE), TRAINER, and ADMIN users to access learner/official workflows."""
    return current_user


def require_trainer(
    current_user: Annotated[
        dict,
        Depends(require_role(AccessRole.TRAINER, AccessRole.ADMIN)),
    ],
) -> dict:
    """Enforces that user is either a TRAINER or an ADMIN."""
    return current_user


def require_admin(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """Legacy and standard admin check: user must be ADMIN."""
    if current_user.get("access_role") != AccessRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_admin_role(
    current_user: Annotated[
        dict,
        Depends(require_role(AccessRole.ADMIN)),
    ],
) -> dict:
    """Standard role-based admin check: user must be ADMIN."""
    return current_user

