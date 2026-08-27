from datetime import datetime

from bson import ObjectId
from pymongo.database import Database


def object_id(value: str) -> ObjectId | None:
    return ObjectId(value) if ObjectId.is_valid(value) else None


def get_user_by_email(database: Database, email: str) -> dict | None:
    return database.users.find_one({"email": email})


def get_user_by_id(database: Database, user_id: str) -> dict | None:
    user_object_id = object_id(user_id)
    return database.users.find_one({"_id": user_object_id}) if user_object_id else None


def role_exists(database: Database, role_id: str) -> bool:
    role_object_id = object_id(role_id)
    return bool(role_object_id and database.roles.find_one({"_id": role_object_id, "status": "active"}))


def insert_user(database: Database, document: dict) -> dict:
    database.users.insert_one(document)
    return document


def update_user(database: Database, user_id: str, updates: dict) -> dict | None:
    user_object_id = object_id(user_id)
    if user_object_id is None:
        return None
    database.users.update_one({"_id": user_object_id}, {"$set": updates})
    return get_user_by_id(database, user_id)


def update_last_login(database: Database, user_id: str, timestamp: datetime) -> dict | None:
    return update_user(database, user_id, {"last_login_at": timestamp, "updated_at": timestamp})
