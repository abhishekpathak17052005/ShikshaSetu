"""MongoDB repository for Trainer Assessment Studio."""
from datetime import UTC, datetime
from typing import Any, Optional
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database


def object_id(value: str | ObjectId) -> ObjectId | None:
    if isinstance(value, ObjectId):
        return value
    return ObjectId(value) if ObjectId.is_valid(value) else None


def create_trainer_indexes(database: Database) -> None:
    """Ensure indexes exist for trainer collections."""
    try:
        database.trainer_questions.create_index([("trainer_id", ASCENDING), ("material_id", ASCENDING)])
        database.trainer_questions.create_index([("status", ASCENDING)])
        database.quizzes.create_index([("trainer_id", ASCENDING)])
        database.quizzes.create_index([("assigned_to", ASCENDING)])
        database.quiz_attempts.create_index([("quiz_id", ASCENDING)])
        database.quiz_attempts.create_index([("user_id", ASCENDING)])
    except Exception:
        pass


class TrainerRepository:
    """Data access layer for Trainer workflows."""

    @staticmethod
    def save_questions(database: Database, questions: list[dict]) -> list[str]:
        if not questions:
            return []
        result = database.trainer_questions.insert_many(questions)
        return [str(uid) for uid in result.inserted_ids]

    @staticmethod
    def get_question_by_id(
        database: Database,
        question_id: str,
        trainer_id: str | None = None,
    ) -> dict | None:
        q_oid = object_id(question_id)
        if not q_oid:
            return None
        query: dict[str, Any] = {"_id": q_oid}
        if trainer_id:
            query["trainer_id"] = str(trainer_id)
        return database.trainer_questions.find_one(query)

    @staticmethod
    def list_questions_by_material(
        database: Database,
        material_id: str,
        trainer_id: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        query: dict[str, Any] = {"material_id": str(material_id)}
        if trainer_id:
            query["trainer_id"] = str(trainer_id)
        if status:
            query["status"] = status
        cursor = database.trainer_questions.find(query)
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("created_at", -1)
        return list(cursor)

    @staticmethod
    def list_all_questions_by_trainer(
        database: Database,
        trainer_id: str,
        status: str | None = None,
    ) -> list[dict]:
        query: dict[str, Any] = {"trainer_id": str(trainer_id)}
        if status and status != "ALL":
            query["status"] = status
        cursor = database.trainer_questions.find(query)
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("created_at", -1)
        return list(cursor)

    @staticmethod
    def get_questions_by_ids(
        database: Database,
        question_ids: list[str],
        trainer_id: str | None = None,
    ) -> list[dict]:
        oids = [object_id(qid) for qid in question_ids if object_id(qid)]
        if not oids:
            return []
        query: dict[str, Any] = {"_id": {"$in": oids}}
        if trainer_id:
            query["trainer_id"] = str(trainer_id)
        return list(database.trainer_questions.find(query))

    @staticmethod
    def update_question(
        database: Database,
        question_id: str,
        trainer_id: str,
        updates: dict,
    ) -> dict | None:
        q_oid = object_id(question_id)
        if not q_oid:
            return None
        updates["updated_at"] = datetime.now(UTC)
        database.trainer_questions.update_one(
            {"_id": q_oid, "trainer_id": str(trainer_id)},
            {"$set": updates},
        )
        return TrainerRepository.get_question_by_id(database, question_id, trainer_id)

    @staticmethod
    def update_question_status(
        database: Database,
        question_id: str,
        trainer_id: str,
        status: str,
        notes: str | None = None,
    ) -> dict | None:
        updates = {
            "status": status,
            "review_notes": notes,
            "updated_at": datetime.now(UTC),
        }
        return TrainerRepository.update_question(database, question_id, trainer_id, updates)

    @staticmethod
    def create_quiz(database: Database, quiz_doc: dict) -> str:
        result = database.quizzes.insert_one(quiz_doc)
        return str(quiz_doc.get("_id") or result.inserted_id)

    @staticmethod
    def get_quiz_by_id(
        database: Database,
        quiz_id: str,
        trainer_id: str | None = None,
    ) -> dict | None:
        q_oid = object_id(quiz_id)
        if not q_oid:
            return None
        query: dict[str, Any] = {"_id": q_oid}
        if trainer_id:
            query["trainer_id"] = str(trainer_id)
        return database.quizzes.find_one(query)

    @staticmethod
    def list_quizzes_by_trainer(database: Database, trainer_id: str) -> list[dict]:
        cursor = database.quizzes.find({"trainer_id": str(trainer_id)})
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("created_at", -1)
        return list(cursor)

    @staticmethod
    def update_quiz_status(
        database: Database,
        quiz_id: str,
        trainer_id: str,
        status: str,
        extra_fields: dict | None = None,
    ) -> dict | None:
        q_oid = object_id(quiz_id)
        if not q_oid:
            return None
        updates = {
            "status": status,
            "updated_at": datetime.now(UTC),
        }
        if extra_fields:
            updates.update(extra_fields)
        database.quizzes.update_one(
            {"_id": q_oid, "trainer_id": str(trainer_id)},
            {"$set": updates},
        )
        return TrainerRepository.get_quiz_by_id(database, quiz_id, trainer_id)

    @staticmethod
    def assign_quiz_to_learners(
        database: Database,
        quiz_id: str,
        trainer_id: str,
        learner_ids: list[str],
    ) -> int:
        q_oid = object_id(quiz_id)
        if not q_oid:
            return 0
        now = datetime.now(UTC)
        quiz = TrainerRepository.get_quiz_by_id(database, quiz_id, trainer_id)
        if not quiz:
            return 0
        existing_assigned = set(quiz.get("assigned_to", []))
        new_assigned = list(existing_assigned.union(set(learner_ids)))
        database.quizzes.update_one(
            {"_id": q_oid, "trainer_id": str(trainer_id)},
            {
                "$set": {
                    "assigned_to": new_assigned,
                    "status": "ASSIGNED",
                    "updated_at": now,
                }
            },
        )
        return len(new_assigned)

    @staticmethod
    def list_materials_by_trainer(database: Database, trainer_id: str) -> list[dict]:
        t_oid = object_id(trainer_id)
        query = {"$or": [{"user_id": str(trainer_id)}, {"user_id": t_oid}]} if t_oid else {"user_id": str(trainer_id)}
        cursor = database.learning_materials.find(query)
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("created_at", -1)
        return list(cursor)

    @staticmethod
    def get_material_by_id(
        database: Database,
        material_id: str,
        trainer_id: str | None = None,
    ) -> dict | None:
        m_oid = object_id(material_id)
        id_query = {"$in": [m_oid, str(material_id)]} if m_oid else str(material_id)
        query: dict[str, Any] = {"_id": id_query}
        if trainer_id:
            t_oid = object_id(trainer_id)
            query["user_id"] = {"$in": [str(trainer_id), t_oid]} if t_oid else str(trainer_id)
        return database.learning_materials.find_one(query)

    @staticmethod
    def get_attempts_for_quiz(database: Database, quiz_id: str) -> list[dict]:
        q_oid = object_id(quiz_id)
        query = {"$or": [{"quiz_id": q_oid}, {"quiz_id": str(quiz_id)}]} if q_oid else {"quiz_id": str(quiz_id)}
        cursor = database.quiz_attempts.find(query)
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("submitted_at", -1)
        return list(cursor)

    @staticmethod
    def get_attempts_by_trainer_quizzes(database: Database, trainer_id: str) -> list[dict]:
        quizzes = TrainerRepository.list_quizzes_by_trainer(database, trainer_id)
        quiz_ids = [q["_id"] for q in quizzes]
        quiz_id_strs = [str(qid) for qid in quiz_ids]
        all_ids = quiz_ids + quiz_id_strs
        if not all_ids:
            return []
        cursor = database.quiz_attempts.find({"quiz_id": {"$in": all_ids}})
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("submitted_at", -1)
        return list(cursor)

    @staticmethod
    def get_attempt_by_id(database: Database, attempt_id: str) -> dict | None:
        a_oid = object_id(attempt_id)
        query = {"$or": [{"_id": a_oid}, {"_id": str(attempt_id)}]} if a_oid else {"_id": str(attempt_id)}
        return database.quiz_attempts.find_one(query)

    @staticmethod
    def add_attempt_feedback(database: Database, attempt_id: str, feedback_doc: dict) -> bool:
        a_oid = object_id(attempt_id)
        query = {"$or": [{"_id": a_oid}, {"_id": str(attempt_id)}]} if a_oid else {"_id": str(attempt_id)}
        res = database.quiz_attempts.update_one(
            query,
            {"$set": {"trainer_feedback": feedback_doc, "updated_at": datetime.now(UTC)}},
        )
        return res.matched_count > 0 or res.modified_count > 0

    @staticmethod
    def list_assigned_quizzes_for_learner(database: Database, learner_id: str) -> list[dict]:
        """Find all published/assigned quizzes available to this learner."""
        cursor = database.quizzes.find({
            "status": {"$in": ["PUBLISHED", "ASSIGNED"]},
            "$or": [
                {"assigned_to": str(learner_id)},
                {"assigned_to": []},  # Publicly published quizzes open to all
                {"assigned_to": {"$exists": False}},
            ],
        })
        if hasattr(cursor, "sort"):
            cursor = cursor.sort("created_at", -1)
        return list(cursor)
