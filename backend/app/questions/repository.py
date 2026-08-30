"""Repository for question bank operations."""
from bson import ObjectId
from pymongo.database import Database


def object_id(value: str) -> ObjectId | None:
    """Convert string to ObjectId if valid."""
    return ObjectId(value) if ObjectId.is_valid(value) else None


def get_question_by_id(database: Database, question_id: str) -> dict | None:
    """Get a single question by question_id (internal use only - includes correct_answer)."""
    return database.question_bank.find_one({
        "question_id": question_id,
        "status": "ACTIVE"
    })


def get_questions_by_competency(
    database: Database,
    competency_code: str,
    question_type: str | None = None,
    difficulty: str | None = None,
    limit: int = 100
) -> list[dict]:
    """Get questions for a competency, optionally filtered by type and difficulty."""
    query = {
        "competency_code": competency_code,
        "status": "ACTIVE"
    }
    if question_type:
        query["question_type"] = question_type
    if difficulty:
        query["difficulty"] = difficulty
    
    return list(database.question_bank.find(query).limit(limit))


def get_random_questions_for_assessment(
    database: Database,
    competency_code: str,
    count: int,
    question_types: list[str] | None = None,
    difficulties: list[str] | None = None
) -> list[dict]:
    """Get random questions for an assessment based on criteria."""
    query = {
        "competency_code": competency_code,
        "status": "ACTIVE"
    }
    
    if question_types:
        query["question_type"] = {"$in": question_types}
    if difficulties:
        query["difficulty"] = {"$in": difficulties}
    
    # MongoDB aggregation pipeline for random sampling
    pipeline = [
        {"$match": query},
        {"$sample": {"size": min(count, 100)}},  # Cap at 100 to prevent memory issues
    ]
    
    return list(database.question_bank.aggregate(pipeline))


def get_question_count(
    database: Database,
    competency_code: str,
    question_type: str | None = None
) -> int:
    """Get count of questions for a competency."""
    query = {
        "competency_code": competency_code,
        "status": "ACTIVE"
    }
    if question_type:
        query["question_type"] = question_type
    
    return database.question_bank.count_documents(query)


def insert_question(database: Database, question_doc: dict) -> str:
    """Insert a new question into the question bank."""
    result = database.question_bank.insert_one(question_doc)
    return str(result.inserted_id)


def insert_many_questions(database: Database, questions: list[dict]) -> list[str]:
    """Insert multiple questions into the question bank."""
    if not questions:
        return []
    result = database.question_bank.insert_many(questions)
    return [str(oid) for oid in result.inserted_ids]


def update_question_status(
    database: Database,
    question_id: str,
    status: str
) -> dict | None:
    """Update question status (ACTIVE, INACTIVE, DEPRECATED)."""
    return database.question_bank.find_one_and_update(
        {"question_id": question_id},
        {"$set": {"status": status, "updated_at": database.client.admin.command("currentDate", {"_time": True})}},
        return_document=True
    )


def list_questions_by_competency_and_type(
    database: Database,
    competency_code: str,
    question_type: str
) -> list[dict]:
    """List all active questions for a competency and type."""
    return list(database.question_bank.find({
        "competency_code": competency_code,
        "question_type": question_type,
        "status": "ACTIVE"
    }))


def get_question_by_mongo_id(database: Database, mongo_id: str) -> dict | None:
    """Get question by MongoDB _id (for internal lookups)."""
    oid = object_id(mongo_id)
    if oid is None:
        return None
    return database.question_bank.find_one({
        "_id": oid,
        "status": "ACTIVE"
    })


def count_questions_by_competency(database: Database, competency_code: str) -> int:
    """Count all active questions for a competency."""
    return database.question_bank.count_documents({
        "competency_code": competency_code,
        "status": "ACTIVE"
    })
