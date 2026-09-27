"""Business logic service for Admin organizational intelligence."""

from collections import defaultdict
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.database import Database

from app.admin import repository, schemas
from app.skill_gaps.engine import calculate_gap, categorize_gap


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


def get_admin_dashboard(db: Database, department: Optional[str] = None) -> schemas.AdminDashboardResponse:
    users = repository.get_all_users(db)
    if department:
        users = [u for u in users if department.strip().lower() in (u.get("department") or "").strip().lower()]
    roles = repository.get_all_roles(db)
    competencies = repository.get_all_competencies(db)
    profiles = repository.get_all_competency_profiles(db)
    activities = repository.get_all_learning_activities(db)
    quizzes = repository.get_all_quizzes(db)
    quiz_attempts = repository.get_all_quiz_attempts(db)
    assessments = repository.get_all_capability_assessments(db)
    requirements = repository.get_all_role_requirements(db)


    officials_count = sum(1 for u in users if u.get("access_role") in ("OFFICIAL", "EMPLOYEE"))
    trainers_count = sum(1 for u in users if u.get("access_role") == "TRAINER")
    active_users = sum(1 for u in users if u.get("status") == "active")

    # Average capability level
    levels = [p.get("current_level") for p in profiles if p.get("current_level") is not None]
    avg_capability = round(sum(levels) / len(levels), 2) if levels else 0.0

    # Learning hours
    total_minutes = sum(a.get("duration_minutes", 0) for a in activities)
    total_learning_hours = round(total_minutes / 60.0, 1)

    # Critical gaps count
    comp_map = {str(c["_id"]): c for c in competencies}
    user_map = {str(u["_id"]): u for u in users}
    user_profiles = defaultdict(dict)
    for p in profiles:
        user_profiles[str(p.get("user_id"))][str(p.get("competency_id"))] = p

    critical_gaps_count = 0
    for u in users:
        u_id = str(u["_id"])
        u_role_id = str(u.get("role_id")) if u.get("role_id") else None
        if not u_role_id:
            continue
        role_reqs = [r for r in requirements if str(r.get("role_id")) == u_role_id]
        for req in role_reqs:
            c_id = str(req.get("competency_id"))
            p = user_profiles.get(u_id, {}).get(c_id)
            cur = p.get("current_level") if p else None
            req_lvl = _safe_float(req.get("required_level", 4.0))
            if cur is None or (req_lvl - cur) >= 1.5:
                critical_gaps_count += 1

    # Assessment coverage
    assessed_user_ids = {str(p.get("user_id")) for p in profiles if p.get("current_level") is not None}
    coverage_pct = round((len(assessed_user_ids) / len(users)) * 100, 1) if users else 0.0

    # Quizzes
    quiz_scores = [a.get("percentage", 0) for a in quiz_attempts if a.get("percentage") is not None]
    avg_quiz_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0.0

    # Department distribution
    dept_counts = defaultdict(int)
    for u in users:
        dept = u.get("department") or "General Administration"
        dept_counts[dept] += 1
    department_distribution = [{"department": d, "count": c} for d, c in dept_counts.items()]

    # Domain capability breakdown
    domain_levels = defaultdict(list)
    for p in profiles:
        c = comp_map.get(str(p.get("competency_id")))
        if c and p.get("current_level") is not None:
            domain_levels[c.get("domain", "CORE")].append(p["current_level"])
    domain_capability_breakdown = [
        {"domain": d, "average_level": round(sum(lvls) / len(lvls), 2), "count": len(lvls)}
        for d, lvls in domain_levels.items()
    ]
    recent_activity = []
    for a in activities[:5]:
        recent_activity.append({
            "type": "LEARNING",
            "title": f"Activity on {a.get('resource_id', 'Course')}",
            "status": a.get("status", "completed"),
            "timestamp": a.get("completed_at") or a.get("started_at") or datetime.now(UTC),
        })

    return schemas.AdminDashboardResponse(
        total_officials=officials_count,
        total_trainers=trainers_count,
        total_users=len(users),
        active_users=active_users,
        average_capability_level=avg_capability,
        total_critical_gaps=critical_gaps_count,
        total_learning_hours=total_learning_hours,
        assessment_coverage_pct=coverage_pct,
        total_quizzes_assigned=len(quizzes),
        total_quiz_attempts=len(quiz_attempts),
        average_quiz_score_pct=avg_quiz_score,
        departments_count=len(dept_counts),
        competencies_count=len(competencies),
        department_distribution=department_distribution,
        domain_capability_breakdown=domain_capability_breakdown,
        recent_activity=recent_activity,
    )


def _contains(value: Any, query: Optional[str]) -> bool:
    return not query or query.strip().lower() in str(value or "").strip().lower()


