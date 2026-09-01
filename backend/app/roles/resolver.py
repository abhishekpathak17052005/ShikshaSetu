"""Role resolution and user competency reconciliation engine."""

from datetime import datetime, UTC
from typing import Optional
from bson import ObjectId
from pymongo.database import Database


def _object_id(val: str | ObjectId) -> Optional[ObjectId]:
    if isinstance(val, ObjectId):
        return val
    return ObjectId(val) if ObjectId.is_valid(val) else None


def resolve_role_for_user(
    database: Database,
    department: Optional[str],
    designation: Optional[str],
) -> Optional[ObjectId]:
    """
    Deterministically resolves the appropriate Role ObjectId for a user based on
    their Department and Designation.
    
    Resolution hierarchy:
    1. Exact match on designation within matching department
    2. Case-insensitive regex match on designation within matching department
    3. Match on designation across all roles
    4. Match on department default role
    5. Fallback to default STATISTICAL_OFFICER or first active role
    """
    dept_str = (department or "").strip().lower()
    desig_str = (designation or "").strip().lower()

    roles = list(database.roles.find({"status": "active"}))
    if not roles:
        roles = list(database.roles.find({}))
    if not roles:
        return None

    # Step 1: Match department + designation exactly or in designations list
    for r in roles:
        r_dept = (r.get("department") or "").strip().lower()
        r_dept_code = (r.get("department_code") or "").strip().lower()
        dept_match = (
            dept_str == r_dept
            or (dept_str and dept_str in r_dept)
            or (r_dept and r_dept in dept_str)
            or (r_dept_code and r_dept_code in dept_str)
        )
        if dept_match:
            designations = [d.strip().lower() for d in r.get("designations", [])]
            if desig_str in designations or (r.get("role_name", "").strip().lower() == desig_str):
                return r["_id"]
            for d in designations:
                if desig_str and (desig_str in d or d in desig_str):
                    return r["_id"]

    # Step 2: Match designation across any department
    for r in roles:
        designations = [d.strip().lower() for d in r.get("designations", [])]
        if desig_str in designations or (r.get("role_name", "").strip().lower() == desig_str):
            return r["_id"]
        for d in designations:
            if desig_str and (desig_str in d or d in desig_str):
                return r["_id"]

    # Step 3: Match department only (take first matching role in department)
    for r in roles:
        r_dept = (r.get("department") or "").strip().lower()
        r_dept_code = (r.get("department_code") or "").strip().lower()
        if dept_str and (
            dept_str == r_dept
            or dept_str in r_dept
            or r_dept in dept_str
            or (r_dept_code and r_dept_code in dept_str)
        ):
            return r["_id"]

    # Step 4: Fallback to STATISTICAL_OFFICER if present
    for r in roles:
        if r.get("role_code") == "STATISTICAL_OFFICER":
            return r["_id"]

    # Step 5: Fallback to first role
    return roles[0]["_id"]


def reconcile_user_competencies(
    database: Database,
    user_id: str | ObjectId,
    new_role_id: str | ObjectId,
) -> dict:
    """
    Safely reconciles a user's competency profiles when their role or department changes.
    
    Invariants:
    1. Historical evidence records in `competency_evidence` are NEVER deleted.
    2. Historical assessment attempts are NEVER deleted.
    3. New applicable competency profiles are activated / created.
    4. Out-of-scope competency profiles are marked 'inactive' so they do not pollute active skill gaps.
    """
    u_oid = _object_id(user_id)
    r_oid = _object_id(new_role_id)
    if not u_oid or not r_oid:
        return {"reconciled": False, "reason": "Invalid user_id or role_id"}

    now = datetime.now(UTC)

    # 1. Update user's role_id
    database.users.update_one(
        {"_id": u_oid},
        {"$set": {"role_id": r_oid, "updated_at": now}}
    )

    # 2. Get new role requirements
    requirements = list(database.role_requirements.find({"role_id": r_oid}))
    req_comp_ids = [req["competency_id"] for req in requirements if "competency_id" in req]

    # 3. Check existing user profiles
    existing_profiles = list(database.competency_profiles.find({"user_id": u_oid}))
    existing_comp_map = {p["competency_id"]: p for p in existing_profiles if "competency_id" in p}

    # 4. Activate or create profiles for applicable competencies
    activated_count = 0
    created_count = 0
    for comp_id in req_comp_ids:
        if comp_id in existing_comp_map:
            # Re-activate profile if it was inactive
            database.competency_profiles.update_one(
                {"_id": existing_comp_map[comp_id]["_id"]},
                {"$set": {"status": "active", "updated_at": now}}
            )
            activated_count += 1
        else:
            # Check if there is existing authoritative evidence for this competency
            latest_ev = database.competency_evidence.find_one(
                {"user_id": u_oid, "competency_id": comp_id},
                sort=[("created_at", -1)]
            )
            initial_level = float(latest_ev.get("score", 0.0)) if latest_ev and latest_ev.get("score") is not None else None
            initial_conf = float(latest_ev.get("confidence", 0.0)) if latest_ev else 0.0

            database.competency_profiles.insert_one({
                "user_id": u_oid,
                "competency_id": comp_id,
                "current_level": initial_level,
                "level": initial_level,
                "confidence": initial_conf,
                "status": "active",
                "last_assessed_at": latest_ev.get("created_at") if latest_ev else None,
                "created_at": now,
                "updated_at": now,
            })
            created_count += 1

    # 5. Mark non-applicable profiles as inactive (preserving document & evidence)
    deactivated_count = 0
    for comp_id, prof in existing_comp_map.items():
        if comp_id not in req_comp_ids:
            database.competency_profiles.update_one(
                {"_id": prof["_id"]},
                {"$set": {"status": "inactive", "updated_at": now}}
            )
            deactivated_count += 1

    return {
        "reconciled": True,
        "role_id": str(r_oid),
        "applicable_competencies_count": len(req_comp_ids),
        "activated": activated_count,
        "created": created_count,
        "deactivated": deactivated_count,
    }
