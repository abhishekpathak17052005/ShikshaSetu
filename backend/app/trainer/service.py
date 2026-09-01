"""Business logic service for Trainer Assessment Studio."""
from datetime import UTC, datetime
from typing import Any, Optional
from bson import ObjectId
from pymongo.database import Database

from app.trainer.models import (
    QuestionReviewStatus,
    TrainerQuizStatus,
    TrainerQuestion,
    TrainerQuiz,
)
from app.trainer.repository import TrainerRepository


class TrainerServiceError(Exception):
    """Domain error in trainer service."""
    pass


class TrainerService:
    """Encapsulates all trainer business logic and lifecycle rules."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.repo = TrainerRepository()

    def get_dashboard(self, trainer_id: str) -> dict:
        """Calculate live metrics for trainer dashboard."""
        materials = self.repo.list_materials_by_trainer(self.database, trainer_id)
        quizzes = self.repo.list_quizzes_by_trainer(self.database, trainer_id)
        all_attempts = self.repo.get_attempts_by_trainer_quizzes(self.database, trainer_id)

        # Count questions by review status across trainer's materials
        all_q_cursor = self.database.trainer_questions.find({"trainer_id": str(trainer_id)})
        all_questions = list(all_q_cursor)
        
        q_approved = sum(1 for q in all_questions if q.get("status") == QuestionReviewStatus.APPROVED.value)
        q_rejected = sum(1 for q in all_questions if q.get("status") == QuestionReviewStatus.REJECTED.value)
        q_pending = sum(1 for q in all_questions if q.get("status") in (QuestionReviewStatus.GENERATED.value, QuestionReviewStatus.EDITED.value))

        # Assigned learners across all published/assigned quizzes
        assigned_learner_ids = set()
        for q in quizzes:
            for uid in q.get("assigned_to", []):
                assigned_learner_ids.add(str(uid))

        published_count = sum(1 for q in quizzes if q.get("status") in (TrainerQuizStatus.PUBLISHED.value, TrainerQuizStatus.ASSIGNED.value))

        # Attempt statistics
        total_attempts = len(all_attempts)
        avg_score = (
            round(sum(a.get("percentage", 0) for a in all_attempts) / total_attempts, 1)
            if total_attempts > 0
            else 0.0
        )

        recent_materials = [
            {
                "id": str(m["_id"]),
                "filename": m.get("original_filename") or m.get("filename"),
                "status": m.get("status"),
                "created_at": m.get("created_at", datetime.now(UTC)).isoformat(),
            }
            for m in materials[:5]
        ]

        recent_quizzes = [
            {
                "id": str(q["_id"]),
                "title": q.get("title"),
                "competency_code": q.get("competency_code"),
                "status": q.get("status"),
                "question_count": q.get("question_count", 0),
                "created_at": q.get("created_at", datetime.now(UTC)).isoformat(),
            }
            for q in quizzes[:5]
        ]

        return {
            "total_materials_uploaded": len(materials),
            "materials_count": len(materials),
            "total_questions_generated": len(all_questions),
            "questions_count": len(all_questions),
            "questions_approved": q_approved,
            "approved_questions_count": q_approved,
            "questions_rejected": q_rejected,
            "rejected_questions_count": q_rejected,
            "questions_pending_review": q_pending,
            "pending_questions_count": q_pending,
            "pending_review_count": q_pending,
            "total_quizzes_created": len(quizzes),
            "quizzes_count": len(quizzes),
            "published_quizzes": published_count,
            "published_quizzes_count": published_count,
            "total_assigned_learners": len(assigned_learner_ids),
            "total_learner_attempts": total_attempts,
            "learner_attempts_count": total_attempts,
            "average_learner_score": avg_score,
            "average_score_all_quizzes": avg_score,
            "recent_materials": recent_materials,
            "recent_quizzes": recent_quizzes,
        }

    def list_materials(self, trainer_id: str) -> list[dict]:
        """List all learning materials uploaded by the trainer with question counts."""
        materials = self.repo.list_materials_by_trainer(self.database, trainer_id)
        result = []
        for m in materials:
            mid_str = str(m["_id"])
            q_cursor = self.database.trainer_questions.find({"material_id": mid_str})
            q_list = list(q_cursor)
            approved_count = sum(1 for q in q_list if q.get("status") == QuestionReviewStatus.APPROVED.value)
            
            created_at_val = m.get("created_at")
            if isinstance(created_at_val, datetime):
                created_str = created_at_val.isoformat()
            else:
                created_str = str(created_at_val or "")

            result.append({
                "_id": mid_str,
                "filename": m.get("filename", ""),
                "original_filename": m.get("original_filename", m.get("filename", "")),
                "content_type": m.get("content_type", "application/octet-stream"),
                "file_size": m.get("file_size", 0),
                "status": m.get("status", "READY"),
                "chunk_count": m.get("chunk_count", 0),
                "questions_count": len(q_list),
                "approved_questions_count": approved_count,
                "created_at": created_str,
            })
        return result

    def get_material_detail(self, trainer_id: str, material_id: str) -> dict:
        """Get details for a specific material owned by the trainer."""
        material = self.repo.get_material_by_id(self.database, material_id, trainer_id)
        if not material:
            raise TrainerServiceError("Learning material not found or not owned by trainer")
        
        mid_str = str(material["_id"])
        q_cursor = self.database.trainer_questions.find({"material_id": mid_str})
        q_list = list(q_cursor)
        approved_count = sum(1 for q in q_list if q.get("status") == QuestionReviewStatus.APPROVED.value)

        created_at_val = material.get("created_at")
        created_str = created_at_val.isoformat() if isinstance(created_at_val, datetime) else str(created_at_val or "")

        return {
            "_id": mid_str,
            "filename": material.get("filename", ""),
            "original_filename": material.get("original_filename", material.get("filename", "")),
            "content_type": material.get("content_type", "application/octet-stream"),
            "file_size": material.get("file_size", 0),
            "status": material.get("status", "READY"),
            "chunk_count": material.get("chunk_count", 0),
            "questions_count": len(q_list),
            "approved_questions_count": approved_count,
            "created_at": created_str,
        }

    def save_generated_questions(
        self,
        trainer_id: str,
        material_id: str,
        competency_code: str,
        questions: list[dict],
    ) -> list[dict]:
        """Persist newly AI-generated MCQs into trainer_questions in GENERATED status."""
        docs = []
        for q in questions:
            doc = TrainerQuestion.create(
                trainer_id=trainer_id,
                material_id=material_id,
                competency_code=competency_code,
                question=q.get("question", ""),
                options=q.get("options", []),
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", ""),
                difficulty=q.get("difficulty", "MEDIUM"),
                source_chunks=q.get("source_chunks", []),
                grounding_score=q.get("grounding_score"),
                status=QuestionReviewStatus.GENERATED,
            )
            docs.append(doc)

        self.repo.save_questions(self.database, docs)
        return docs

    def list_questions_for_material(
        self,
        trainer_id: str,
        material_id: str,
        status_filter: str | None = None,
    ) -> list[dict]:
        """List all generated/reviewed questions for a material."""
        questions = self.repo.list_questions_by_material(
            self.database,
            material_id=material_id,
            trainer_id=trainer_id,
            status=status_filter,
        )
        return [self._format_question(q) for q in questions]

    def list_all_questions(
        self,
        trainer_id: str,
        status_filter: str | None = None,
    ) -> list[dict]:
        """List all questions across all trainer materials."""
        questions = self.repo.list_all_questions_by_trainer(
            self.database,
            trainer_id=trainer_id,
            status=status_filter,
        )
        return [self._format_question(q) for q in questions]

    def get_question(self, trainer_id: str, question_id: str) -> dict:
        """Get single question detail with full answer key and review state."""
        q = self.repo.get_question_by_id(self.database, question_id, trainer_id)
        if not q:
            raise TrainerServiceError("Question not found or not owned by trainer")
        return self._format_question(q)

    def edit_question(self, trainer_id: str, question_id: str, updates: dict) -> dict:
        """Edit question content and transition status to EDITED."""
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        if not clean_updates:
            return self.get_question(trainer_id, question_id)
        
        clean_updates["status"] = QuestionReviewStatus.EDITED.value
        updated = self.repo.update_question(self.database, question_id, trainer_id, clean_updates)
        if not updated:
            raise TrainerServiceError("Failed to update question or question not found")
        return self._format_question(updated)

    def review_question(
        self,
        trainer_id: str,
        question_id: str,
        action: str,
        notes: str | None = None,
    ) -> dict:
        """Approve or reject a question."""
        target_status = (
            QuestionReviewStatus.APPROVED.value
            if action == "APPROVE"
            else QuestionReviewStatus.REJECTED.value
        )
        updated = self.repo.update_question_status(
            self.database,
            question_id=question_id,
            trainer_id=trainer_id,
            status=target_status,
            notes=notes,
        )
        if not updated:
            raise TrainerServiceError("Failed to review question or question not found")
        return self._format_question(updated)

    def create_quiz_draft(
        self,
        trainer_id: str,
        title: str,
        description: str | None,
        material_id: str | None,
        competency_code: str,
        question_ids: list[str],
    ) -> dict:
        """
        Create a quiz draft from reviewed questions.
        CRITICAL RULE: All selected questions MUST have status == 'APPROVED'.
        """
        questions = self.repo.get_questions_by_ids(self.database, question_ids, trainer_id)
        if len(questions) != len(question_ids):
            raise TrainerServiceError("One or more question IDs are invalid or not owned by trainer")

        # Verify all questions are APPROVED
        unapproved = [str(q["_id"]) for q in questions if q.get("status") != QuestionReviewStatus.APPROVED.value]
        if unapproved:
            raise TrainerServiceError(
                f"Cannot create quiz: Questions {unapproved} are not in APPROVED state. Review and approve questions first."
            )

        quiz_questions = [
            {
                "question_id": str(q["_id"]),
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q["explanation"],
                "difficulty": q.get("difficulty", "MEDIUM"),
                "source_chunks": q.get("source_chunks", []),
            }
            for q in questions
        ]

        quiz_doc = TrainerQuiz.create(
            trainer_id=trainer_id,
            material_id=material_id,
            competency_code=competency_code,
            title=title,
            description=description,
            questions=quiz_questions,
            question_ids=question_ids,
        )

        quiz_id = self.repo.create_quiz(self.database, quiz_doc)
        quiz_doc["_id"] = quiz_id
        return self._format_quiz(quiz_doc)

    def publish_quiz(self, trainer_id: str, quiz_id: str) -> dict:
        """Publish a quiz draft, making it ready for assignment and learner access."""
        quiz = self.repo.get_quiz_by_id(self.database, quiz_id, trainer_id)
        if not quiz:
            raise TrainerServiceError("Quiz not found or not owned by trainer")
        
        if not quiz.get("questions"):
            raise TrainerServiceError("Cannot publish empty quiz")

        updated = self.repo.update_quiz_status(
            self.database,
            quiz_id=quiz_id,
            trainer_id=trainer_id,
            status=TrainerQuizStatus.PUBLISHED.value,
            extra_fields={"published_at": datetime.now(UTC)},
        )
        if not updated:
            raise TrainerServiceError("Failed to publish quiz")
        return self._format_quiz(updated)

    def assign_quiz(self, trainer_id: str, quiz_id: str, learner_ids: list[str]) -> dict:
        """Assign a published quiz to one or more learners."""
        quiz = self.repo.get_quiz_by_id(self.database, quiz_id, trainer_id)
        if not quiz:
            raise TrainerServiceError("Quiz not found or not owned by trainer")

        if quiz.get("status") == TrainerQuizStatus.DRAFT.value:
            raise TrainerServiceError("Cannot assign a DRAFT quiz. Please publish the quiz first.")

        assigned_count = self.repo.assign_quiz_to_learners(
            self.database,
            quiz_id=quiz_id,
            trainer_id=trainer_id,
            learner_ids=learner_ids,
        )

        return {
            "quiz_id": str(quiz["_id"]),
            "assigned_learners_count": assigned_count,
            "status": TrainerQuizStatus.ASSIGNED.value,
            "message": f"Quiz successfully assigned to {len(learner_ids)} learner(s)",
        }

    def list_quizzes(self, trainer_id: str) -> list[dict]:
        """List all quizzes created by the trainer."""
        quizzes = self.repo.list_quizzes_by_trainer(self.database, trainer_id)
        return [self._format_quiz(q) for q in quizzes]

    def get_quiz_details(self, trainer_id: str, quiz_id: str) -> dict:
        """Get details for a specific quiz owned by the trainer."""
        quiz = self.repo.get_quiz_by_id(self.database, quiz_id, trainer_id)
        if not quiz:
            raise TrainerServiceError("Quiz not found or not owned by trainer")
        return self._format_quiz(quiz)

    def list_quiz_attempts(self, trainer_id: str, quiz_id: str) -> list[dict]:
        """List all learner attempts for a quiz with evaluation summaries."""
        quiz = self.repo.get_quiz_by_id(self.database, quiz_id, trainer_id)
        if not quiz:
            raise TrainerServiceError("Quiz not found or not owned by trainer")

        attempts = self.repo.get_attempts_for_quiz(self.database, quiz_id)
        result = []
        for a in attempts:
            user_id = str(a.get("user_id", ""))
            user = self.database.users.find_one({"$or": [{"_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else None}, {"_id": user_id}]}) or {}

            sub_val = a.get("submitted_at")
            sub_str = sub_val.isoformat() if isinstance(sub_val, datetime) else str(sub_val or "")

            feedback = a.get("trainer_feedback")
            result.append({
                "_id": str(a["_id"]),
                "quiz_id": str(a.get("quiz_id", quiz_id)),
                "quiz_title": quiz.get("title", "Assessment"),
                "learner_id": user_id,
                "learner_name": user.get("full_name", "Unknown Official"),
                "learner_email": user.get("email", ""),
                "score": a.get("score", 0),
                "percentage": a.get("percentage", 0.0),
                "correct_count": a.get("correct_count", 0),
                "total_questions": a.get("total_questions", 0),
                "competency_code": quiz.get("competency_code", ""),
                "submitted_at": sub_str,
                "has_trainer_feedback": bool(feedback),
                "trainer_feedback": feedback,
            })
        return result

    def list_assigned_learners(self, trainer_id: str) -> list[dict]:
        """List all learners in the organization with assignment and attempt summaries."""
        quizzes = self.repo.list_quizzes_by_trainer(self.database, trainer_id)
        assigned_map: dict[str, dict] = {}

        for q in quizzes:
            assigned_ids = q.get("assigned_to", [])
            for uid in assigned_ids:
                uid_str = str(uid)
                if uid_str not in assigned_map:
                    assigned_map[uid_str] = {"assigned_count": 0, "quiz_ids": []}
                assigned_map[uid_str]["assigned_count"] += 1
                assigned_map[uid_str]["quiz_ids"].append(str(q["_id"]))

        # Query all official and employee users in the system
        all_users = list(self.database.users.find({
            "access_role": {"$in": ["OFFICIAL", "EMPLOYEE"]},
        }))

        learners = []
        for user in all_users:
            uid_str = str(user["_id"])
            data = assigned_map.get(uid_str, {"assigned_count": 0, "quiz_ids": []})
            
            # Find completed attempts for trainer's quizzes if any
            attempts = []
            if data["quiz_ids"]:
                attempts = list(self.database.quiz_attempts.find({
                    "$or": [{"user_id": ObjectId(uid_str) if ObjectId.is_valid(uid_str) else None}, {"user_id": uid_str}],
                    "quiz_id": {"$in": [ObjectId(qid) for qid in data["quiz_ids"] if ObjectId.is_valid(qid)] + data["quiz_ids"]},
                }))

            avg = (
                round(sum(a.get("percentage", 0) for a in attempts) / len(attempts), 1)
                if attempts
                else 0.0
            )

            learners.append({
                "_id": uid_str,
                "id": uid_str,
                "learner_id": uid_str,
                "full_name": user.get("full_name", "Official User"),
                "email": user.get("email", ""),
                "department": user.get("department", "Public Administration"),
                "designation": user.get("designation", "Civil Service Official"),
                "employee_id": user.get("employee_id", "EMP-001"),
                "access_role": user.get("access_role", "OFFICIAL"),
                "assigned_quizzes_count": data["assigned_count"],
                "completed_quizzes_count": len(attempts),
                "average_score": avg,
            })
        return learners

    def get_learner_results(self, trainer_id: str, learner_id: str) -> dict:
        """Get full history and evaluation of a specific learner under trainer's quizzes."""
        quizzes = self.repo.list_quizzes_by_trainer(self.database, trainer_id)
        quiz_map = {str(q["_id"]): q for q in quizzes}
        all_quiz_ids = list(quiz_map.keys())

        user = self.database.users.find_one({"$or": [{"_id": ObjectId(learner_id) if ObjectId.is_valid(learner_id) else None}, {"_id": learner_id}]})
        if not user:
            raise TrainerServiceError("Learner not found")

        attempts = list(self.database.quiz_attempts.find({
            "$or": [{"user_id": ObjectId(learner_id) if ObjectId.is_valid(learner_id) else None}, {"user_id": learner_id}],
        }))

        formatted_attempts = []
        for a in attempts:
            qid_str = str(a.get("quiz_id", ""))
            quiz_info = quiz_map.get(qid_str, {})
            sub_val = a.get("submitted_at")
            sub_str = sub_val.isoformat() if isinstance(sub_val, datetime) else str(sub_val or "")

            formatted_attempts.append({
                "attempt_id": str(a["_id"]),
                "quiz_id": qid_str,
                "quiz_title": quiz_info.get("title", "Assessment"),
                "competency_code": quiz_info.get("competency_code", ""),
                "score": a.get("score", 0),
                "percentage": a.get("percentage", 0.0),
                "correct_count": a.get("correct_count", 0),
                "total_questions": a.get("total_questions", 0),
                "submitted_at": sub_str,
                "trainer_feedback": a.get("trainer_feedback"),
            })

        return {
            "learner_id": str(user["_id"]),
            "full_name": user.get("full_name", ""),
            "email": user.get("email", ""),
            "department": user.get("department", ""),
            "designation": user.get("designation", ""),
            "total_attempts": len(formatted_attempts),
            "attempts": formatted_attempts,
        }

    def submit_feedback(
        self,
        trainer_id: str,
        attempt_id: str,
        feedback_text: str,
        strengths: list[str],
        areas_for_improvement: list[str],
        rating: int | None = None,
    ) -> dict:
        """Submit trainer qualitative feedback on a learner attempt."""
        attempt = self.repo.get_attempt_by_id(self.database, attempt_id)
        if not attempt:
            raise TrainerServiceError("Quiz attempt not found")

        # Verify that the quiz belongs to the trainer
        quiz_id = str(attempt.get("quiz_id", ""))
        quiz = self.repo.get_quiz_by_id(self.database, quiz_id, trainer_id)
        if not quiz:
            raise TrainerServiceError("Attempt belongs to a quiz not owned by this trainer")

        now = datetime.now(UTC)
        feedback_doc = {
            "trainer_id": str(trainer_id),
            "feedback_text": feedback_text,
            "strengths": strengths or [],
            "areas_for_improvement": areas_for_improvement or [],
            "rating": rating,
            "created_at": now.isoformat(),
        }

        success = self.repo.add_attempt_feedback(self.database, attempt_id, feedback_doc)
        if not success:
            raise TrainerServiceError("Failed to save feedback")

        return {
            "attempt_id": str(attempt["_id"]),
            "quiz_id": quiz_id,
            "feedback": feedback_doc,
            "message": "Feedback submitted successfully",
        }

    # =========================================================================
    # Helpers
    # =========================================================================

    def _format_question(self, q: dict) -> dict:
        created_val = q.get("created_at")
        updated_val = q.get("updated_at")
        return {
            "_id": str(q["_id"]),
            "material_id": str(q.get("material_id", "")),
            "competency_code": q.get("competency_code", ""),
            "question": q.get("question", ""),
            "options": q.get("options", []),
            "correct_answer": q.get("correct_answer", ""),
            "explanation": q.get("explanation", ""),
            "difficulty": q.get("difficulty", "MEDIUM"),
            "source_chunks": q.get("source_chunks", []),
            "grounding_score": q.get("grounding_score"),
            "status": q.get("status", QuestionReviewStatus.GENERATED.value),
            "review_notes": q.get("review_notes"),
            "created_at": created_val.isoformat() if isinstance(created_val, datetime) else str(created_val or ""),
            "updated_at": updated_val.isoformat() if isinstance(updated_val, datetime) else str(updated_val or ""),
        }

    def _format_quiz(self, q: dict) -> dict:
        created_val = q.get("created_at")
        pub_val = q.get("published_at")
        questions = [
            {
                "_id": str(qu.get("question_id", qu.get("_id", ""))),
                "material_id": str(q.get("material_id", "")),
                "competency_code": q.get("competency_code", ""),
                "question": qu.get("question", ""),
                "options": qu.get("options", []),
                "correct_answer": qu.get("correct_answer", ""),
                "explanation": qu.get("explanation", ""),
                "difficulty": qu.get("difficulty", "MEDIUM"),
                "source_chunks": qu.get("source_chunks", []),
                "grounding_score": qu.get("grounding_score"),
                "status": QuestionReviewStatus.APPROVED.value,
                "review_notes": None,
                "created_at": created_val.isoformat() if isinstance(created_val, datetime) else str(created_val or ""),
                "updated_at": created_val.isoformat() if isinstance(created_val, datetime) else str(created_val or ""),
            }
            for qu in q.get("questions", [])
        ]

        assigned_list = q.get("assigned_to", [])
        attempts = self.repo.get_attempts_for_quiz(self.database, str(q["_id"]))
        avg_score = (
            round(sum(a.get("percentage", 0) for a in attempts) / len(attempts), 1)
            if attempts
            else None
        )

        return {
            "_id": str(q["_id"]),
            "trainer_id": str(q.get("trainer_id", "")),
            "title": q.get("title", ""),
            "description": q.get("description"),
            "competency_code": q.get("competency_code", ""),
            "status": q.get("status", TrainerQuizStatus.DRAFT.value),
            "question_count": q.get("question_count", len(questions)),
            "questions": questions,
            "assigned_learners_count": len(assigned_list),
            "attempts_count": len(attempts),
            "average_score": avg_score,
            "created_at": created_val.isoformat() if isinstance(created_val, datetime) else str(created_val or ""),
            "published_at": pub_val.isoformat() if isinstance(pub_val, datetime) else str(pub_val or "") if pub_val else None,
        }
