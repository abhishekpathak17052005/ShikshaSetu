"""Repository for capability assessment operations."""
from bson import ObjectId
from pymongo.database import Database


def object_id(value: str) -> ObjectId | None:
    """Convert string to ObjectId if valid."""
    return ObjectId(value) if ObjectId.is_valid(value) else None


def insert_capability_assessment(database: Database, assessment_doc: dict) -> str:
    """Insert a new capability assessment."""
    result = database.capability_assessments.insert_one(assessment_doc)
    return str(result.inserted_id)


def get_capability_assessment_for_user(
    database: Database,
    assessment_id: str,
    user_id: str
) -> dict | None:
    """Get capability assessment for a specific user (ownership check)."""
    assessment_oid = object_id(assessment_id)
    user_oid = object_id(user_id)
    
    if assessment_oid is None or user_oid is None:
        return None
    
    return database.capability_assessments.find_one({
        "_id": assessment_oid,
        "user_id": user_oid
    })


def get_capability_assessment_by_id(database: Database, assessment_id: str) -> dict | None:
    """Get capability assessment by ID (internal use only)."""
    assessment_oid = object_id(assessment_id)
    if assessment_oid is None:
        return None
    
    return database.capability_assessments.find_one({"_id": assessment_oid})


def get_user_capability_assessments(
    database: Database,
    user_id: str,
    competency_code: str | None = None,
    status: str | None = None,
    limit: int = 100
) -> list[dict]:
    """Get all capability assessments for a user, optionally filtered."""
    user_oid = object_id(user_id)
    if user_oid is None:
        return []
    
    query = {"user_id": user_oid}
    if competency_code:
        query["competency_code"] = competency_code
    if status:
        query["status"] = status
    
    return list(
        database.capability_assessments
        .find(query)
        .sort("created_at", -1)
        .limit(limit)
    )


def get_in_progress_assessment_for_user_and_competency(
    database: Database,
    user_id: str,
    competency_code: str
) -> dict | None:
    """Check if user has an IN_PROGRESS assessment for a competency."""
    user_oid = object_id(user_id)
    if user_oid is None:
        return None
    
    return database.capability_assessments.find_one({
        "user_id": user_oid,
        "competency_code": competency_code,
        "status": "IN_PROGRESS"
    })


def update_assessment_status_and_submit(
    database: Database,
    assessment_id: str,
    user_id: str,
    update_dict: dict
) -> dict | None:
    """Update assessment status to SUBMITTED and add submission data."""
    assessment_oid = object_id(assessment_id)
    user_oid = object_id(user_id)
    
    if assessment_oid is None or user_oid is None:
        return None
    
    # Atomic update: check status is IN_PROGRESS before updating
    result = database.capability_assessments.find_one_and_update(
        {
            "_id": assessment_oid,
            "user_id": user_oid,
            "status": "IN_PROGRESS"  # Ensure not already submitted
        },
        {"$set": update_dict},
        return_document=True
    )
    
    return result


def get_submitted_assessment_results(
    database: Database,
    assessment_id: str,
    user_id: str
) -> dict | None:
    """Get results of a submitted assessment."""
    assessment_oid = object_id(assessment_id)
    user_oid = object_id(user_id)
    
    if assessment_oid is None or user_oid is None:
        return None
    
    return database.capability_assessments.find_one({
        "_id": assessment_oid,
        "user_id": user_oid,
        "status": "SUBMITTED"
    })


def get_latest_assessment_for_competency(
    database: Database,
    user_id: str,
    competency_code: str
) -> dict | None:
    """Get most recent assessment for a user and competency."""
    user_oid = object_id(user_id)
    if user_oid is None:
        return None
    
    return database.capability_assessments.find_one(
        {
            "user_id": user_oid,
            "competency_code": competency_code,
            "status": "SUBMITTED"
        },
        sort=[("submitted_at", -1)]
    )


def count_user_assessments_for_competency(
    database: Database,
    user_id: str,
    competency_code: str,
    status: str | None = None
) -> int:
    """Count assessments for a user and competency."""
    user_oid = object_id(user_id)
    if user_oid is None:
        return 0
    
    query = {
        "user_id": user_oid,
        "competency_code": competency_code
    }
    if status:
        query["status"] = status
    
    return database.capability_assessments.count_documents(query)
