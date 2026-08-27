"""
Service layer for skill gap calculation.

Orchestrates repository queries + engine calculations.
"""

from fastapi import HTTPException, status
from pymongo.database import Database

from app.skill_gaps import engine, repository
from app.skill_gaps.schemas import SkillGapResponse, SkillGapSummary


def get_database(database: Database | None) -> Database:
    """Ensure database is available."""
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return database


def calculate_skill_gaps(database: Database | None, user_id: str) -> SkillGapResponse:
    """
    Calculate skill gaps for authenticated user.
    
    Core logic:
    1. Get user's professional role
    2. Get role's competency requirements
    3. Get user's current competency profiles
    4. Calculate gap for each requirement
    5. Sort by priority
    6. Return response
    
    Args:
        database: MongoDB database
        user_id: Authenticated user's ObjectId as string
    
    Returns:
        SkillGapResponse with role, summary, and sorted gaps
    
    Raises:
        HTTPException: If user not found, role missing, etc.
    """
    db = get_database(database)
    
    # 1. Get user's professional role
    role_doc = repository.get_user_role(db, user_id)
    if role_doc is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User does not have a professional role assigned",
        )
    
    role_id = str(role_doc["_id"])
    
    # 2. Get role's competency requirements
    requirements = repository.get_role_requirements_with_competencies(db, role_id)
    if not requirements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No competency requirements are configured for this role",
        )
    
    # 3. Get user's current competency profiles for all requirements
    requirement_competency_ids = [req["competency_id"] for req in requirements]
    profiles = repository.get_user_competency_profiles(
        db,
        user_id,
        requirement_competency_ids,
    )
    
    # 4. Calculate gap for each requirement
    gap_items = []
    for req in requirements:
        competency_id_str = str(req["competency_id"])
        profile = profiles.get(competency_id_str)
        
        current_level = profile["current_level"] if profile else None
        confidence = profile.get("confidence", 0.0) if profile else 0.0
        last_assessed_at = profile.get("last_assessed_at") if profile else None
        
        gap_item = engine.build_gap_item(
            competency_id=competency_id_str,
            competency_code=req["competency_code"],
            competency_name=req["competency_name"],
            domain=req["domain"],
            required_level=req["required_level"],
            current_level=current_level,
            role_priority=req["priority"],
            importance=req["importance"],
            confidence=confidence,
            last_assessed_at=last_assessed_at,
        )
        gap_items.append(gap_item)
    
    # 5. Sort by priority
    sorted_gaps = engine.sort_gaps(gap_items)
    
    # 6. Calculate summary
    summary_data = engine.calculate_summary(sorted_gaps)
    
    # Build response
    summary = SkillGapSummary(
        role_id=role_id,
        role_code=role_doc["role_code"],
        role_name=role_doc["role_name"],
        **summary_data,
    )
    
    return SkillGapResponse(
        role={
            "id": role_id,
            "code": role_doc["role_code"],
            "name": role_doc["role_name"],
        },
        summary=summary,
        gaps=sorted_gaps,
    )
