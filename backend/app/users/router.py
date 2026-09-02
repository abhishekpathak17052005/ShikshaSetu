from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pymongo.errors import DuplicateKeyError

from app.auth.dependencies import get_current_user
from app.auth.router import public_user
from app.auth.schemas import UserProfileUpdate, UserResponse
from app.users import repository

router = APIRouter(prefix="/users", tags=["users"])


def update_profile(request: Request, current_user: dict, payload: UserProfileUpdate) -> dict:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return public_user(current_user)

    from app.roles.resolver import resolve_role_for_user, reconcile_user_competencies

    new_dept = updates.get("department", current_user.get("department"))
    new_desig = updates.get("designation", current_user.get("designation"))

    if "department" in updates or "designation" in updates:
        resolved_role_oid = resolve_role_for_user(database, new_dept, new_desig)
        if resolved_role_oid:
            updates["role_id"] = resolved_role_oid
            reconcile_user_competencies(database, current_user["_id"], resolved_role_oid)

    updates["updated_at"] = datetime.now(UTC)
    try:
        updated_user = repository.update_user(database, str(current_user["_id"]), updates)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Profile update could not be completed") from None
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return public_user(updated_user)



@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
) -> dict:
    return public_user(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    request: Request,
    payload: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    return update_profile(request, current_user, payload)


@router.get("/me/evidence")
def get_my_evidence(
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Retrieve all authoritative and supporting evidence records from the immutable ledger."""
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")

    from bson import ObjectId
    uid = current_user["_id"]
    uid_str = str(uid)

    cursor = database.competency_evidence.find({"$or": [{"user_id": uid}, {"user_id": uid_str}]})
    evidence_docs = list(cursor)

    comp_docs = list(database.competencies.find())
    comp_map = {c["_id"]: c for c in comp_docs}
    comp_code_map = {c["code"]: c for c in comp_docs}

    results = []
    for doc in evidence_docs:
        c_id = doc.get("competency_id")
        comp = comp_map.get(c_id) or comp_code_map.get(str(c_id))
        comp_code = comp.get("code") if comp else str(c_id)
        comp_name = comp.get("name") if comp else comp_code.replace("_", " ")

        raw_type = str(doc.get("evidence_type", "SUPPORTING")).upper()
        conf = float(doc.get("confidence", doc.get("evidence_confidence", 0.85 if ("ASSESS" in raw_type or "QUIZ" in raw_type) else 0.3)))
        is_authoritative = "ASSESS" in raw_type or "QUIZ" in raw_type or conf >= 0.7

        raw_score = doc.get("score", doc.get("level", 3.0))
        try:
            val = float(raw_score)
            # If stored as percentage (e.g., 60.0 or 85.0), scale to 1.0 - 5.0
            if val > 5.0:
                normalized_score = round(min(5.0, max(1.0, (val / 100.0) * 5.0)), 1)
            else:
                normalized_score = round(min(5.0, max(1.0, val)), 1)
        except (ValueError, TypeError):
            normalized_score = 3.0

        results.append({
            "id": str(doc.get("_id", ObjectId())),
            "type": "AUTHORITATIVE" if is_authoritative else "SUPPORTING",
            "source": doc.get("source", doc.get("assessment_type", "Standardized Assessment" if is_authoritative else "Learning Module")),
            "title": doc.get("title", f"Competency Verification: {comp_name}"),
            "competency_code": comp_code,
            "competency_name": comp_name,
            "confidence": conf,
            "score": normalized_score,
            "date": doc.get("created_at", doc.get("timestamp", datetime.now(UTC))),
            "notes": doc.get("notes", "Immutable cryptographic capability audit record."),
        })

    # If newly registered user without prior evidence, seed initial baseline evidence from role requirements
    if not results:
        role_id = current_user.get("role_id")
        reqs = list(database.role_requirements.find({"role_id": role_id})) if role_id else []
        now = datetime.now(UTC)
        starter_records = []
        for req in (reqs[:4] if reqs else []):
            c_id = req.get("competency_id")
            comp = comp_map.get(c_id) or comp_code_map.get(str(c_id))
            comp_code = comp.get("code") if comp else "GENERAL_COMP"
            comp_name = comp.get("name") if comp else comp_code.replace("_", " ")

            ev_doc = {
                "user_id": uid,
                "competency_id": comp.get("_id", c_id) if comp else c_id,
                "evidence_type": "BASELINE_ASSESSMENT",
                "source": "Initial Competency Self-Declaration & Orientation",
                "title": f"Baseline Capability Verification: {comp_name}",
                "confidence": 0.85,
                "score": float(req.get("required_level", 3.0)),
                "level": float(req.get("required_level", 3.0)),
                "notes": "Initial civil service role capability baseline recorded upon department onboarding.",
                "created_at": now,
            }
            database.competency_evidence.insert_one(ev_doc)
            starter_records.append({
                "id": str(ev_doc["_id"]),
                "type": "AUTHORITATIVE",
                "source": ev_doc["source"],
                "title": ev_doc["title"],
                "competency_code": comp_code,
                "competency_name": comp_name,
                "confidence": 0.85,
                "score": ev_doc["score"],
                "date": now,
                "notes": ev_doc["notes"],
            })
        return starter_records

    results.sort(key=lambda x: x.get("date") if isinstance(x.get("date"), datetime) else datetime.min.replace(tzinfo=UTC), reverse=True)
    return results
