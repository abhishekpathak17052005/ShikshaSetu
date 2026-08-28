"""API router for learning resources and recommendations."""

from typing import Optional, List
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.learning_resources.service import RecommendationService
from app.learning_resources.models import RecommendationResponse, LearningRecommendation

router = APIRouter(prefix="/recommendations", tags=["learning-resources"])


@router.get("/me", response_model=RecommendationResponse)
def get_my_recommendations(
    request: Request,
    current_user: dict = Depends(get_current_user),
    limit: Optional[int] = None,
) -> RecommendationResponse:
    """
    Get personalized learning recommendations for authenticated user.

    Uses the user's skill gaps and role to generate ranked recommendations.

    Query Parameters:
        limit: Maximum number of recommendations to return (default: None = all)

    Returns:
        RecommendationResponse with ranked recommendations and explanations

    Raises:
        401: Not authenticated
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    service = RecommendationService(database)
    return service.get_recommendations_for_user(
        user_id=str(current_user["_id"]),
        limit=limit,
    )


class ResourceDetailsResponse(BaseModel):
    """Response for resource details."""
    resource_id: str
    title: str
    provider: str
    resource_type: str
    metadata: dict
    source: dict


@router.get("/resources/{resource_id}", response_model=dict)
def get_resource_details(
    request: Request,
    resource_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get detailed information about a specific learning resource.

    Path Parameters:
        resource_id: The resource ID (e.g., "IGOT-12345", "NSSTA-PROTO-xxx")

    Returns:
        Complete resource document with metadata

    Raises:
        401: Not authenticated
        404: Resource not found
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    service = RecommendationService(database)
    resource = service.get_resource_details(resource_id)

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Convert MongoDB document to dict, handling ObjectIds
    return {
        "resource_id": resource.get("resource_id"),
        "title": resource.get("title"),
        "provider": resource.get("provider"),
        "resource_type": resource.get("resource_type"),
        "metadata": resource.get("metadata"),
        "source": resource.get("source"),
        "provider_specific": resource.get("provider_specific"),
        "status": resource.get("status"),
    }


class CompetencyResourcesResponse(BaseModel):
    """Response for resources by competency."""
    competency_code: str
    total_resources: int
    resources: List[dict]


@router.get("/competencies/{competency_code}/resources", response_model=dict)
def get_resources_by_competency(
    request: Request,
    competency_code: str,
    provider: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get all learning resources mapped to a competency.

    Path Parameters:
        competency_code: The competency code (e.g., "STAT-SAMPLING")

    Query Parameters:
        provider: Filter by provider ("IGOT" or "NSSTA", default: None = all)

    Returns:
        List of resources with their metadata

    Raises:
        401: Not authenticated
        404: Competency not found or has no resources
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    service = RecommendationService(database)
    resources = service.get_resources_by_competency(competency_code, provider)

    if not resources:
        raise HTTPException(
            status_code=404,
            detail=f"No resources found for competency {competency_code}",
        )

    return {
        "competency_code": competency_code,
        "provider_filter": provider,
        "total_resources": len(resources),
        "resources": [
            {
                "resource_id": r.get("resource_id"),
                "title": r.get("title"),
                "provider": r.get("provider"),
                "resource_type": r.get("resource_type"),
                "source": r.get("source"),
            }
            for r in resources
        ],
    }


class UnmappedResourcesResponse(BaseModel):
    """Response for unmapped resources."""
    total_resources: int
    resources: List[dict]


@router.get("/resources/unmapped", response_model=dict)
def get_unmapped_resources(
    request: Request,
    provider: Optional[str] = None,
    limit: Optional[int] = 10,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get learning resources with no competency mappings (browseable only).

    Query Parameters:
        provider: Filter by provider ("IGOT" or "NSSTA", default: None = all)
        limit: Maximum number to return (default: 10)

    Returns:
        List of unmapped resources

    Raises:
        401: Not authenticated
        503: Database unavailable
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    service = RecommendationService(database)
    resources = service.get_unmapped_resources(provider=provider, limit=limit)

    return {
        "provider_filter": provider,
        "total_resources": len(resources),
        "resources": [
            {
                "resource_id": r.get("resource_id"),
                "title": r.get("title"),
                "provider": r.get("provider"),
                "resource_type": r.get("resource_type"),
            }
            for r in resources
        ],
    }
