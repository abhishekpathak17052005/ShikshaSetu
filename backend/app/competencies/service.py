from fastapi import HTTPException, status
from pymongo.database import Database

from app.competencies import repository


def _public(document: dict) -> dict:
    result = dict(document)
    result["id"] = str(result.pop("_id"))
    return result


def get_database(database: Database | None) -> Database:
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return database


def list_competencies(database: Database | None) -> list[dict]:
    return [_public(item) for item in repository.list_competencies(get_database(database))]


def get_competency(database: Database | None, competency_id: str) -> dict:
    item = repository.get_competency(get_database(database), competency_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competency not found")
    return _public(item)


def list_roles(database: Database | None) -> list[dict]:
    return [_public(item) for item in repository.list_roles(get_database(database))]


def get_role(database: Database | None, role_id: str) -> dict:
    item = repository.get_role(get_database(database), role_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return _public(item)


def list_role_requirements(database: Database | None, role_id: str) -> list[dict]:
    database = get_database(database)
    if repository.get_role(database, role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return [_public_requirement(item) for item in repository.list_role_requirements(database, role_id)]


def _public_requirement(document: dict) -> dict:
    result = dict(document)
    result["role_id"] = str(result.pop("role_id"))
    result["competency_id"] = str(result.pop("competency_id"))
    return result
