from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pymongo.database import Database

from app.admin import schemas, service
from app.auth.dependencies import require_admin_role
from app.core.analytics_cache import (
    get_admin_dashboard_cache,
    set_admin_dashboard_cache,
    get_admin_workforce_cache,
    set_admin_workforce_cache,
    get_admin_competencies_cache,
    set_admin_competencies_cache,
    get_admin_skill_gaps_cache,
    set_admin_skill_gaps_cache,
    invalidate_admin_cache,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Organizational Intelligence"],
    dependencies=[Depends(require_admin_role)],
)


def _get_db(request: Request) -> Database:
    db = getattr(request.app.state, "database", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return db


@router.get(
    "/dashboard",
    response_model=schemas.AdminDashboardResponse,
    summary="Get executive admin dashboard metrics",
)
def get_dashboard(
    request: Request,
    department: Optional[str] = Query(None, description="Filter metrics by department"),
) -> schemas.AdminDashboardResponse:
    cached = get_admin_dashboard_cache(department)
    if cached is not None:
        return cached
    db = _get_db(request)
    data = service.get_admin_dashboard(db, department=department)
    set_admin_dashboard_cache(data, department)
    return data


@router.get(
    "/workforce",
    response_model=schemas.WorkforceOverviewResponse,
    summary="Get workforce breakdown and capability distribution",
)
def get_workforce(
    request: Request,
    department: Optional[str] = Query(None, description="Filter workforce by department"),
) -> schemas.WorkforceOverviewResponse:
    cached = get_admin_workforce_cache(department)
    if cached is not None:
        return cached
    db = _get_db(request)
    data = service.get_workforce_overview(db, department=department)
    set_admin_workforce_cache(data, department)
    return data


@router.get(
    "/competencies",
    response_model=schemas.CompetencyAnalyticsResponse,
    summary="Get organization-wide competency analytics",
)
def get_competencies(
    request: Request,
    department: Optional[str] = Query(None, description="Filter competency analytics by department"),
) -> schemas.CompetencyAnalyticsResponse:
    cached = get_admin_competencies_cache(department)
    if cached is not None:
        return cached
    db = _get_db(request)
    data = service.get_competency_analytics(db, department=department)
    set_admin_competencies_cache(data, department)
    return data


@router.get(
    "/skill-gaps",
    response_model=schemas.SkillGapAnalyticsResponse,
    summary="Get organization-wide skill gap analytics",
)
def get_skill_gaps(
    request: Request,
    department: Optional[str] = Query(None, description="Filter skill gap analytics by department"),
) -> schemas.SkillGapAnalyticsResponse:
    cached = get_admin_skill_gaps_cache(department)
    if cached is not None:
        return cached
    db = _get_db(request)
    data = service.get_skill_gap_analytics(db, department=department)
    set_admin_skill_gaps_cache(data, department)
    return data


@router.get(
    "/workforce-intelligence",
    response_model=schemas.WorkforceIntelligenceResponse,
    summary="Get filtered government workforce capability intelligence",
)
def get_workforce_intelligence(
    request: Request,
    department: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    designation: Optional[str] = Query(None),
    competency_domain: Optional[str] = Query(None),
    gap_severity: Optional[str] = Query(None),
    training_status: Optional[str] = Query(None),
) -> schemas.WorkforceIntelligenceResponse:
    db = _get_db(request)
    return service.get_workforce_intelligence(
        db,
        department=department,
        role=role,
        designation=designation,
        competency_domain=competency_domain,
        gap_severity=gap_severity,
        training_status=training_status,
    )


@router.get(
    "/talent-discovery",
    response_model=schemas.TalentDiscoveryResponse,
    summary="Discover opt-in, evidence-backed workforce capabilities",
)
def get_talent_discovery(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    department: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    designation: Optional[str] = Query(None),
    competency: Optional[str] = Query(None),
    competency_domain: Optional[str] = Query(None),
    minimum_proficiency: Optional[float] = Query(None, ge=0, le=5),
    minimum_confidence: Optional[float] = Query(None, ge=0, le=1),
    training_status: Optional[str] = Query(None),
) -> schemas.TalentDiscoveryResponse:
    db = _get_db(request)
    return service.discover_talent(
        db,
        page=page,
        limit=limit,
        department=department,
        role=role,
        designation=designation,
        competency=competency,
        competency_domain=competency_domain,
        minimum_proficiency=minimum_proficiency,
        minimum_confidence=minimum_confidence,
        training_status=training_status,
    )


@router.get(
    "/training-effectiveness",
    response_model=schemas.TrainingEffectivenessResponse,
    summary="Get training effectiveness and evidence metrics",
)
def get_training_effectiveness(request: Request) -> schemas.TrainingEffectivenessResponse:
    db = _get_db(request)
    return service.get_training_effectiveness(db)


@router.get(
    "/emerging-skills",
    response_model=schemas.EmergingSkillsResponse,
    summary="Get emerging skill requirements and strategic capability needs",
)
def get_emerging_skills(request: Request) -> schemas.EmergingSkillsResponse:
    db = _get_db(request)
    return service.get_emerging_skills(db)


@router.get(
    "/capacity-planning",
    response_model=schemas.CapacityPlanningResponse,
    summary="Get organizational capacity planning recommendations",
)
def get_capacity_planning(request: Request) -> schemas.CapacityPlanningResponse:
    db = _get_db(request)
    return service.get_capacity_planning(db)


@router.get(
    "/users",
    response_model=schemas.AdminUserListResponse,
    summary="Get organizational user directory",
)
def get_users(
    request: Request,
    department: Optional[str] = Query(None, description="Filter users by department"),
) -> schemas.AdminUserListResponse:
    db = _get_db(request)
    return service.get_admin_users(db, department=department)


@router.get(
    "/reports",
    response_model=schemas.AdminReportsResponse,
    summary="Get consolidated intelligence reports",
)
def get_reports(request: Request) -> schemas.AdminReportsResponse:
    db = _get_db(request)
    return service.get_admin_reports(db)


@router.get(
    "/users/{user_id}/profile",
    response_model=schemas.AdminWorkforceProfileResponse,
    summary="Get individual workforce profile with learning progress, gaps, assessments and evidence",
)
def get_user_workforce_profile(
    request: Request,
    user_id: str,
) -> schemas.AdminWorkforceProfileResponse:
    """
    Return a consolidated User 360 / Individual Workforce Profile for a single user.

    Includes:
    - User identity and resolved professional role
    - Per-competency capability levels vs role requirements
    - Active skill gaps sorted by priority
    - All learning activities with explicit stored progress
    - Learning summary (totals, overall learning progress)
    - Formal capability assessment history
    - Evidence ledger summary (supporting vs authoritative)
    - Chronological learning/assessment timeline

    Access: ADMIN only (enforced at router level via require_admin_role).
    Data isolation: all data is scoped to the target user_id server-side.
    Mutations: none — this endpoint is read-only.

    Raises:
        404: User not found
        403: Caller is not ADMIN
        401: Not authenticated
    """
    db = _get_db(request)
    return service.get_user_workforce_profile(db, user_id)


@router.post(
    "/users/{user_id}/promote-to-trainer",
    response_model=schemas.AdminUserItem,
    summary="Promote an official to trainer role",
)
def promote_user_to_trainer(
    request: Request,
    user_id: str,
) -> schemas.AdminUserItem:
    db = _get_db(request)
    result = service.promote_user_to_trainer(db, user_id)
    invalidate_admin_cache()
    return result


@router.post(
    "/users/{user_id}/assign-role",
    response_model=schemas.AdminUserItem,
    summary="Assign or correct a user's professional role and reconcile competency requirements",
)
def assign_user_role(
    request: Request,
    user_id: str,
    payload: schemas.AdminAssignRoleRequest,
) -> schemas.AdminUserItem:
    db = _get_db(request)
    result = service.assign_user_role(db, user_id, payload)
    invalidate_admin_cache()
    return result




# ─── RAG Admin Endpoints ──────────────────────────────────────────────────────

@router.post("/rag/seed-datasets")
def seed_rag_datasets(
    request: Request,
    overwrite: bool = False,
) -> dict:
    """Seed all RAG datasets (Glossary, Synonyms, Eval Set, Refusal Set)."""
    db = _get_db(request)
    try:
        from app.rag.datasets.seed_all import seed_all
        results = seed_all(db, overwrite=overwrite)
        return {"status": "ok", "results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Seed failed: {exc}")


@router.post("/rag/run-evaluation")
def run_rag_evaluation(request: Request) -> dict:
    """Run routing + refusal evaluation against seeded test sets."""
    db = _get_db(request)
    try:
        from app.rag.evaluation.runner import run_full_eval
        report = run_full_eval(db)
        return {
            "status": "ok",
            "routing_accuracy": report.routing_accuracy,
            "refusal_accuracy": report.refusal_accuracy,
            "total_eval_queries": report.total_eval,
            "routing_correct": report.routing_correct,
            "refusal_total": report.refusal_total,
            "refusal_correct": report.refusal_correct,
            "avg_latency_ms": report.avg_latency_ms,
            "routing_failures": [
                {"eval_id": r.eval_id, "query": r.query[:80],
                 "expected": r.expected_intent, "got": r.actual_intent}
                for r in report.eval_results if not r.routing_correct
            ],
            "refusal_failures": [
                {"test_id": r.test_id, "query": r.query[:80], "reason": r.failure_reason}
                for r in report.refusal_results if not r.passed
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}")


@router.post("/rag/reembed-materials")
def reembed_materials(request: Request) -> dict:
    """Re-embed all PENDING/FAILED document chunks using Gemini."""
    db = _get_db(request)
    settings = getattr(request.app.state, "settings", None)
    if not settings:
        from app.core.config import get_settings
        settings = get_settings()

    try:
        from app.scripts.migrate_embed_backfill import run_backfill
        import threading

        def _bg():
            try:
                run_backfill()
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning("Background reembed failed: %s", exc)

        t = threading.Thread(target=_bg, daemon=True, name="bg-reembed")
        t.start()
        return {"status": "started", "message": "Re-embedding running in background"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Reembed trigger failed: {exc}")
