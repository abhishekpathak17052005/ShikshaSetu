import logging

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request) -> HealthResponse:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )

    try:
        database.command("ping")
    except PyMongoError:
        logger.warning("MongoDB health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None

    return HealthResponse(
        status="ok",
        service=request.app.title,
        database="connected",
    )
