"""Service layer for learning activities."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pymongo.database import Database
from bson import ObjectId

from app.learning_activities import repository
from app.learning_activities.models import LearningActivityStatus
from app.learning_activities.schemas import LearningActivityResponse


def _object_id(value: str) -> Optional[ObjectId]:
    """Convert string to ObjectId."""
    try:
        return ObjectId(value)
    except (ValueError, TypeError):
        return None


def _format_activity_for_response(document: dict) -> LearningActivityResponse:
    """Convert MongoDB document to response schema."""
    return LearningActivityResponse(
        activity_id=str(document["_id"]),
        user_id=str(document["user_id"]),
        resource_id=document["resource_id"],
        competency_id=document["competency_id"],
        status=LearningActivityStatus(document["status"]),
        started_at=document["started_at"],
        completed_at=document.get("completed_at"),
        last_accessed_at=document["last_accessed_at"],
        progress_percent=document.get("progress_percent", 0),
        duration_minutes=document.get("duration_minutes", 0),
        notes=document.get("notes"),
    )


def start_learning_activity(
    database: Database,
    user_id: str,
    resource_id: str,
    competency_id: str,
) -> LearningActivityResponse:
    """Start a new learning activity."""
    # Check if user already has activity for this resource
    existing = repository.get_user_activity_for_resource(
        database, user_id, resource_id
    )
    
    if existing and existing["status"] != "completed":
        # Return existing in-progress activity
        return _format_activity_for_response(existing)
    
    # Create new activity
    activity_id = repository.create_learning_activity(
        database, user_id, resource_id, competency_id
    )
    
    activity = repository.get_learning_activity(database, activity_id, user_id)
    return _format_activity_for_response(activity)


def update_learning_activity(
    database: Database,
    activity_id: str,
    user_id: str,
    progress_percent: Optional[float] = None,
    duration_minutes: Optional[float] = None,
    notes: Optional[str] = None,
) -> LearningActivityResponse:
    """Update a learning activity's progress."""
    update_data = {}
    
    if progress_percent is not None:
        update_data["progress_percent"] = max(0, min(100, progress_percent))
    
    if duration_minutes is not None:
        update_data["duration_minutes"] = max(0, duration_minutes)
    
    if notes is not None:
        update_data["notes"] = notes
    
    activity = repository.update_learning_activity(
        database, activity_id, user_id, update_data
    )
    
    if not activity:
        raise ValueError(f"Activity {activity_id} not found or unauthorized")
    
    return _format_activity_for_response(activity)


def complete_learning_activity(
    database: Database,
    activity_id: str,
    user_id: str,
    final_score: Optional[float] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete a learning activity and generate evidence.
    
    IMPORTANT: Learning completion creates supporting EVIDENCE, not authoritative competency updates.
    Competency levels are updated only by assessment/quiz evidence, not by course completion.
    This preserves the integrity of the skill gap calculation.
    """
    # Get current activity
    activity = repository.get_learning_activity(database, activity_id, user_id)
    if not activity:
        raise ValueError(f"Activity {activity_id} not found or unauthorized")
    
    # Mark as completed
    completed_activity = repository.complete_learning_activity(
        database, activity_id, user_id
    )
    
    # Generate evidence (supporting, not authoritative)
    evidence_collection = database["competency_evidence"]
    
    # Calculate evidence score from final_score or progress
    if final_score is not None:
        evidence_score = max(0, min(100, final_score))
    else:
        # Default: use progress as evidence score
        evidence_score = activity.get("progress_percent", 0)
    
    evidence_document = {
        "user_id": _object_id(user_id),
        "competency_id": activity["competency_id"],
        "type": "LEARNING_ACTIVITY",  # Supporting evidence only
        "score": evidence_score,
        "recorded_at": datetime.utcnow(),
        "source": {
            "activity_id": _object_id(activity_id),
            "resource_id": activity["resource_id"],
        },
        "notes": notes or f"Completed learning activity for {activity['resource_id']}",
        "confidence": 0.3,  # Lower than assessment evidence (0.8) - supporting only
    }
    
    result = evidence_collection.insert_one(evidence_document)
    evidence_id = str(result.inserted_id)
    
    # Get current competency level (NOT MODIFIED by learning completion)
    profiles_collection = database["competency_profiles"]
    user_oid = _object_id(user_id)
    
    current_profile = profiles_collection.find_one({
        "user_id": user_oid,
        "competency_id": activity["competency_id"],
    })
    
    current_level = current_profile["current_level"] if current_profile else 0
    
    # NOTE: We DO NOT update the competency level here.
    # Competency updates only come from ASSESSMENT/QUIZ evidence (type: CAPABILITY_ASSESSMENT)
    # Learning completion is supporting evidence, not proof of demonstrated capability.
    # This is recorded only in the evidence collection for context/audit trail.
    
    # Skill gap remains unchanged until assessment evidence updates competency
    # In production, gap calculation would fetch from role_requirements
    required_level = 4.0  # Statistical Officer standard
    gap_current = max(0, required_level - current_level)
    
    return {
        "activity": _format_activity_for_response(completed_activity),
        "evidence_created": True,
        "evidence_id": evidence_id,
        "evidence_type": "LEARNING_ACTIVITY",
        "evidence_confidence": 0.3,
        "note": "Learning completion recorded as supporting evidence. Competency level updated only by assessment/capability evidence.",
        "current_competency_level": round(current_level, 2),
        "current_skill_gap": round(gap_current, 2),
        "next_step": "Complete an assessment or capability quiz to demonstrate the learned skill and update your competency level.",
    }


def get_learning_activity_details(
    database: Database,
    activity_id: str,
    user_id: str,
) -> LearningActivityResponse:
    """Get details of a learning activity."""
    activity = repository.get_learning_activity(database, activity_id, user_id)
    if not activity:
        raise ValueError(f"Activity {activity_id} not found or unauthorized")
    
    return _format_activity_for_response(activity)


def list_user_activities(
    database: Database,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[LearningActivityResponse]:
    """List user's learning activities."""
    activities = repository.list_user_learning_activities(
        database, user_id, status=status, limit=limit
    )
    
    return [_format_activity_for_response(a) for a in activities]


def get_user_completed_resource_ids(
    database: Database,
    user_id: str,
) -> List[str]:
    """Get list of resource IDs completed by user."""
    return repository.get_user_completed_resources(database, user_id)


def get_user_in_progress_resource_ids(
    database: Database,
    user_id: str,
) -> List[str]:
    """Get list of resource IDs in progress by user."""
    return repository.get_user_in_progress_resources(database, user_id)