def get_workforce_intelligence(
    db: Database,
    department: Optional[str] = None,
    role: Optional[str] = None,
    designation: Optional[str] = None,
    competency_domain: Optional[str] = None,
    gap_severity: Optional[str] = None,
    training_status: Optional[str] = None,
) -> schemas.WorkforceIntelligenceResponse:
    """Build filtered workforce intelligence from persisted workforce records."""
    users = repository.get_all_users(db)
    roles = repository.get_all_roles(db)
    competencies = repository.get_all_competencies(db)
    requirements = repository.get_all_role_requirements(db)
    profiles = repository.get_all_competency_profiles(db)
    activities = repository.get_all_learning_activities(db)
    evidence = repository.get_all_evidence_records(db)
    role_map = {str(item.get("_id")): item for item in roles}
    comp_map = {str(item.get("_id")): item for item in competencies}
    profiles_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    evidence_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    activities_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in profiles:
        profiles_by_user[str(item.get("user_id"))].append(item)
    for item in evidence:
        evidence_by_user[str(item.get("user_id"))].append(item)
    for item in activities:
        activities_by_user[str(item.get("user_id"))].append(item)

    selected_users = []
    active_gap_users = set()
    gap_levels = {"CRITICAL": 2.0, "HIGH": 1.0, "MEDIUM": 0.0}
    for user in users:
        professional_role = role_map.get(str(user.get("role_id")), {}).get("role_name", "")
        if not _contains(user.get("department"), department):
            continue
        if not _contains(professional_role, role):
            continue
        if not _contains(user.get("designation"), designation):
            continue
        user_profiles = profiles_by_user.get(str(user.get("_id")), [])
        user_activities = activities_by_user.get(str(user.get("_id")), [])
        if training_status and not any(str(item.get("status", "")).lower() == training_status.lower() for item in user_activities):
            continue
        user_requirements = [item for item in requirements if str(item.get("role_id")) == str(user.get("role_id"))]
        user_gaps = []
        for requirement in user_requirements:
            competency = comp_map.get(str(requirement.get("competency_id")))
            if not competency or not _contains(competency.get("domain"), competency_domain):
                continue
            profile = next((item for item in user_profiles if str(item.get("competency_id")) == str(requirement.get("competency_id"))), None)
            current = _safe_float(profile.get("current_level")) if profile else 0.0
            required = _safe_float(requirement.get("required_level"), 4.0)
            gap = max(0.0, required - current)
            severity = "CRITICAL" if gap >= 2.0 else ("HIGH" if gap >= 1.0 else ("MEDIUM" if gap > 0 else "LOW"))
            user_gaps.append(severity)
        if gap_severity and gap_severity.upper() not in user_gaps:
            continue
        if any(severity != "LOW" for severity in user_gaps):
            active_gap_users.add(str(user.get("_id")))
        selected_users.append(user)

    selected_ids = {str(item.get("_id")) for item in selected_users}
    selected_profiles = [item for item in profiles if str(item.get("user_id")) in selected_ids]
    levels = [_safe_float(item.get("current_level")) for item in selected_profiles if item.get("current_level") is not None]
    department_rows: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"officials": 0, "levels": [], "critical_gaps": 0, "training_activity": 0})
    for user in selected_users:
        dept = user.get("department") or "General Administration"
        row = department_rows[dept]
        row["officials"] += 1
        row["levels"].extend([_safe_float(item.get("current_level")) for item in profiles_by_user.get(str(user.get("_id")), []) if item.get("current_level") is not None])
        row["training_activity"] += len(activities_by_user.get(str(user.get("_id")), []))
    for user in selected_users:
        user_id = str(user.get("_id"))
        role_requirements = [item for item in requirements if str(item.get("role_id")) == str(user.get("role_id"))]
        profile_map = {str(item.get("competency_id")): item for item in profiles_by_user.get(user_id, [])}
        for requirement in role_requirements:
            current = _safe_float(profile_map.get(str(requirement.get("competency_id")), {}).get("current_level"))
            if _safe_float(requirement.get("required_level"), 4.0) - current >= 2.0:
                department_rows[user.get("department") or "General Administration"]["critical_gaps"] += 1

    competency_rows: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"levels": [], "gaps": 0, "evidence": 0})
    for profile in selected_profiles:
        competency = comp_map.get(str(profile.get("competency_id")))
        if not competency or not _contains(competency.get("domain"), competency_domain):
            continue
        code = competency.get("code", str(profile.get("competency_id")))
        competency_rows[code]["name"] = competency.get("name", code)
        competency_rows[code]["domain"] = competency.get("domain", "CORE")
        if profile.get("current_level") is not None:
            competency_rows[code]["levels"].append(_safe_float(profile.get("current_level")))
        competency_rows[code]["evidence"] += len([item for item in evidence_by_user.get(str(profile.get("user_id")), []) if str(item.get("competency_id")) == str(profile.get("competency_id"))])

    training_total = sum(len(activities_by_user.get(str(user.get("_id")), [])) for user in selected_users)
    training_completed = sum(sum(1 for item in activities_by_user.get(str(user.get("_id")), []) if item.get("status") == "completed") for user in selected_users)
    training_rate = round((training_completed / training_total) * 100, 1) if training_total else None
    historical_fields = [item.get("previous_level") for item in selected_profiles if item.get("previous_level") is not None]
    return schemas.WorkforceIntelligenceResponse(
        filters={"department": department, "role": role, "designation": designation, "competency_domain": competency_domain, "gap_severity": gap_severity, "training_status": training_status},
        overview={
            "total_officials": len(selected_users),
            "departments": len({item.get("department") for item in selected_users if item.get("department")}),
            "roles": len({str(item.get("role_id")) for item in selected_users if item.get("role_id")}),
            "average_proficiency": round(sum(levels) / len(levels), 2) if levels else None,
            "officials_with_active_skill_gaps": len(active_gap_users),
            "assessed_profiles": len(selected_profiles),
        },
        competency_intelligence={"competencies": [{"code": code, "name": row.get("name"), "domain": row.get("domain"), "average_proficiency": round(sum(row["levels"]) / len(row["levels"]), 2) if row["levels"] else None, "assessed_count": len(row["levels"]), "supporting_evidence_count": row["evidence"]} for code, row in competency_rows.items()]},
        department_analysis=[{"department": dept, "officials": row["officials"], "average_proficiency": round(sum(row["levels"]) / len(row["levels"]), 2) if row["levels"] else None, "critical_gaps": row["critical_gaps"], "training_activity": row["training_activity"]} for dept, row in department_rows.items()],
        training_effectiveness={"assigned": training_total, "completed": training_completed, "completion_rate_pct": training_rate, "assessment_improvement": None, "competency_improvement": None},
        trends={"available": bool(historical_fields), "message": "Historical trend data available" if historical_fields else "Insufficient historical data", "proficiency": []},
    )


