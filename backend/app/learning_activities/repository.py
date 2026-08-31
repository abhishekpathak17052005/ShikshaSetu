"""Repository layer for learning activities."""

from datetime import datetime
from typing import Optional, List
from pymongo.database import Database
from bson import ObjectId


def object_id(value: str) -> Optional[ObjectId]:
    """Convert string to ObjectId if valid."""
    try:
        return ObjectId(value)
    except (ValueError, TypeError):
        return None


def create_learning_activity_indexes(database: Database) -> None:
    """Ensure indexes exist for learning activities collection."""
    collection = database["learning_activities"]
    collection.create_index([("user_id", 1), ("status", 1)])
    collection.create_index([("user_id", 1), ("completed_at", 1)])
    collection.create_index([("resource_id", 1)])
    collection.create_index([("user_id", 1), ("competency_id", 1)])


def create_learning_activity(
    database: Database,
    user_id: str,
    resource_id: str,
    competency_id: str,
) -> str:
    """Create a new learning activity."""
    collection = database["learning_activities"]
    
    document = {
        "user_id": object_id(user_id),
        "resource_id": resource_id,
        "competency_id": competency_id,
        "status": "in_progress",
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "last_accessed_at": datetime.utcnow(),
        "progress_percent": 0.0,
        "duration_minutes": 0.0,
        "notes": None,
    }
    
    result = collection.insert_one(document)
    return str(result.inserted_id)


def get_learning_activity(
    database: Database,
    activity_id: str,
    user_id: str,
) -> Optional[dict]:
    """Get a learning activity (verified ownership)."""
    collection = database["learning_activities"]
    
    activity_oid = object_id(activity_id)
    if not activity_oid:
        return None
    
    user_oid = object_id(user_id)
    if not user_oid:
        return None
    
    document = collection.find_one({
        "_id": activity_oid,
        "user_id": user_oid,
    })
    
    return document


def update_learning_activity(
    database: Database,
    activity_id: str,
    user_id: str,
    update_data: dict,
) -> Optional[dict]:
    """Update a learning activity."""
    collection = database["learning_activities"]
    
    activity_oid = object_id(activity_id)
    if not activity_oid:
        return None
    
    user_oid = object_id(user_id)
    if not user_oid:
        return None
    
    # Add last accessed timestamp
    update_data["last_accessed_at"] = datetime.utcnow()
    
    result = collection.find_one_and_update(
        {
            "_id": activity_oid,
            "user_id": user_oid,
        },
        {"$set": update_data},
        return_document=True,
    )
    
    return result


def complete_learning_activity(
    database: Database,
    activity_id: str,
    user_id: str,
) -> Optional[dict]:
    """Mark a learning activity as completed."""
    collection = database["learning_activities"]
    
    activity_oid = object_id(activity_id)
    if not activity_oid:
        return None
    
    user_oid = object_id(user_id)
    if not user_oid:
        return None
    
    result = collection.find_one_and_update(
        {
            "_id": activity_oid,
            "user_id": user_oid,
        },
        {
            "$set": {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "last_accessed_at": datetime.utcnow(),
            }
        },
        return_document=True,
    )
    
    return result


def list_user_learning_activities(
    database: Database,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """List user's learning activities."""
    collection = database["learning_activities"]
    
    user_oid = object_id(user_id)
    if not user_oid:
        return []
    
    query = {"user_id": user_oid}
    if status:
        query["status"] = status
    
    documents = list(
        collection.find(query)
        .sort("last_accessed_at", -1)
        .limit(limit)
    )
    
    return documents


def get_user_activity_for_resource(
    database: Database,
    user_id: str,
    resource_id: str,
) -> Optional[dict]:
    """Get user's learning activity for a specific resource."""
    collection = database["learning_activities"]
    
    user_oid = object_id(user_id)
    if not user_oid:
        return None
    
    document = collection.find_one({
        "user_id": user_oid,
        "resource_id": resource_id,
    })
    
    return document


def get_user_completed_resources(
    database: Database,
    user_id: str,
) -> List[str]:
    """Get list of resources completed by user."""
    collection = database["learning_activities"]
    
    user_oid = object_id(user_id)
    if not user_oid:
        return []
    
    results = collection.find(
        {
            "user_id": user_oid,
            "status": "completed",
        },
        {"resource_id": 1}
    )
    
    return [r["resource_id"] for r in results]


def get_user_in_progress_resources(
    database: Database,
    user_id: str,
) -> List[str]:
    """Get list of resources currently in progress by user."""
    collection = database["learning_activities"]
    
    user_oid = object_id(user_id)
    if not user_oid:
        return []
    
    results = collection.find(
        {
            "user_id": user_oid,
            "status": "in_progress",
        },
        {"resource_id": 1}
    )
    
    return [r["resource_id"] for r in results]
