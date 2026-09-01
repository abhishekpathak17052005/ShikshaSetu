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


def list_user_competencies(database: Database | None, user_id: str) -> list[dict]:
    db = get_database(database)
    from bson import ObjectId
    from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies

    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
    if not u_oid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID")

    user = db.users.find_one({"_id": u_oid})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_id = user.get("role_id")
    if not role_id:
        resolved_role_id = resolve_role_for_user(db, user.get("department"), user.get("designation"))
        if resolved_role_id:
            reconcile_user_competencies(db, u_oid, resolved_role_id)
            role_id = resolved_role_id

    if not role_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No role configured for user")

    r_oid = ObjectId(role_id) if isinstance(role_id, str) and ObjectId.is_valid(role_id) else role_id

    # Fetch role requirements
    reqs = list(db.role_requirements.find({"role_id": r_oid}).sort("priority", 1))
    if not reqs:
        # Check if user needs reconciliation
        resolved_role_id = resolve_role_for_user(db, user.get("department"), user.get("designation"))
        if resolved_role_id and resolved_role_id != r_oid:
            reconcile_user_competencies(db, u_oid, resolved_role_id)
            reqs = list(db.role_requirements.find({"role_id": resolved_role_id}).sort("priority", 1))

    # Fetch user profiles
    profiles = list(db.competency_profiles.find({"user_id": u_oid}))
    prof_map = {str(p["competency_id"]): p for p in profiles if "competency_id" in p}

    # Fetch competency details
    comp_ids = [req["competency_id"] for req in reqs if "competency_id" in req]
    comps = list(db.competencies.find({"_id": {"$in": comp_ids}}))
    comp_map = {str(c["_id"]): c for c in comps}

    results = []
    for req in reqs:
        c_oid_str = str(req.get("competency_id"))
        comp = comp_map.get(c_oid_str)
        if not comp:
            continue

        p = prof_map.get(c_oid_str)
        cur_lvl = p.get("current_level") if (p and p.get("current_level") is not None) else (p.get("level") if p else None)
        conf = float(p.get("confidence", 0.0)) if p else 0.0
        req_lvl = float(req.get("required_level", 4.0))
        last_assessed = p.get("last_assessed_at") or p.get("last_updated_at") if p else None

        if cur_lvl is not None:
            gap = max(0.0, req_lvl - cur_lvl)
            if gap <= 0:
                gap_cat = "NONE"
                indicator = "Strong"
            elif gap <= 1.0:
                gap_cat = "LOW"
                indicator = "Developing"
            elif gap <= 2.0:
                gap_cat = "MEDIUM"
                indicator = "Needs Attention"
            else:
                gap_cat = "CRITICAL"
                indicator = "Needs Attention"
        else:
            gap = req_lvl
            gap_cat = "NOT_ASSESSED"
            indicator = "Not Assessed"

        results.append({
            "id": c_oid_str,
            "code": comp.get("code", ""),
            "name": comp.get("name", ""),
            "domain": comp.get("domain", "STATISTICAL"),
            "description": comp.get("description", ""),
            "required_level": req_lvl,
            "priority": int(req.get("priority", 2)),
            "importance": float(req.get("importance", 0.75)),
            "current_level": cur_lvl,
            "confidence": conf,
            "gap": round(gap, 2),
            "gap_category": gap_cat,
            "last_assessed_at": last_assessed,
            "indicator": indicator,
            "level_definitions": comp.get("level_definitions", {}),
        })

    return results

