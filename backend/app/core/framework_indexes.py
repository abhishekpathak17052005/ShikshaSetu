from pymongo import ASCENDING
from pymongo.database import Database


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
    
    # Phase 2: Question Bank Indexes
    database.question_bank.create_index([("competency_code", ASCENDING)], name="ix_question_competency")
    database.question_bank.create_index([("question_type", ASCENDING)], name="ix_question_type")
    database.question_bank.create_index(
        [("competency_code", ASCENDING), ("question_type", ASCENDING)],
        name="ix_question_competency_type",
    )
    database.question_bank.create_index([("status", ASCENDING)], name="ix_question_status")
    
    # Phase 2: Capability Assessments Indexes
    database.capability_assessments.create_index([("user_id", ASCENDING)], name="ix_cap_assess_user")
    database.capability_assessments.create_index([("competency_code", ASCENDING)], name="ix_cap_assess_competency")
    database.capability_assessments.create_index(
        [("user_id", ASCENDING), ("competency_code", ASCENDING)],
        name="ix_cap_assess_user_competency",
    )
    database.capability_assessments.create_index([("status", ASCENDING)], name="ix_cap_assess_status")
    database.capability_assessments.create_index([("created_at", ASCENDING)], name="ix_cap_assess_created")