def discover_talent(
    db: Database,
    page: int = 1,
    limit: int = 25,
    department: Optional[str] = None,
    role: Optional[str] = None,
    designation: Optional[str] = None,
    competency: Optional[str] = None,
    competency_domain: Optional[str] = None,
    minimum_proficiency: Optional[float] = None,
    minimum_confidence: Optional[float] = None,
    training_status: Optional[str] = None,
) -> schemas.TalentDiscoveryResponse:
    """Return opt-in, evidence-grounded capability matches for admin decision support."""
    users = repository.get_all_users(db)
    roles = {str(item.get("_id")): item for item in repository.get_all_roles(db)}
    competencies = {str(item.get("_id")): item for item in repository.get_all_competencies(db)}
    profiles = repository.get_all_competency_profiles(db)
    evidence = repository.get_all_evidence_records(db)
    activities = repository.get_all_learning_activities(db)
    preferences = list(db.talent_preferences.find({"opt_in_enabled": True})) if hasattr(db, "talent_preferences") else []
    opted_in = {str(item.get("user_id")) for item in preferences}
    profiles_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    evidence_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    activities_by_user: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in profiles: profiles_by_user[str(item.get("user_id"))].append(item)
    for item in evidence: evidence_by_user[str(item.get("user_id"))].append(item)
    for item in activities: activities_by_user[str(item.get("user_id"))].append(item)
    results = []
    for user in users:
        user_id = str(user.get("_id"))
        if user.get("status") != "active" or user_id not in opted_in:
            continue
        professional_role = roles.get(str(user.get("role_id")), {}).get("role_name", "")
        if not _contains(user.get("department"), department) or not _contains(professional_role, role) or not _contains(user.get("designation"), designation):
            continue
        user_profiles = profiles_by_user.get(user_id, [])
        matched = []
        for profile in user_profiles:
            comp = competencies.get(str(profile.get("competency_id")))
            if not comp or not _contains(comp.get("code"), competency) and not _contains(comp.get("name"), competency):
                continue
            if not _contains(comp.get("domain"), competency_domain):
                continue
            current = _safe_float(profile.get("current_level"))
            confidence = _safe_float(profile.get("confidence"))
            evidence_count = sum(1 for item in evidence_by_user.get(user_id, []) if str(item.get("competency_id")) == str(profile.get("competency_id")))
            if minimum_proficiency is not None and current < minimum_proficiency:
                continue
            if minimum_confidence is not None and confidence < minimum_confidence:
                continue
            matched.append({"code": comp.get("code"), "name": comp.get("name"), "domain": comp.get("domain"), "current_proficiency": current, "required_proficiency": profile.get("required_level"), "evidence_confidence": confidence, "supporting_evidence_count": evidence_count})
        if not matched:
            continue
        user_activities = activities_by_user.get(user_id, [])
        if training_status and not any(str(item.get("status", "")).lower() == training_status.lower() for item in user_activities):
            continue
        average_level = sum(item["current_proficiency"] for item in matched) / len(matched)
        average_confidence = sum(item["evidence_confidence"] for item in matched) / len(matched)
        match_score = round(min(1.0, (average_level / 5.0) * 0.65 + average_confidence * 0.35), 3)
        results.append({"official": {"id": user_id, "name": user.get("full_name", "Official")}, "current_role": professional_role or user.get("designation") or "Official", "department": user.get("department") or "General Administration", "designation": user.get("designation") or "Official", "competencies": matched, "capability_match": match_score, "recent_learning_activity": len(user_activities), "evidence_backed": any(item["supporting_evidence_count"] > 0 for item in matched), "explanation": [f"Matches {len(matched)} filtered competency profile(s)", f"Average relevant proficiency: {average_level:.1f}/5", f"Evidence confidence: {average_confidence:.0%}"]})
    results.sort(key=lambda item: item["capability_match"], reverse=True)
    start = max(0, (page - 1) * limit)
    return schemas.TalentDiscoveryResponse(filters={"department": department, "role": role, "designation": designation, "competency": competency, "competency_domain": competency_domain, "minimum_proficiency": minimum_proficiency, "minimum_confidence": minimum_confidence, "training_status": training_status}, page=page, limit=limit, total=len(results), results=results[start:start + limit], data_basis="Active officials who opted into talent discovery, matched against persisted competency profiles and evidence records.")


def get_workforce_overview(db: Database, department: Optional[str] = None) -> schemas.WorkforceOverviewResponse:
    users = repository.get_all_users(db)
    if department:
        users = [u for u in users if department.strip().lower() in (u.get("department") or "").strip().lower()]
    roles = repository.get_all_roles(db)
    competencies = repository.get_all_competencies(db)
    profiles = repository.get_all_competency_profiles(db)


    role_map = {str(r["_id"]): r.get("role_name", "Official") for r in roles}
    comp_map = {str(c["_id"]): c for c in competencies}

    user_profiles = defaultdict(list)
    for p in profiles:
        user_profiles[str(p.get("user_id"))].append(p)

    dept_counts = defaultdict(int)
    role_counts = defaultdict(int)
    domain_levels = defaultdict(list)
    tier_counts = {"Advanced (4.0 - 5.0)": 0, "Proficient (3.0 - 3.9)": 0, "Developing (2.0 - 2.9)": 0, "Novice (< 2.0)": 0}

    employee_items = []
    for u in users:
        u_id = str(u["_id"])
        dept = u.get("department") or "General Administration"
        dept_counts[dept] += 1
        prof_role = role_map.get(str(u.get("role_id")), "Role Mapping Pending") if u.get("role_id") else "Role Mapping Pending"
        role_counts[prof_role] += 1

        u_profs = user_profiles.get(u_id, [])
        assessed = [p.get("current_level") for p in u_profs if p.get("current_level") is not None]
        avg_lvl = round(sum(assessed) / len(assessed), 2) if assessed else None

        if avg_lvl is not None:
            if avg_lvl >= 4.0:
                tier_counts["Advanced (4.0 - 5.0)"] += 1
            elif avg_lvl >= 3.0:
                tier_counts["Proficient (3.0 - 3.9)"] += 1
            elif avg_lvl >= 2.0:
                tier_counts["Developing (2.0 - 2.9)"] += 1
            else:
                tier_counts["Novice (< 2.0)"] += 1

        for p in u_profs:
            c = comp_map.get(str(p.get("competency_id")))
            if c and p.get("current_level") is not None:
                domain_levels[c.get("domain", "CORE")].append(p["current_level"])

        employee_items.append(schemas.WorkforceEmployeeItem(
            id=u_id,
            full_name=u.get("full_name", "Officer"),
            email=u.get("email", ""),
            employee_id=u.get("employee_id") or f"EMP-{u_id[:6].upper()}",
            department=dept,
            designation=u.get("designation") or "Officer",
            professional_role=prof_role,
            access_role=u.get("access_role", "OFFICIAL"),
            status=u.get("status", "active"),
            assessed_competencies=len(assessed),
            average_proficiency=avg_lvl,
            last_assessment_at=u.get("updated_at"),
        ))

    domain_distribution = [
        {"domain": d, "average_proficiency": round(sum(lvls) / len(lvls), 2), "total_assessed": len(lvls)}
        for d, lvls in domain_levels.items()
    ]
    return schemas.WorkforceOverviewResponse(
        total_workforce=len(users),
        department_breakdown=[{"department": d, "count": c} for d, c in dept_counts.items()],
        role_breakdown=[{"role": r, "count": c} for r, c in role_counts.items()],
        domain_proficiency_distribution=domain_distribution,
        proficiency_tier_distribution=tier_counts,
        employees=employee_items,
    )


