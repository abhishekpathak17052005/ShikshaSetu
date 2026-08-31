"""Repository layer for Admin organizational intelligence queries."""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.database import Database


def get_all_users(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all users in the system."""
    return list(db.users.find({}))


def get_all_roles(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all professional roles."""
    return list(db.roles.find({}))


def get_all_competencies(db: Database) -> List[Dict[str, Any]]:
    """Retrieve full competency taxonomy."""
    return list(db.competencies.find({}))


def get_all_role_requirements(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all role-to-competency requirement mappings."""
    return list(db.role_requirements.find({}))


def get_all_competency_profiles(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all user competency profiles."""
    return list(db.competency_profiles.find({}))


def get_all_learning_activities(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all learning activities across all users."""
    return list(db.learning_activities.find({}))


def get_all_quizzes(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all trainer quizzes."""
    return list(db.quizzes.find({}))


def get_all_quiz_attempts(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all quiz attempt submissions."""
    return list(db.quiz_attempts.find({}))


def get_all_evidence_records(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all competency evidence ledger entries."""
    return list(db.competency_evidence.find({}))


def get_all_capability_assessments(db: Database) -> List[Dict[str, Any]]:
    """Retrieve all formal capability assessments."""
    return list(db.capability_assessments.find({}))


def get_all_learning_resources(db: Database) -> List[Dict[str, Any]]:
    """Retrieve catalog learning resources."""
    return list(db.learning_resources.find({}))
