"""User-isolated capability context builder for Karmayogi AI Co-Pilot."""

from typing import Dict, Any, List, Optional
from pymongo.database import Database
from bson import ObjectId

from app.skill_gaps.service import calculate_skill_gaps
from app.learning_resources.service import RecommendationService


def build_user_capability_context(
    database: Database,
    user_id: str,
    active_competency_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Constructs a scoped, privacy-isolated capability summary for the LLM.
    Does NOT dump the whole database; only extracts the requesting official's state.
    """
    user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
    if not user_oid:
        return {}

    user = database.users.find_one({"_id": user_oid})
    if not user:
        return {}

    # 1. User Metadata
    role_doc = database.roles.find_one({"_id": user.get("role_id")}) if user.get("role_id") else None
    role_name = role_doc.get("role_name") if role_doc else (user.get("designation") or "Civil Services Official")
    role_code = role_doc.get("role_code") if role_doc else "OFFICIAL"

    profile_summary = {
        "full_name": user.get("full_name", "Officer"),
        "designation": user.get("designation", "Civil Services Official"),
        "department": user.get("department", "Government of India"),
        "role_name": role_name,
        "role_code": role_code,
        "access_role": user.get("access_role", "OFFICIAL"),
    }


    # 2. Skill Gaps Calculation
    gaps_list = []
    top_gaps = []
    try:
        gap_response = calculate_skill_gaps(database, user_id)
        raw_gaps = gap_response.gaps or []
        for g in raw_gaps:
            g_dict = g.model_dump() if hasattr(g, "model_dump") else g
            gaps_list.append({
                "competency_code": g_dict.get("competency_code"),
                "competency_name": g_dict.get("competency_name"),
                "current_level": g_dict.get("current_level", 0.0),
                "required_level": g_dict.get("required_level", 0.0),
                "gap": g_dict.get("gap", 0.0),
                "priority": g_dict.get("priority", "MEDIUM"),
            })
        # Sort by gap size descending
        gaps_list.sort(key=lambda x: x["gap"], reverse=True)
        top_gaps = gaps_list[:5]
    except Exception:
        pass

    # 3. Top Recommendations
    recs_list = []
    try:
        rec_service = RecommendationService(database)
        rec_resp = rec_service.get_recommendations_for_user(user_id, limit=5)
        for r in rec_resp.recommendations:
            res = r.resource
            recs_list.append({
                "resource_id": res.resource_id,
                "title": res.title,
                "provider": r.provider,
                "competency_code": r.competency_code,
                "gap": r.gap,
                "score": round(r.score, 2),
                "url": res.provider_specific.course_url or res.source.source_url,
                "source_doc": res.source.source_document,
            })
    except Exception:
        pass

    # 4. Learning Activity & Evidence Summary
    active_learning = []
    completed_learning = []
    try:
        activities = list(database.learning_activities.find({"user_id": user_oid}))
        for a in activities:
            item = {
                "resource_id": a.get("resource_id"),
                "status": a.get("status"),
                "progress": a.get("progress_percent", 0),
            }
            if a.get("status") == "completed":
                completed_learning.append(item)
            else:
                active_learning.append(item)
    except Exception:
        pass

    # 5. Evidence Ledger Counts
    supporting_count = 0
    authoritative_count = 0
    try:
        evidence_docs = list(database.competency_evidence.find({"user_id": user_oid}))
        for ev in evidence_docs:
            if ev.get("type") in ("LEARNING_ACTIVITY", "AI_QUIZ"):
                supporting_count += 1
            elif ev.get("type") == "CAPABILITY_ASSESSMENT":
                authoritative_count += 1
    except Exception:
        pass

    return {
        "profile": profile_summary,
        "top_gaps": top_gaps,
        "total_gaps_count": len(gaps_list),
        "recommendations": recs_list,
        "active_learning_count": len(active_learning),
        "completed_learning_count": len(completed_learning),
        "supporting_evidence_count": supporting_count,
        "authoritative_evidence_count": authoritative_count,
        "active_competency_code": active_competency_code,
    }