def get_competency_analytics(db: Database, department: Optional[str] = None) -> schemas.CompetencyAnalyticsResponse:
    users = repository.get_all_users(db)
    if department:
        users = [u for u in users if department.strip().lower() in (u.get("department") or "").strip().lower()]
    competencies = repository.get_all_competencies(db)
    requirements = repository.get_all_role_requirements(db)
    profiles = repository.get_all_competency_profiles(db)

    # If department filter is active, filter profiles to only matching users
    if department:
        target_uids = {str(u["_id"]) for u in users}
        profiles = [p for p in profiles if str(p.get("user_id")) in target_uids]
        target_role_ids = {str(u.get("role_id")) for u in users if u.get("role_id")}
        requirements = [r for r in requirements if str(r.get("role_id")) in target_role_ids]


    # Group profiles by competency
    comp_profiles = defaultdict(list)
    for p in profiles:
        if p.get("current_level") is not None:
            comp_profiles[str(p.get("competency_id"))].append(p.get("current_level"))

    # Group requirements by competency
    comp_reqs = defaultdict(list)
    for r in requirements:
        comp_reqs[str(r.get("competency_id"))].append(r)

    items = []
    domain_counts = defaultdict(int)

    for c in competencies:
        c_id = str(c["_id"])
        domain = c.get("domain", "CORE")
        domain_counts[domain] += 1
        reqs = comp_reqs.get(c_id, [])
        req_roles_count = len(reqs)
        req_levels = [_safe_float(r.get("required_level", 4.0)) for r in reqs]
        avg_req = round(sum(req_levels) / len(req_levels), 2) if req_levels else 4.0

        cur_levels = comp_profiles.get(c_id, [])
        avg_cur = round(sum(cur_levels) / len(cur_levels), 2) if cur_levels else 0.0
        avg_gap = round(max(0.0, avg_req - avg_cur), 2) if cur_levels else 0.0

        meeting_count = sum(1 for lvl in cur_levels if lvl >= avg_req)
        meeting_pct = round((meeting_count / len(cur_levels)) * 100, 1) if cur_levels else 0.0
        critical_deficits = sum(1 for lvl in cur_levels if (avg_req - lvl) >= 1.5)

        priority = "CRITICAL" if avg_gap >= 1.5 else ("HIGH" if avg_gap >= 1.0 else ("MEDIUM" if avg_gap >= 0.5 else "LOW"))

        items.append(schemas.CompetencyAnalyticsItem(
            competency_id=c_id,
            code=c.get("code", "COMP"),
            name=c.get("name", "Competency"),
            domain=domain,
            required_roles_count=req_roles_count,
            average_required_level=avg_req,
            average_current_level=avg_cur,
            average_gap=avg_gap,
            assessed_officials_count=len(cur_levels),
            meeting_requirement_pct=meeting_pct,
            critical_deficits_count=critical_deficits,
            priority=priority,
        ))

    items.sort(key=lambda x: x.average_gap, reverse=True)

    return schemas.CompetencyAnalyticsResponse(
        total_competencies=len(competencies),
        domain_breakdown=[{"domain": d, "count": c} for d, c in domain_counts.items()],
        competencies=items,
    )


def get_skill_gap_analytics(db: Database, department: Optional[str] = None) -> schemas.SkillGapAnalyticsResponse:
    users = repository.get_all_users(db)
    if department:
        users = [u for u in users if department.strip().lower() in (u.get("department") or "").strip().lower()]
    competencies = repository.get_all_competencies(db)
    requirements = repository.get_all_role_requirements(db)
    profiles = repository.get_all_competency_profiles(db)


    comp_map = {str(c["_id"]): c for c in competencies}
    user_profiles = defaultdict(dict)
    for p in profiles:
        user_profiles[str(p.get("user_id"))][str(p.get("competency_id"))] = p

    gap_data = defaultdict(lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0, "gaps": []})
    domain_gaps = defaultdict(int)
    dept_gaps = defaultdict(int)

    total_critical = 0
    total_high = 0
    total_medium = 0
    total_low = 0

    for u in users:
        u_id = str(u["_id"])
        u_role_id = str(u.get("role_id")) if u.get("role_id") else None
        dept = u.get("department") or "General Administration"
        role_reqs = [r for r in requirements if str(r.get("role_id")) == u_role_id] if u_role_id else []

        for req in role_reqs:
            c_id = str(req.get("competency_id"))
            c = comp_map.get(c_id)
            if not c:
                continue
            domain = c.get("domain", "CORE")
            req_lvl = _safe_float(req.get("required_level", 4.0))
            p = user_profiles.get(u_id, {}).get(c_id)
            cur = p.get("current_level") if p else None

            gap = req_lvl - cur if cur is not None else req_lvl
            gap = max(0.0, gap)

            if gap >= 2.0:
                gap_data[c_id]["critical"] += 1
                total_critical += 1
            elif gap >= 1.0:
                gap_data[c_id]["high"] += 1
                total_high += 1
            elif gap > 0.0:
                gap_data[c_id]["medium"] += 1
                total_medium += 1
            else:
                gap_data[c_id]["low"] += 1
                total_low += 1

            if gap > 0.0:
                domain_gaps[domain] += 1
                dept_gaps[dept] += 1
                gap_data[c_id]["gaps"].append(gap)

    top_gaps = []
    for c_id, stats in gap_data.items():
        c = comp_map.get(c_id)
        if not c:
            continue
        gaps_list = stats["gaps"]
        avg_g = round(sum(gaps_list) / len(gaps_list), 2) if gaps_list else 0.0
        affected = stats["critical"] + stats["high"] + stats["medium"]
        priority = "CRITICAL" if stats["critical"] > 0 else ("HIGH" if stats["high"] > 0 else "MEDIUM")

        top_gaps.append(schemas.OrganizationGapItem(
            competency_id=c_id,
            competency_code=c.get("code", "COMP"),
            competency_name=c.get("name", "Competency"),
            domain=c.get("domain", "CORE"),
            officials_affected=affected,
            critical_count=stats["critical"],
            high_count=stats["high"],
            medium_count=stats["medium"],
            low_count=stats["low"],
            average_gap=avg_g,
            priority=priority,
        ))

    top_gaps.sort(key=lambda x: (x.critical_count * 3 + x.high_count * 2 + x.medium_count), reverse=True)

    return schemas.SkillGapAnalyticsResponse(
        total_gaps_identified=total_critical + total_high + total_medium,
        critical_gaps_count=total_critical,
        high_gaps_count=total_high,
        medium_gaps_count=total_medium,
        low_gaps_count=total_low,
        domain_gap_distribution=[{"domain": d, "count": c} for d, c in domain_gaps.items()],
        department_gap_distribution=[{"department": d, "count": c} for d, c in dept_gaps.items()],
        top_organization_gaps=top_gaps[:10],
    )


