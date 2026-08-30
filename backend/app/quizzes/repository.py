"""Quiz repository - CRUD operations for quizzes and attempts."""
from datetime import datetime

from bson import ObjectId
from pymongo.database import Database


def object_id(value: str) -> ObjectId | None:
    """Convert string to ObjectId if valid."""
    return ObjectId(value) if ObjectId.is_valid(value) else None


def create_quiz_indexes(database: Database) -> None:
    """Create necessary indexes for quiz collection."""
    database.quizzes.create_index("user_id")
    database.quizzes.create_index([("user_id", 1), ("created_at", -1)])
    database.quizzes.create_index("material_id")
    database.quizzes.create_index([("user_id", 1), ("status", 1)])


def create_quiz_attempt_indexes(database: Database) -> None:
    """Create necessary indexes for quiz_attempts collection."""
    database.quiz_attempts.create_index("quiz_id")
    database.quiz_attempts.create_index("user_id")
    database.quiz_attempts.create_index([("quiz_id", 1), ("user_id", 1)])
    database.quiz_attempts.create_index([("user_id", 1), ("submitted_at", -1)])


def insert_quiz(database: Database, quiz_document: dict) -> str:
    """Insert a new quiz and return its ID."""
    result = database.quizzes.insert_one(quiz_document)
    return str(result.inserted_id)


def get_quiz_by_id(database: Database, quiz_id: str, user_id: str) -> dict | None:
    """Get a quiz by ID, verifying user ownership."""
    quiz_oid = object_id(quiz_id)
    user_oid = object_id(user_id)
    if quiz_oid is None or user_oid is None:
        return None
    return database.quizzes.find_one({"_id": quiz_oid, "user_id": user_oid})


def get_quiz_without_auth(database: Database, quiz_id: str) -> dict | None:
    """Get a quiz by ID without authentication (internal use only)."""
    quiz_oid = object_id(quiz_id)
    if quiz_oid is None:
        return None
    return database.quizzes.find_one({"_id": quiz_oid})


def update_quiz_status(
    database: Database,
    quiz_id: str,
    user_id: str,
    status: str,
) -> dict | None:
    """Update quiz status."""
    quiz_oid = object_id(quiz_id)
    user_oid = object_id(user_id)
    if quiz_oid is None or user_oid is None:
        return None
    
    result = database.quizzes.find_one_and_update(
        {"_id": quiz_oid, "user_id": user_oid},
        {"$set": {"status": status}},
        return_document=True,
    )
    return result


def update_quiz_with_score(
    database: Database,
    quiz_id: str,
    user_id: str,
    score: int,
    percentage: float,
    submitted_at: datetime,
) -> dict | None:
    """Update quiz with score after submission."""
    quiz_oid = object_id(quiz_id)
    user_oid = object_id(user_id)
    if quiz_oid is None or user_oid is None:
        return None
    
    result = database.quizzes.find_one_and_update(
        {"_id": quiz_oid, "user_id": user_oid},
        {
            "$set": {
                "status": "SUBMITTED",
                "score": score,
                "percentage": percentage,
                "submitted_at": submitted_at,
            }
        },
        return_document=True,
    )
    return result


def insert_quiz_attempt(database: Database, attempt_document: dict) -> str:
    """Insert a new quiz attempt and return its ID."""
    result = database.quiz_attempts.insert_one(attempt_document)
    return str(result.inserted_id)


def get_quiz_attempt_by_id(
    database: Database,
    attempt_id: str,
    user_id: str,
) -> dict | None:
    """Get a quiz attempt by ID, verifying user ownership."""
    attempt_oid = object_id(attempt_id)
    user_oid = object_id(user_id)
    if attempt_oid is None or user_oid is None:
        return None
    return database.quiz_attempts.find_one({"_id": attempt_oid, "user_id": user_oid})


def get_quiz_attempt_by_quiz_id(
    database: Database,
    quiz_id: str,
    user_id: str,
) -> dict | None:
    """Get the attempt for a quiz (should be only one per quiz per user)."""
    quiz_oid = object_id(quiz_id)
    user_oid = object_id(user_id)
    if quiz_oid is None or user_oid is None:
        return None
    return database.quiz_attempts.find_one({"quiz_id": quiz_oid, "user_id": user_oid})


def get_quiz_attempts_for_user(
    database: Database,
    user_id: str,
    limit: int = 10,
) -> list[dict]:
    """Get recent quiz attempts for a user."""
    user_oid = object_id(user_id)
    if user_oid is None:
        return []
    
    return list(
        database.quiz_attempts.find({"user_id": user_oid})
        .sort("submitted_at", -1)
        .limit(limit)
    )
