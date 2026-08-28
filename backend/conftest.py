"""
Global pytest configuration and fixtures.
Sets up MongoDB database and test utilities.
"""

import pytest
from datetime import datetime, UTC
from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import Settings


@pytest.fixture(scope="session")
def mongodb_uri() -> str:
    """Get MongoDB URI from settings or environment."""
    return Settings().mongodb_uri


@pytest.fixture(scope="session")
def mongodb_database_name() -> str:
    """Get MongoDB database name for testing.
    
    IMPORTANT: This returns the TEST database name, NOT production.
    Production uses 'shikshasetu', tests use 'shikshasetu_test'.
    This isolation prevents test cleanup from affecting production data.
    """
    return "shikshasetu_test"  # Always use test database for pytest


@pytest.fixture(scope="session")
def mongodb_client(mongodb_uri: str) -> MongoClient:
    """Create a MongoDB client for the session."""
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Test connection
    try:
        client.admin.command("ping")
    except Exception as e:
        pytest.skip(f"MongoDB not available: {e}")
    yield client
    client.close()


@pytest.fixture
def database(mongodb_client: MongoClient, mongodb_database_name: str) -> Database:
    """
    Provide a clean MongoDB database for each test.
    
    CRITICAL: This fixture ALWAYS connects to shikshasetu_test (test database).
    This prevents test cleanup from affecting production database (shikshasetu).
    
    Database isolation:
    - Production/API: shikshasetu (connected by FastAPI via Settings)
    - Tests: shikshasetu_test (connected by pytest via this fixture)
    
    Cleanup runs ONLY on shikshasetu_test after each test.
    Production data remains untouched.
    """
    db = mongodb_client[mongodb_database_name]  # mongodb_database_name = "shikshasetu_test"
    
    # Yield the database
    yield db
    
    # Cleanup: drop collections used in tests (only in TEST database)
    collections_to_clean = [
        "learning_resources",
        "learning_resource_mappings",  # Corrected: was "resource_mappings" (doesn't exist)
        "competencies",
        "users",
        "skill_gaps",
    ]
    for collection_name in collections_to_clean:
        db[collection_name].delete_many({})


@pytest.fixture
def sample_competency(database: Database) -> ObjectId:
    """Insert a sample competency for testing."""
    comp_id = ObjectId()
    database.competencies.insert_one({
        "_id": comp_id,
        "code": "STAT-SAMPLING",
        "name": "Sampling",
        "domain": "Statistical Competencies",
        "description": "Sampling theory",
        "level_definitions": {
            "1": "Aware",
            "2": "Basic",
            "3": "Intermediate",
            "4": "Advanced",
            "5": "Expert",
        },
        "framework_status": "prototype",
    })
    return comp_id


@pytest.fixture
def sample_igot_resource(database: Database, sample_competency: ObjectId) -> ObjectId:
    """Insert a sample iGOT resource."""
    res_id = ObjectId()
    database.learning_resources.insert_one({
        "_id": res_id,
        "resource_id": "IGOT-12345",
        "provider": "IGOT",
        "resource_type": "COURSE",
        "title": "Advanced Sampling Techniques",
        "metadata": {
            "duration_hours": 24.0,
            "difficulty": "Intermediate",
            "target_roles": ["Statistical Officer"],
            "prerequisites": [],
        },
        "competencies": ["STAT-SAMPLING"],
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": "https://igot.example.com/course/12345",
            "source_document": "SRC-01",
            "verification_status": "VERIFIED",
        },
        "provider_specific": {
            "course_id": "12345",
            "course_url": "https://igot.example.com/course/12345",
            "provider_name": "iGOT Karmayogi",
            "extraction_note": None,
        },
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    return res_id


@pytest.fixture
def sample_nssta_resource(database: Database, sample_competency: ObjectId) -> ObjectId:
    """Insert a sample NSSTA resource with NULL course_id."""
    res_id = ObjectId()
    database.learning_resources.insert_one({
        "_id": res_id,
        "resource_id": "NSSTA-PROTO-ABC123",
        "provider": "NSSTA",
        "resource_type": "TRAINING_PROGRAMME",
        "title": "NSSTA Sampling Programme",
        "metadata": {
            "duration_hours": 16.0,
            "difficulty": "Beginner",
            "target_roles": [],
            "prerequisites": [],
        },
        "competencies": ["STAT-SAMPLING"],
        "source": {
            "source_type": "GOVERNMENT_PUBLICATION",
            "source_url": "https://mospi.gov.in/nssta",
            "source_document": "SRC-05",
            "verification_status": "TENTATIVE",
        },
        "provider_specific": {
            "course_id": None,  # NULL for NSSTA
            "programme_id": "PROG-001",
            "provider_name": "MoSPI/NSSTA",
            "extraction_note": None,
        },
        "status": "ACTIVE",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    return res_id


@pytest.fixture
def sample_mappings(
    database: Database,
    sample_competency: ObjectId,
    sample_igot_resource: ObjectId,
    sample_nssta_resource: ObjectId,
) -> list[ObjectId]:
    """Insert sample resource-to-competency mappings."""
    mapping_ids = []
    
    # iGOT mapping
    igot_mapping_id = ObjectId()
    database.learning_resource_mappings.insert_one({
        "_id": igot_mapping_id,
        "resource_id": sample_igot_resource,
        "competency_code": "STAT-SAMPLING",
        "provider": "IGOT",
        "mapping_confidence": 0.95,
        "manual_verified": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    mapping_ids.append(igot_mapping_id)
    
    # NSSTA mapping
    nssta_mapping_id = ObjectId()
    database.learning_resource_mappings.insert_one({
        "_id": nssta_mapping_id,
        "resource_id": sample_nssta_resource,
        "competency_code": "STAT-SAMPLING",
        "provider": "NSSTA",
        "mapping_confidence": 0.85,
        "manual_verified": False,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    })
    mapping_ids.append(nssta_mapping_id)
    
    return mapping_ids