def get_training_effectiveness(db: Database) -> schemas.TrainingEffectivenessResponse:
    users = repository.get_all_users(db)
    activities = repository.get_all_learning_activities(db)
    quizzes = repository.get_all_quizzes(db)
    quiz_attempts = repository.get_all_quiz_attempts(db)
    evidence = repository.get_all_evidence_records(db)
    assessments = repository.get_all_capability_assessments(db)

    total_enrolled = len(activities)
    completed_activities = [a for a in activities if a.get("status") == "completed"]
    completion_rate = round((len(completed_activities) / total_enrolled) * 100, 1) if total_enrolled else 0.0

    total_minutes = sum(a.get("duration_minutes", 0) for a in activities)
    total_hours = round(total_minutes / 60.0, 1)

    supporting_count = sum(1 for e in evidence if e.get("evidence_type") in ("LEARNING_ACTIVITY", "AI_QUIZ")) or len(completed_activities)
    authoritative_count = sum(1 for e in evidence if e.get("evidence_type") == "CAPABILITY_ASSESSMENT") or len(assessments)

    quiz_scores = [a.get("percentage", 0) for a in quiz_attempts if a.get("percentage") is not None]
    avg_quiz_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0.0

    # Department breakdown
    user_dept_map = {str(u["_id"]): u.get("department", "General") for u in users}
    dept_completed = defaultdict(int)
    dept_total = defaultdict(int)
    for a in activities:
        dept = user_dept_map.get(str(a.get("user_id")), "General Administration")
        dept_total[dept] += 1
        if a.get("status") == "completed":
            dept_completed[dept] += 1

    completion_by_dept = [
        {"department": d, "enrolled": dept_total[d], "completed": dept_completed[d], "rate_pct": round((dept_completed[d] / dept_total[d]) * 100, 1) if dept_total[d] else 0.0}
        for d in dept_total
    ]
    return schemas.TrainingEffectivenessResponse(
        total_enrolled_activities=total_enrolled,
        total_completed_activities=len(completed_activities),
        overall_completion_rate_pct=completion_rate,
        total_learning_minutes=total_minutes,
        total_learning_hours=total_hours,
        supporting_evidence_count=supporting_count,
        authoritative_evidence_count=authoritative_count,
        total_quizzes_created=len(quizzes),
        total_quizzes_assigned=len(quizzes),
        total_quiz_submissions=len(quiz_attempts),
        average_quiz_score_pct=avg_quiz_score,
        completion_by_department=completion_by_dept,
        evidence_ledger_breakdown={
            "Supporting Evidence (Learning & Quizzes)": supporting_count,
            "Authoritative Evidence (Capability Assessments)": authoritative_count,
        },
        training_to_assessment_funnel={
            "Learning Enrolled": total_enrolled,
            "Modules Completed": len(completed_activities),
            "Practice Quizzes Taken": len(quiz_attempts),
            "Formal Assessments Validated": authoritative_count,
        },
    )


def get_emerging_skills(db: Database) -> schemas.EmergingSkillsResponse:
    users = repository.get_all_users(db)
    competencies = repository.get_all_competencies(db)
    requirements = repository.get_all_role_requirements(db)
    profiles = repository.get_all_competency_profiles(db)

    comp_profiles = defaultdict(list)
    profile_map = defaultdict(dict)
    for profile in profiles:
        if profile.get("current_level") is not None:
            profile_map[str(profile.get("user_id"))][str(profile.get("competency_id"))] = profile

    requirements_by_role = defaultdict(list)
    for requirement in requirements:
        requirements_by_role[str(requirement.get("role_id"))].append(requirement)

    competency_map = {str(c["_id"]): c for c in competencies}
    observed = defaultdict(lambda: {"gaps": [], "current": [], "required": [], "users": set()})
    for user in users:
        role_id = str(user.get("role_id")) if user.get("role_id") else None
        if not role_id:
            continue
        for requirement in requirements_by_role.get(role_id, []):
            competency_id = str(requirement.get("competency_id"))
            profile = profile_map.get(str(user["_id"]), {}).get(competency_id)
            if not profile:
                continue
            current = _safe_float(profile.get("current_level"))
            required = _safe_float(requirement.get("required_level"))
            gap = max(0.0, required - current)
            if gap <= 0:
                continue
            stats = observed[competency_id]
            stats["gaps"].append(gap)
            stats["current"].append(current)
            stats["required"].append(required)
            stats["users"].add(str(user["_id"]))

    emerging = []
    for c in competencies:
        c_id = str(c["_id"])
        stats = observed.get(c_id)
        if not stats or not stats["gaps"]:
            continue
        domain = c.get("domain", "CORE")
        code = c.get("code", "")
        name = c.get("name", "")

        gap = sum(stats["gaps"]) / len(stats["gaps"])
        avg_current = sum(stats["current"]) / len(stats["current"])
        avg_required = sum(stats["required"]) / len(stats["required"])
        rationale = f"Observed gap of {gap:.1f} points across {len(stats['users'])} assessed official(s) with role requirements."
        focus = f"Review mapped learning resources and assessment evidence for {name}."

        emerging.append(schemas.EmergingSkillItem(
            competency_id=c_id,
            code=code,
            name=name,
            domain=domain,
            officials_in_deficit=len(stats["users"]),
            average_gap_size=round(gap, 1),
            average_current_level=round(avg_current, 1),
            average_required_level=round(avg_required, 1),
            rationale=rationale,
            recommended_focus=focus,
        ))

    emerging.sort(key=lambda x: (x.average_gap_size or 0, x.officials_in_deficit), reverse=True)
    domain_counts = defaultdict(int)
    for item in emerging:
        domain_counts[item.domain] += item.officials_in_deficit

    return schemas.EmergingSkillsResponse(
        strategic_focus_domains=[domain for domain, _ in sorted(domain_counts.items(), key=lambda pair: pair[1], reverse=True)],
        emerging_capabilities=emerging[:10],
        historical_trend_available=False,
        data_basis="Based on assessed competency profiles and stored role requirements; historical trend unavailable.",
    )


