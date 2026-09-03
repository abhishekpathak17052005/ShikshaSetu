import logging

from pymongo import ASCENDING, TEXT
from pymongo.database import Database

logger = logging.getLogger(__name__)


def ensure_framework_indexes(database: Database) -> None:
    database.assessments.create_index([("assessment_key", ASCENDING)], unique=True, name="uq_assessment_key")
    database.assessment_attempts.create_index([("user_id", ASCENDING)], name="ix_attempt_user")
    database.assessment_attempts.create_index([("assessment_id", ASCENDING)], name="ix_attempt_assessment")
    database.assessment_attempts.create_index(
        [("user_id", ASCENDING), ("assessment_id", ASCENDING)],
        name="ix_attempt_user_assessment",
    )
    database.users.create_index([("email", ASCENDING)], unique=True, name="uq_user_email")
    database.users.create_index([("employee_id", ASCENDING)], unique=True, name="uq_employee_id")
    database.users.create_index([("role_id", ASCENDING)], name="ix_user_role")
    database.competencies.create_index([("code", ASCENDING)], unique=True, name="uq_competency_code")
    database.roles.create_index([("role_code", ASCENDING)], unique=True, name="uq_role_code")
    database.role_requirements.create_index(
        [("role_id", ASCENDING), ("competency_id", ASCENDING)],
        unique=True,
        name="uq_role_competency",
    )
    database.competency_profiles.create_index(
        [("user_id", ASCENDING), ("competency_id", ASCENDING)],
        unique=True,
        name="uq_user_competency_profile",
    )
    database.competency_evidence.create_index(
        [("user_id", ASCENDING), ("competency_id", ASCENDING)],
        name="ix_user_competency_evidence",
    )
    database.adaptive_assessment_sessions.create_index(
        [("user_id", ASCENDING), ("status", ASCENDING), ("completed_at", -1)],
        name="ix_adaptive_sessions_user_status_date",
    )

    # ── RAG / Document Intelligence indexes ──────────────────────────────────

    # learning_materials: fast lookup by user (ownership check on every request)
    database.learning_materials.create_index(
        [("user_id", ASCENDING)], name="ix_lm_user_id"
    )
    # learning_materials: status filter (e.g. find all READY materials)
    database.learning_materials.create_index(
        [("status", ASCENDING)], name="ix_lm_status"
    )

    # document_chunks: primary lookup — every retrieval filters by material_id
    database.document_chunks.create_index(
        [("material_id", ASCENDING)], name="ix_dc_material_id"
    )
    # document_chunks: compound for metadata-filtered retrieval
    database.document_chunks.create_index(
        [("material_id", ASCENDING), ("competency_code", ASCENDING)],
        name="ix_dc_material_competency",
    )
    # document_chunks: embedding_status — needed to queue re-embedding jobs
    database.document_chunks.create_index(
        [("embedding_status", ASCENDING)], name="ix_dc_embedding_status"
    )
    # document_chunks: full-text search for keyword retrieval branch
    # create_index raises OperationFailure if a conflicting text index already
    # exists; wrap individually so other indexes are not blocked on failure.
    try:
        database.document_chunks.create_index(
            [("text", TEXT), ("source_section", TEXT)],
            name="ix_dc_text_fulltext",
            default_language="english",
        )
    except Exception as exc:
        logger.warning("Could not create text index on document_chunks: %s", exc)
