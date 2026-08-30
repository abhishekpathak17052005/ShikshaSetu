"""Seed capability assessment configurations for core competencies."""
from datetime import datetime, UTC

from bson import ObjectId
from pymongo.database import Database


def seed_capability_assessment_configs(database: Database) -> None:
    """
    Seed capability assessment configurations for core competencies.
    
    Configurations define:
    - Which question types (MCQ, SCENARIO)
    - Number of questions
    - Difficulty levels
    - Passing thresholds
    """
    
    # Clear existing configs to avoid duplicates on re-seed
    database.assessment_configurations.delete_many({})
    
    now = datetime.now(UTC)
    
    # Core competencies and their assessment configurations
    configs = [
        # Technical Competencies
        {
            "competency_code": "TECH_PYTHON",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
            "time_limit_minutes": 30,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        {
            "competency_code": "TECH_SQL",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 12,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
            "time_limit_minutes": 35,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        {
            "competency_code": "TECH_R",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 70.0,
            "time_limit_minutes": 30,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        # Statistical Competencies
        {
            "competency_code": "STAT_SAMPLING",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 65.0,
            "time_limit_minutes": 35,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        {
            "competency_code": "STAT_SURVEY_DESIGN",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 65.0,
            "time_limit_minutes": 35,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        # Digital Governance Competencies
        {
            "competency_code": "DIGOV_CYBERSECURITY",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 12,
            "difficulty": "MIXED",
            "passing_threshold": 75.0,
            "time_limit_minutes": 40,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        {
            "competency_code": "DIGOV_DATA_PRIVACY",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 75.0,
            "time_limit_minutes": 30,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        # Behavioural / Managerial Competencies
        {
            "competency_code": "BEH_LEADERSHIP",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 60.0,
            "time_limit_minutes": 40,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        {
            "competency_code": "BEH_COMMUNICATION",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 10,
            "difficulty": "MIXED",
            "passing_threshold": 60.0,
            "time_limit_minutes": 35,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
        {
            "competency_code": "BEH_PROJECT_MANAGEMENT",
            "assessment_types": ["MCQ", "SCENARIO"],
            "number_of_questions": 12,
            "difficulty": "MIXED",
            "passing_threshold": 65.0,
            "time_limit_minutes": 40,
            "show_correct_answers_after": True,
            "allow_retake": True,
            "status": "ACTIVE",
            "created_at": now,
            "updated_at": now,
        },
    ]
    
    # Insert all configurations
    result = database.assessment_configurations.insert_many(configs)
    
    # Create indexes
    database.assessment_configurations.create_index("competency_code")
    database.assessment_configurations.create_index([("competency_code", 1), ("status", 1)])
    database.assessment_configurations.create_index("status")
    
    return len(result.inserted_ids)


if __name__ == "__main__":
    from app.core.database import initialize_database
    from app.core.config import get_settings
    
    settings = get_settings()
    client, database = initialize_database(settings.mongodb_uri, settings.mongodb_database)
    
    try:
        count = seed_capability_assessment_configs(database)
        print(f"✓ Seeded {count} assessment configurations")
    finally:
        client.close()