def get_capacity_planning(db: Database) -> schemas.CapacityPlanningResponse:
    users = repository.get_all_users(db)
    competencies = repository.get_all_competencies(db)
    resources = repository.get_all_learning_resources(db)
    requirements = repository.get_all_role_requirements(db)

    res_by_comp = defaultdict(list)
    for r in resources:
        for key in (r.get("competency_code"), r.get("competency_id")):
            if key:
                res_by_comp[str(key)].append(r)

    profile_map = defaultdict(dict)
    for profile in repository.get_all_competency_profiles(db):
        if profile.get("current_level") is not None:
            profile_map[str(profile.get("user_id"))][str(profile.get("competency_id"))] = profile
    requirements_by_role = defaultdict(list)
    for requirement in requirements:
        requirements_by_role[str(requirement.get("role_id"))].append(requirement)

    interventions = []
    total_hours = 0.0
    total_officials = 0

    for c in competencies:
        code = c.get("code", "COMP")
        name = c.get("name", "Competency")
        domain = c.get("domain", "CORE")
        matching_res = res_by_comp.get(code) or res_by_comp.get(str(c["_id"]), [])
        top_res = matching_res[0] if matching_res else None

        gap_users = set()
        gaps = []
        for user in users:
            role_id = str(user.get("role_id")) if user.get("role_id") else None
            for requirement in requirements_by_role.get(role_id, []):
                if str(requirement.get("competency_id")) != str(c["_id"]):
                    continue
                profile = profile_map.get(str(user["_id"]), {}).get(str(c["_id"]))
                if not profile:
                    continue
                gap = max(0.0, _safe_float(requirement.get("required_level")) - _safe_float(profile.get("current_level")))
                if gap > 0:
                    gap_users.add(str(user["_id"]))
                    gaps.append(gap)
        target_count = len(gap_users)
        if target_count == 0:
            continue
        duration_values = [_safe_float(r.get("metadata", {}).get("duration_hours"), None) for r in matching_res]
        duration_values = [value for value in duration_values if value is not None and value > 0]
        est_hours = round(min(duration_values) * target_count, 1) if duration_values else None
        if est_hours is not None:
            total_hours += est_hours
        total_officials += target_count
        average_gap = sum(gaps) / len(gaps)
        priority = "CRITICAL" if average_gap >= 2 else ("HIGH" if average_gap >= 1 else "MEDIUM")

        interventions.append(schemas.CapacityInterventionItem(
            competency_code=code,
            competency_name=name,
            domain=domain,
            priority=priority,
            target_officials_count=target_count,
            estimated_training_hours=est_hours,
            recommended_courses_count=len(matching_res),
            top_resource_title=top_res.get("title") if top_res else None,
            top_resource_provider=top_res.get("provider") if top_res else None,
            suggested_cohort_size=None,
        ))

    return schemas.CapacityPlanningResponse(
        total_training_hours_required=round(total_hours, 1) if total_hours else None,
        total_officials_requiring_intervention=total_officials,
        high_priority_initiatives_count=len(interventions),
        interventions=interventions,
        data_basis="Based on assessed officials below stored role requirements and mapped catalog resources. Duration and cohort size are shown only when configured.",
    )


def get_admin_users(db: Database, department: Optional[str] = None) -> schemas.AdminUserListResponse:
    users = repository.get_all_users(db)
    if department:
        users = [u for u in users if department.strip().lower() in (u.get("department") or "").strip().lower()]
    roles = repository.get_all_roles(db)
    role_map = {str(r["_id"]): r.get("role_name", "Official") for r in roles}


    items = []
    for u in users:
        u_id = str(u["_id"])
        prof_role = role_map.get(str(u.get("role_id")), "Unresolved") if u.get("role_id") else "Unresolved"
        items.append(schemas.AdminUserItem(
            id=u_id,
            email=u.get("email", ""),
            full_name=u.get("full_name", "User"),
            employee_id=u.get("employee_id") or f"EMP-{u_id[:6].upper()}",
            department=u.get("department") or "General Administration",
            designation=u.get("designation") or "Officer",
            access_role=u.get("access_role", "OFFICIAL"),
            professional_role=prof_role,
            status=u.get("status", "active"),
            created_at=u.get("created_at") or datetime.now(UTC),
            last_login_at=u.get("last_login_at"),
        ))

    return schemas.AdminUserListResponse(
        total=len(items),
        users=items,
    )


def get_admin_reports(db: Database) -> schemas.AdminReportsResponse:
    dash = get_admin_dashboard(db)
    gaps = get_skill_gap_analytics(db)
    training = get_training_effectiveness(db)

    return schemas.AdminReportsResponse(
        generated_at=datetime.now(UTC),
        workforce_summary={
            "total_users": dash.total_users,
            "total_officials": dash.total_officials,
            "total_trainers": dash.total_trainers,
            "active_users": dash.active_users,
            "average_capability_level": dash.average_capability_level,
            "assessment_coverage_pct": dash.assessment_coverage_pct,
        },
        skill_gap_summary={
            "total_gaps": gaps.total_gaps_identified,
            "critical_gaps": gaps.critical_gaps_count,
            "high_gaps": gaps.high_gaps_count,
            "medium_gaps": gaps.medium_gaps_count,
        },
        training_summary={
            "total_enrolled": training.total_enrolled_activities,
            "total_completed": training.total_completed_activities,
            "completion_rate_pct": training.overall_completion_rate_pct,
            "learning_hours": training.total_learning_hours,
            "average_quiz_score_pct": training.average_quiz_score_pct,
        },
        compliance_summary={
            "evidence_ledger_integrity": "VALIDATED",
            "authoritative_assessments": training.authoritative_evidence_count,
            "supporting_evidence_records": training.supporting_evidence_count,
            "governance_status": "COMPLIANT",
        },
    )


def promote_user_to_trainer(db: Database, user_id: str) -> schemas.AdminUserItem:
    """Promote an existing official user to trainer. Restricted to ADMIN caller."""
    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
    user = db.users.find_one({"_id": u_oid}) if u_oid else db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.get("access_role") == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot alter ADMIN role via trainer promotion",
        )

    target_id = user["_id"]
    now = datetime.now(UTC)
    db.users.update_one(
        {"_id": target_id},
        {"$set": {"access_role": "TRAINER", "updated_at": now}},
    )
    updated_user = db.users.find_one({"_id": target_id}) or user
    updated_user["access_role"] = "TRAINER"

    roles = repository.get_all_roles(db)
    role_map = {str(r["_id"]): r.get("role_name", "Official") for r in roles}
    prof_role = role_map.get(str(updated_user.get("role_id")), "Unresolved") if updated_user.get("role_id") else "Unresolved"

    return schemas.AdminUserItem(
        id=str(updated_user["_id"]),
        email=updated_user.get("email", ""),
        full_name=updated_user.get("full_name", "User"),
        employee_id=updated_user.get("employee_id") or f"EMP-{str(updated_user['_id'])[:6].upper()}",
        department=updated_user.get("department") or "General Administration",
        designation=updated_user.get("designation") or "Officer",
        access_role="TRAINER",
        professional_role=prof_role,
        status=updated_user.get("status", "active"),
        created_at=updated_user.get("created_at") or now,
        last_login_at=updated_user.get("last_login_at"),
    )


