from datetime import datetime

from bson import ObjectId
from pymongo.database import Database


def object_id(value: str) -> ObjectId | None:
    return ObjectId(value) if ObjectId.is_valid(value) else None


def get_assessment(database: Database, assessment_key: str) -> dict | None:
    return database.assessments.find_one({"assessment_key": assessment_key, "status": "active"})


def insert_attempt(database: Database, document: dict) -> None:
    database.assessment_attempts.insert_one(document)


def get_attempt_for_user(database: Database, attempt_id: str, user_id: str) -> dict | None:
    attempt_object_id = object_id(attempt_id)
    user_object_id = object_id(user_id)
    if attempt_object_id is None or user_object_id is None:
        return None
    return database.assessment_attempts.find_one({"_id": attempt_object_id, "user_id": user_object_id})


def submit_attempt(database: Database, attempt_id: str, user_id: str, update: dict) -> dict | None:
    attempt_object_id = object_id(attempt_id)
    user_object_id = object_id(user_id)
    if attempt_object_id is None or user_object_id is None:
        return None
    database.assessment_attempts.update_one(
        {"_id": attempt_object_id, "user_id": user_object_id, "status": "IN_PROGRESS"},
        {"$set": update},
    )
    return get_attempt_for_user(database, attempt_id, user_id)


def upsert_profile(database: Database, user_id: ObjectId, competency_id: ObjectId, update: dict) -> None:
    database.competency_profiles.update_one(
        {"user_id": user_id, "competency_id": competency_id},
        {"$set": update, "$setOnInsert": {"user_id": user_id, "competency_id": competency_id}},
        upsert=True,
    )


def insert_evidence(database: Database, document: dict) -> None:
    database.competency_evidence.insert_one(document)
