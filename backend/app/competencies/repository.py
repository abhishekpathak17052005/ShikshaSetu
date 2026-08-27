from bson import ObjectId
from pymongo.database import Database


def _object_id(value: str) -> ObjectId | None:
    return ObjectId(value) if ObjectId.is_valid(value) else None


def list_competencies(database: Database) -> list[dict]:
    return list(database.competencies.find({}, {"_id": 1, "code": 1, "name": 1, "domain": 1, "description": 1, "level_definitions": 1, "status": 1, "framework_status": 1, "source_type": 1, "source_reference": 1, "created_at": 1, "updated_at": 1}).sort("code", 1))


def get_competency(database: Database, competency_id: str) -> dict | None:
    object_id = _object_id(competency_id)
    return database.competencies.find_one({"_id": object_id}) if object_id else None


def list_roles(database: Database) -> list[dict]:
    return list(database.roles.find({}).sort("role_code", 1))


def get_role(database: Database, role_id: str) -> dict | None:
    object_id = _object_id(role_id)
    return database.roles.find_one({"_id": object_id}) if object_id else None


def list_role_requirements(database: Database, role_id: str) -> list[dict]:
    object_id = _object_id(role_id)
    if object_id is None:
        return []
    return list(database.role_requirements.find({"role_id": object_id}).sort("priority", 1))