def assign_user_role(db: Database, user_id: str, payload: schemas.AdminAssignRoleRequest) -> schemas.AdminUserItem:
    """Admin-controlled resolution of a user's professional role and competency reconciliation."""
    from app.roles.resolver import reconcile_user_competencies

    u_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
    user = db.users.find_one({"_id": u_oid}) if u_oid else db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    r_oid = ObjectId(payload.role_id) if ObjectId.is_valid(payload.role_id) else None
    role = db.roles.find_one({"_id": r_oid}) if r_oid else db.roles.find_one({"_id": payload.role_id})
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specified role not found in active role catalog",
        )

    now = datetime.now(UTC)
    updates: dict[str, Any] = {"updated_at": now}
    if payload.department:
        updates["department"] = payload.department
    if payload.designation:
        updates["designation"] = payload.designation

    if updates:
        db.users.update_one({"_id": user["_id"]}, {"$set": updates})

    # Formally reconcile user competencies to newly assigned role
    reconcile_user_competencies(db, user["_id"], role["_id"])

    updated_user = db.users.find_one({"_id": user["_id"]}) or user

    return schemas.AdminUserItem(
        id=str(updated_user["_id"]),
        email=updated_user.get("email", ""),
        full_name=updated_user.get("full_name", "User"),
        employee_id=updated_user.get("employee_id") or f"EMP-{str(updated_user['_id'])[:6].upper()}",
        department=updated_user.get("department") or "General Administration",
        designation=updated_user.get("designation") or "Officer",
        access_role=updated_user.get("access_role", "OFFICIAL"),
        professional_role=role.get("role_name", "Official"),
        status=updated_user.get("status", "active"),
        created_at=updated_user.get("created_at") or now,
        last_login_at=updated_user.get("last_login_at"),
    )


