"""
Repository layer for skill gap queries.

Reuses existing MongoDB collections without duplication.
"""

from bson import ObjectId
from pymongo.database import Database


def object_id(value: str) -> ObjectId | None:
    """Convert string to ObjectId if valid."""
    return ObjectId(value) if ObjectId.is_valid(value) else None


def get_user_role(database: Database, user_id: str) -> dict | None:
    """
    Get the user's professional role.
    
    Args:
        database: MongoDB database
        user_id: User ObjectId as string
    
    Returns:
        Role document or None
    """
    user_object_id = object_id(user_id)
    if user_object_id is None:
        return None
    
    user = database.users.find_one(
        {"_id": user_object_id},
        {"role_id": 1},
    )
    if user is None or "role_id" not in user:
        return None
    
    role_doc = database.roles.find_one(
        {"_id": user["role_id"]},
        {
            "_id": 1,
            "role_code": 1,
            "role_name": 1,
            "description": 1,
            "status": 1,
        },
    )
    return role_doc


def get_role_requirements_with_competencies(
    database: Database,
    role_id: str,
) -> list[dict]:
    """
    Get all competency requirements for a role with enriched competency details.
    
    Args:
        database: MongoDB database
        role_id: Role ObjectId as string
    
    Returns:
        List of requirement documents with competency details embedded
    """
    role_object_id = object_id(role_id)
    if role_object_id is None:
        return []
    
    requirements = list(
        database.role_requirements.find(
            {"role_id": role_object_id},
            {
                "competency_id": 1,
                "required_level": 1,
                "priority": 1,
                "importance": 1,
            },
        )
    )
    
    # Enrich with competency details
    enriched = []
    for req in requirements:
        competency = database.competencies.find_one(
            {"_id": req["competency_id"]},
            {
                "_id": 1,
                "code": 1,
                "name": 1,
                "domain": 1,
            },
        )
        if competency:
            enriched.append(
                {
                    "competency_id": competency["_id"],
                    "competency_code": competency["code"],
                    "competency_name": competency["name"],
                    "domain": competency["domain"],
                    "required_level": req["required_level"],
                    "priority": req["priority"],
                    "importance": req["importance"],
                }
            )
    
    return enriched


def get_user_competency_profiles(
    database: Database,
    user_id: str,
    competency_ids: list[str],
) -> dict[str, dict]:
    """
    Get user's current competency profiles for multiple competencies.
    
    Args:
        database: MongoDB database
        user_id: User ObjectId as string
        competency_ids: List of competency ObjectIds as strings
    
    Returns:
        Dict mapping competency_id (string) to profile doc or None
    """
    user_object_id = object_id(user_id)
    if user_object_id is None:
        return {}
    
    # Convert competency IDs to ObjectIds
    competency_object_ids = [
        cid for cid in [object_id(cid) for cid in competency_ids] if cid is not None
    ]
    
    if not competency_object_ids:
        return {}
    
    # Fetch all profiles for this user across these competencies
    profiles = list(
        database.competency_profiles.find(
            {
                "user_id": user_object_id,
                "competency_id": {"$in": competency_object_ids},
            },
            {
                "competency_id": 1,
                "current_level": 1,
                "confidence": 1,
                "last_assessed_at": 1,
            },
        )
    )
    
    # Map by competency_id (as string for easier lookup)
    return {str(p["competency_id"]): p for p in profiles}