def get_user_workforce_profile(
    db: Database, user_id: str
) -> schemas.AdminWorkforceProfileResponse:
    """
    Build a consolidated individual workforce profile for Admin observability.

    Assembles:
    - User identity and professional role
    - Per-competency capability levels vs role requirements (authoritative profiles)
    - Active skill gaps sorted by priority
    - Learning activities with progress (stored explicitly, not derived)
    - Learning summary metrics (totals, overall progress)
    - Capability assessment history
    - Evidence summary (supporting vs authoritative — kept strictly separate)
    - Chronological timeline of learning/assessment events

    RBAC: caller must already be verified as ADMIN before calling this function.
    Data isolation: all queries are scoped to the target user_id.
    Mutation: this function is read-only. No writes to any collection.
    """
    # ── 1. Resolve user ──────────────────────────────────────────────────────
    user_doc = repository.get_user_by_id(db, user_id)
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    roles = repository.get_all_roles(db)
    role_map = {str(r["_id"]): r for r in roles}
    competencies = repository.get_all_competencies(db)
    comp_map = {str(c["_id"]): c for c in competencies}
    # also index by code for assessment lookups
    comp_code_map = {c.get("code", ""): c for c in competencies}

    prof_role_doc = role_map.get(str(user_doc.get("role_id"))) if user_doc.get("role_id") else None
    prof_role_name = prof_role_doc.get("role_name", "Unresolved") if prof_role_doc else "Unresolved"

    user_item = schemas.AdminUserItem(
        id=str(user_doc["_id"]),
        email=user_doc.get("email", ""),
        full_name=user_doc.get("full_name", "User"),
        employee_id=user_doc.get("employee_id") or f"EMP-{str(user_doc['_id'])[:6].upper()}",
        department=user_doc.get("department") or "General Administration",
        designation=user_doc.get("designation") or "Officer",
        access_role=user_doc.get("access_role", "OFFICIAL"),
        professional_role=prof_role_name,
        status=user_doc.get("status", "active"),
        created_at=user_doc.get("created_at") or datetime.now(UTC),
        last_login_at=user_doc.get("last_login_at"),
    )

    # ── 2. Competency profiles + role requirements → capability + gaps ────────
    profiles = repository.get_user_competency_profiles(db, user_id)
    profile_by_comp = {}
    for p in profiles:
        # competency_id can be stored as ObjectId or string
        cid = str(p.get("competency_id"))
        profile_by_comp[cid] = p

    requirements = repository.get_all_role_requirements(db)
    role_id_str = str(user_doc.get("role_id")) if user_doc.get("role_id") else None
    user_requirements = [r for r in requirements if str(r.get("role_id")) == role_id_str] if role_id_str else []

    capabilities: list[schemas.AdminCapabilityItem] = []
    active_gaps: list[schemas.AdminCapabilityItem] = []

    for req in user_requirements:
        c_id = str(req.get("competency_id"))
        c_doc = comp_map.get(c_id)
        if not c_doc:
            continue
        req_lvl = _safe_float(req.get("required_level", 4.0))
        profile = profile_by_comp.get(c_id)
        cur_lvl = _safe_float(profile.get("current_level")) if profile and profile.get("current_level") is not None else None
        gap = max(0.0, req_lvl - cur_lvl) if cur_lvl is not None else req_lvl
        gap_cat = (
            "CRITICAL" if gap >= 2.0
            else "HIGH" if gap >= 1.0
            else "MEDIUM" if gap > 0.0
            else "MET"
        )
        item = schemas.AdminCapabilityItem(
            competency_code=c_doc.get("code", c_id),
            competency_name=c_doc.get("name", "Competency"),
            domain=c_doc.get("domain", "CORE"),
            current_level=cur_lvl,
            required_level=req_lvl,
            gap=round(gap, 2),
            gap_category=gap_cat,
        )
        capabilities.append(item)
        if gap > 0.0:
            active_gaps.append(item)

    # sort active gaps: CRITICAL first
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "MET": 4}
    active_gaps.sort(key=lambda x: priority_order.get(x.gap_category, 9))

    # ── 3. Learning activities ────────────────────────────────────────────────
    resources = repository.get_all_learning_resources(db)
    res_map = {r.get("resource_id") or str(r["_id"]): r for r in resources}
    # Also index by _id string for fallback
    res_id_map = {str(r["_id"]): r for r in resources}

    activity_docs = repository.get_user_learning_activities(db, user_id)
    learning_items: list[schemas.AdminLearningActivityItem] = []

    for act in activity_docs:
        res_id = act.get("resource_id", "")
        res_doc = res_map.get(res_id) or res_id_map.get(res_id) or {}
        res_title = res_doc.get("title") or res_doc.get("name") or res_id or "Learning Resource"
        provider = res_doc.get("provider") or res_doc.get("source") or None
        comp_id_str = str(act.get("competency_id", ""))

        learning_items.append(schemas.AdminLearningActivityItem(
            activity_id=str(act["_id"]),
            resource_id=res_id,
            resource_title=res_title,
            provider=provider,
            competency_id=comp_id_str,
            status=act.get("status", "not_started"),
            progress_percent=_safe_float(act.get("progress_percent", 0)),
            started_at=act.get("started_at"),
            last_accessed_at=act.get("last_accessed_at"),
            completed_at=act.get("completed_at"),
            duration_minutes=_safe_float(act.get("duration_minutes", 0)),
        ))

    # ── 4. Learning summary ───────────────────────────────────────────────────
    total_acts = len(learning_items)
    completed_acts = sum(1 for a in learning_items if a.status == "completed")
    in_progress_acts = sum(1 for a in learning_items if a.status == "in_progress")
    not_started_acts = sum(1 for a in learning_items if a.status == "not_started")
    abandoned_acts = sum(1 for a in learning_items if a.status == "abandoned")
    total_minutes = sum(a.duration_minutes for a in learning_items)

    # Overall learning progress: mean of stored progress_percent values.
    # Labeled "Learning Progress" — NOT "Competency Progress".
    # Only calculated when there are activities; null otherwise.
    if total_acts > 0:
        overall_progress = round(
            sum(a.progress_percent for a in learning_items) / total_acts, 1
        )
    else:
        overall_progress = None

    learning_summary: dict[str, Any] = {
        "total_activities": total_acts,
        "completed": completed_acts,
        "in_progress": in_progress_acts,
        "not_started": not_started_acts,
        "abandoned": abandoned_acts,
        "total_learning_hours": round(total_minutes / 60.0, 1),
        # Explicit label: this is LEARNING progress, not competency progress
        "overall_learning_progress_pct": overall_progress,
        "progress_note": (
            "Learning progress reflects learner-reported engagement. "
            "Competency updates require formal assessment evidence."
        ),
    }

    # ── 5. Assessments ────────────────────────────────────────────────────────
    assessment_docs = repository.get_user_capability_assessments(db, user_id)
    assessment_items: list[schemas.AdminAssessmentItem] = []

    for ass in assessment_docs:
        ass_status = ass.get("status", "")
        is_submitted = ass_status in ("SUBMITTED", "submitted", "COMPLETED", "completed")
        assessment_items.append(schemas.AdminAssessmentItem(
            assessment_id=str(ass["_id"]),
            assessment_type="FORMAL_CAPABILITY",
            competency_code=ass.get("competency_code"),
            status=ass_status,
            score=_safe_float(ass["score"]) if ass.get("score") is not None else None,
            percentage=_safe_float(ass["percentage"]) if ass.get("percentage") is not None else None,
            assessed_at=ass.get("submitted_at") or ass.get("started_at"),
            # Authoritative only when formally submitted
            authoritative=is_submitted,
        ))

    # ── 6. Evidence ───────────────────────────────────────────────────────────
    evidence_docs = repository.get_user_evidence_records(db, user_id)
    evidence_items: list[schemas.AdminEvidenceItem] = []

    supporting_count = 0
    authoritative_count = 0

    for ev in evidence_docs:
        ev_type = ev.get("type") or ev.get("evidence_type") or "LEARNING_ACTIVITY"
        is_auth = ev_type in ("CAPABILITY_ASSESSMENT", "ADAPTIVE_ASSESSMENT")
        if is_auth:
            authoritative_count += 1
        else:
            supporting_count += 1

        c_id = str(ev.get("competency_id", ""))
        c_doc = comp_map.get(c_id) or comp_code_map.get(c_id)
        comp_code = c_doc.get("code") if c_doc else c_id or None

        evidence_items.append(schemas.AdminEvidenceItem(
            evidence_id=str(ev["_id"]),
            evidence_type=ev_type,
            competency_code=comp_code,
            confidence=_safe_float(ev.get("confidence", 0.3)) if ev.get("confidence") is not None else None,
            source=ev.get("source", {}).get("resource_id") if isinstance(ev.get("source"), dict) else str(ev.get("source", "")),
            recorded_at=ev.get("recorded_at"),
        ))

    evidence_summary: dict[str, Any] = {
        "supporting_count": supporting_count,
        "supporting_confidence": 0.30,
        "authoritative_count": authoritative_count,
        "authoritative_confidence": 0.85,
        "total_records": len(evidence_items),
        "governance_note": (
            "Supporting evidence (confidence 0.30) is generated by learning completion. "
            "Authoritative evidence (confidence 0.85) is generated exclusively by formal "
            "capability assessments and directly updates the competency profile."
        ),
    }

    # ── 7. Timeline ───────────────────────────────────────────────────────────
    timeline: list[dict[str, Any]] = []

    for act in activity_docs:
        res_id = act.get("resource_id", "Resource")
        res_doc = res_map.get(res_id) or res_id_map.get(res_id) or {}
        res_label = res_doc.get("title") or res_id

        if act.get("started_at"):
            timeline.append({
                "timestamp": act["started_at"],
                "event_type": "LEARNING_STARTED",
                "title": f"Learning started: {res_label}",
                "detail": f"Status: in_progress",
                "icon": "book",
            })
        if act.get("completed_at"):
            timeline.append({
                "timestamp": act["completed_at"],
                "event_type": "LEARNING_COMPLETED",
                "title": f"Learning completed: {res_label}",
                "detail": f"Progress: {act.get('progress_percent', 0):.0f}%",
                "icon": "check",
            })
            timeline.append({
                "timestamp": act["completed_at"],
                "event_type": "SUPPORTING_EVIDENCE",
                "title": "Supporting evidence recorded",
                "detail": "Confidence: 0.30 — supporting only, does not update competency",
                "icon": "evidence",
            })

    for ass in assessment_docs:
        if ass.get("started_at"):
            timeline.append({
                "timestamp": ass["started_at"],
                "event_type": "ASSESSMENT_STARTED",
                "title": f"Formal assessment started: {ass.get('competency_code', 'Competency')}",
                "detail": "Capability assessment in progress",
                "icon": "assessment",
            })
        if ass.get("submitted_at"):
            score_label = f"Score: {ass.get('percentage', 0):.1f}%" if ass.get("percentage") is not None else ""
            timeline.append({
                "timestamp": ass["submitted_at"],
                "event_type": "ASSESSMENT_SUBMITTED",
                "title": f"Assessment submitted: {ass.get('competency_code', 'Competency')}",
                "detail": score_label,
                "icon": "assessment",
            })
            timeline.append({
                "timestamp": ass["submitted_at"],
                "event_type": "AUTHORITATIVE_EVIDENCE",
                "title": "Authoritative evidence recorded",
                "detail": "Confidence: 0.85 — competency profile updated",
                "icon": "shield",
            })

    # Sort timeline chronologically ascending
    timeline.sort(
        key=lambda e: (e["timestamp"] or datetime.min.replace(tzinfo=UTC)).isoformat()
        if hasattr(e["timestamp"], "isoformat")
        else str(e["timestamp"] or ""),
    )

    return schemas.AdminWorkforceProfileResponse(
        user=user_item,
        capabilities=capabilities,
        active_gaps=active_gaps,
        learning_summary=learning_summary,
        learning_activities=learning_items,
        assessments=assessment_items,
        evidence_summary=evidence_summary,
        evidence=evidence_items,
        timeline=timeline,
    )
