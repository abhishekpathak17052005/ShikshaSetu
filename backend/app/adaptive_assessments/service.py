"""Service orchestrator for the Adaptive Capability Assessment Engine."""

from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.database import Database

from app.skill_gaps.service import calculate_skill_gaps
from .calibration import (
    DEFAULT_INITIAL_THETA,
    MIN_THETA,
    MAX_THETA,
    map_theta_to_difficulty,
    map_theta_to_level_label,
    calculate_next_theta,
    get_difficulty_fallback_order,
)
from .schemas import (
    AdaptiveStartRequest,
    AdaptiveStartResponse,
    AdaptiveQuestionItem,
    AdaptiveAnswerRequest,
    AdaptiveAnswerResponse,
    AdaptiveFinalizeResponse,
)


def _to_object_id(val: str) -> Optional[ObjectId]:
    return ObjectId(val) if ObjectId.is_valid(val) else None


class AdaptiveAssessmentService:
    """Manages adaptive capability assessment sessions, item selection, and finalization."""

    def __init__(self, database: Database):
        self.db = database

    def _get_competency_details(self, competency_code: str) -> tuple[Optional[ObjectId], str]:
        """Resolves competency ObjectId and title."""
        cleaned = competency_code.strip().upper()
        # Search competencies collection by code or name
        comp = self.db.competencies.find_one({"code": cleaned})
        if not comp:
            try:
                comp = self.db.competencies.find_one({"code": {"$regex": f"^{cleaned}$", "$options": "i"}})
            except Exception:
                pass
        
        if comp:
            return comp["_id"], comp.get("title") or comp.get("name") or cleaned

        # If not present in DB, insert dynamic entry
        c_oid = ObjectId()
        self.db.competencies.insert_one({
            "_id": c_oid,
            "code": cleaned,
            "title": cleaned.replace("_", " ").title(),
            "domain": "STATISTICAL",
            "status": "ACTIVE",
        })
        return c_oid, cleaned.replace("_", " ").title()

    def _select_next_question(
        self,
        competency_code: str,
        target_difficulty: str,
        excluded_question_ids: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Selects an unasked question with graceful difficulty fallback order."""
        fallback_order = get_difficulty_fallback_order(target_difficulty)
        
        for diff in fallback_order:
            query = {
                "competency_code": competency_code.upper(),
                "status": "ACTIVE",
                "question_id": {"$nin": excluded_question_ids},
                "difficulty": diff,
            }
            q_doc = self.db.question_bank.find_one(query)
            if q_doc:
                return q_doc

        # If strict difficulty queries fail, search any unasked question for this competency
        any_query = {
            "competency_code": competency_code.upper(),
            "status": "ACTIVE",
            "question_id": {"$nin": excluded_question_ids},
        }
        return self.db.question_bank.find_one(any_query)

    def _format_question_item(self, q_doc: Dict[str, Any]) -> AdaptiveQuestionItem:
        """Formats a question document for learner presentation, redacting correct answers."""
        return AdaptiveQuestionItem(
            question_id=str(q_doc.get("question_id") or q_doc.get("_id")),
            question_type=q_doc.get("question_type", "MCQ"),
            question_text=q_doc.get("question_text", ""),
            options=q_doc.get("options", []),
            difficulty=q_doc.get("difficulty", "MEDIUM"),
            scenario_context=q_doc.get("scenario_context"),
        )

    def start_session(
        self,
        user_id: str,
        request: AdaptiveStartRequest,
    ) -> AdaptiveStartResponse:
        """Initializes a new adaptive capability assessment session for the user."""
        user_oid = _to_object_id(user_id)
        if not user_oid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

        competency_oid, comp_name = self._get_competency_details(request.competency_code)
        if not competency_oid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Competency code '{request.competency_code}' not found in framework",
            )

        # Validate that competency is applicable to the user's assigned role
        user = self.db.users.find_one({"_id": user_oid})
        if user and user.get("access_role") in ("OFFICIAL", "EMPLOYEE"):
            role_id = user.get("role_id")
            if role_id:
                reqs = list(self.db.role_requirements.find({"role_id": role_id}))
                req_comp_ids = {str(r.get("competency_id")) for r in reqs if "competency_id" in r}
                if req_comp_ids and str(competency_oid) not in req_comp_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Competency '{request.competency_code}' is not applicable to your department/role.",
                    )

        initial_theta = DEFAULT_INITIAL_THETA
        initial_diff = "MEDIUM"


        # Select initial item
        first_q = self._select_next_question(
            competency_code=request.competency_code,
            target_difficulty=initial_diff,
            excluded_question_ids=[],
        )

        asked_ids = []
        q_item = None
        if first_q:
            qid = str(first_q.get("question_id") or first_q.get("_id"))
            asked_ids.append(qid)
            q_item = self._format_question_item(first_q)

        session_oid = ObjectId()
        session_doc = {
            "_id": session_oid,
            "user_id": user_oid,
            "competency_code": request.competency_code.upper(),
            "competency_name": comp_name,
            "competency_id": competency_oid,
            "current_estimated_level": initial_theta,
            "current_difficulty": initial_diff,
            "questions_attempted": 0,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "max_questions": request.max_questions,
            "question_history": [],
            "asked_question_ids": asked_ids,
            "current_question": first_q,
            "started_at": datetime.now(UTC),
            "completed_at": None,
            "status": "IN_PROGRESS",
        }

        self.db.adaptive_assessment_sessions.insert_one(session_doc)

        return AdaptiveStartResponse(
            session_id=str(session_oid),
            competency_code=request.competency_code.upper(),
            competency_name=comp_name,
            estimated_level=initial_theta,
            difficulty=initial_diff,
            proficiency_tier=map_theta_to_level_label(initial_theta),
            current_question_number=1,
            total_questions_planned=request.max_questions,
            question=q_item,
            status="IN_PROGRESS",
        )

    def submit_answer(
        self,
        user_id: str,
        session_id: str,
        request: AdaptiveAnswerRequest,
    ) -> AdaptiveAnswerResponse:
        """Processes an answer, computes calibrated step-up/down theta, and selects next adaptive question."""
        user_oid = _to_object_id(user_id)
        session_oid = _to_object_id(session_id)
        if not user_oid or not session_oid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

        session = self.db.adaptive_assessment_sessions.find_one({
            "_id": session_oid,
            "user_id": user_oid,
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adaptive assessment session not found or access unauthorized",
            )

        if session.get("status") == "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment session is already completed and finalized",
            )

        current_q = session.get("current_question")
        if not current_q:
            # Look up question in question bank
            current_q = self.db.question_bank.find_one({"question_id": request.question_id})
            if not current_q:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        # Evaluate Answer Deterministically
        correct_answer = str(current_q.get("correct_answer", "")).strip().upper()
        selected_raw = str(request.selected_answer).strip().upper()
        
        # Check matching by option key or option text
        is_correct = (selected_raw == correct_answer)
        if not is_correct and current_q.get("options"):
            for idx, opt in enumerate(current_q["options"]):
                opt_letter = chr(65 + idx)
                if selected_raw == opt_letter and correct_answer == opt.strip().upper():
                    is_correct = True
                    break
                elif selected_raw == opt.strip().upper() and correct_answer == opt_letter:
                    is_correct = True
                    break

        q_difficulty = current_q.get("difficulty", "MEDIUM")
        prev_theta = session.get("current_estimated_level", DEFAULT_INITIAL_THETA)
        updated_theta = calculate_next_theta(prev_theta, q_difficulty, is_correct)
        next_difficulty = map_theta_to_difficulty(updated_theta)

        correct_count = session.get("correct_answers", 0) + (1 if is_correct else 0)
        incorrect_count = session.get("incorrect_answers", 0) + (0 if is_correct else 1)
        questions_attempted = session.get("questions_attempted", 0) + 1

        history_entry = {
            "question_id": request.question_id,
            "question_text": current_q.get("question_text", ""),
            "difficulty": q_difficulty,
            "selected_answer": request.selected_answer,
            "is_correct": is_correct,
            "explanation": current_q.get("explanation", "Deterministic question bank evaluation."),
            "theta_before": prev_theta,
            "theta_after": updated_theta,
            "answered_at": datetime.now(UTC),
        }

        history = session.get("question_history", [])
        history.append(history_entry)

        is_complete = (questions_attempted >= session.get("max_questions", 5))

        next_q_item = None
        next_q_doc = None
        asked_ids = list(session.get("asked_question_ids", []))

        if not is_complete:
            next_q_doc = self._select_next_question(
                competency_code=session["competency_code"],
                target_difficulty=next_difficulty,
                excluded_question_ids=asked_ids,
            )
            if next_q_doc:
                next_qid = str(next_q_doc.get("question_id") or next_q_doc.get("_id"))
                asked_ids.append(next_qid)
                next_q_item = self._format_question_item(next_q_doc)
            else:
                # No more unasked questions available
                is_complete = True

        # Update Session
        self.db.adaptive_assessment_sessions.update_one(
            {"_id": session_oid},
            {
                "$set": {
                    "current_estimated_level": updated_theta,
                    "current_difficulty": next_difficulty,
                    "questions_attempted": questions_attempted,
                    "correct_answers": correct_count,
                    "incorrect_answers": incorrect_count,
                    "question_history": history,
                    "asked_question_ids": asked_ids,
                    "current_question": next_q_doc,
                    "updated_at": datetime.now(UTC),
                }
            }
        )

        return AdaptiveAnswerResponse(
            session_id=str(session_oid),
            is_correct=is_correct,
            explanation=current_q.get("explanation"),
            previous_estimated_level=prev_theta,
            updated_estimated_level=updated_theta,
            next_difficulty=next_difficulty,
            proficiency_tier=map_theta_to_level_label(updated_theta),
            questions_completed=questions_attempted,
            total_questions_planned=session.get("max_questions", 5),
            is_complete=is_complete,
            next_question=next_q_item,
        )

    def finalize_session(
        self,
        user_id: str,
        session_id: str,
    ) -> AdaptiveFinalizeResponse:
        """
        Finalizes the assessment:
        1. Calculates final demonstrated capability.
        2. Records AUTHORITATIVE EVIDENCE (confidence: 0.85).
        3. Updates official Competency Profile.
        4. Recalculates Skill Gaps.
        """
        user_oid = _to_object_id(user_id)
        session_oid = _to_object_id(session_id)
        if not user_oid or not session_oid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")

        session = self.db.adaptive_assessment_sessions.find_one({
            "_id": session_oid,
            "user_id": user_oid,
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Adaptive assessment session not found or access unauthorized",
            )

        competency_oid = session.get("competency_id")
        competency_code = session["competency_code"]
        comp_name = session.get("competency_name", competency_code)
        now = datetime.now(UTC)

        final_theta = session.get("current_estimated_level", DEFAULT_INITIAL_THETA)
        history = session.get("question_history", [])
        total_q = max(len(history), 1)
        correct_count = session.get("correct_answers", 0)
        accuracy_pct = round((correct_count / total_q) * 100.0, 1)

        # 1. Fetch Previous Competency Profile Level
        prev_profile = self.db.competency_profiles.find_one({
            "user_id": user_oid,
            "competency_id": competency_oid,
        })
        prev_level = float(prev_profile.get("current_level") or 0.0) if prev_profile else 0.0


        # 2. Fetch Previous Skill Gap
        prev_gap = 0.0
        try:
            gap_resp_before = calculate_skill_gaps(self.db, user_id)
            for g in gap_resp_before.gaps:
                if getattr(g, "competency_code", "") == competency_code:
                    prev_gap = float(getattr(g, "gap", 0.0))
                    break
        except Exception:
            pass

        # 3. Create Authoritative Evidence Record (0.85)
        evidence_oid = ObjectId()
        evidence_doc = {
            "_id": evidence_oid,
            "user_id": user_oid,
            "competency_id": competency_oid,
            "evidence_type": "CAPABILITY_ASSESSMENT",
            "type": "CAPABILITY_ASSESSMENT",
            "score": final_theta,
            "confidence": 0.85,
            "weight": 0.85,
            "source": "adaptive_capability_assessment",
            "assessment_id": session_oid,
            "metadata": {
                "percentage": accuracy_pct,
                "correct_answers": correct_count,
                "total_questions": len(history),
                "competency_code": competency_code,
                "demonstrated_capability": final_theta,
            },
            "created_at": now,
        }
        self.db.competency_evidence.insert_one(evidence_doc)

        # 4. Update Official Competency Profile
        self.db.competency_profiles.update_one(
            {"user_id": user_oid, "competency_id": competency_oid},
            {
                "$set": {
                    "current_level": final_theta,
                    "confidence": 0.85,
                    "last_assessed_at": now,
                    "status": "active",
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "user_id": user_oid,
                    "competency_id": competency_oid,
                }
            },
            upsert=True,
        )

        # 5. Recalculate Skill Gaps
        updated_gap = 0.0
        try:
            gap_resp_after = calculate_skill_gaps(self.db, user_id)
            for g in gap_resp_after.gaps:
                if getattr(g, "competency_code", "") == competency_code:
                    updated_gap = float(getattr(g, "gap", 0.0))
                    break
        except Exception:
            pass

        # 6. Mark Session Completed
        self.db.adaptive_assessment_sessions.update_one(
            {"_id": session_oid},
            {
                "$set": {
                    "status": "COMPLETED",
                    "final_score": final_theta,
                    "accuracy_pct": accuracy_pct,
                    "completed_at": now,
                    "evidence_id": evidence_oid,
                    "previous_competency_level": prev_level,
                    "updated_competency_level": final_theta,
                    "previous_skill_gap": prev_gap,
                    "updated_skill_gap": updated_gap,
                }
            }
        )

        return AdaptiveFinalizeResponse(
            session_id=str(session_oid),
            competency_code=competency_code,
            competency_name=comp_name,
            final_demonstrated_level=final_theta,
            proficiency_tier=map_theta_to_level_label(final_theta),
            total_questions=len(history),
            correct_count=correct_count,
            accuracy_pct=accuracy_pct,
            previous_competency_level=prev_level,
            updated_competency_level=final_theta,
            previous_skill_gap=prev_gap,
            updated_skill_gap=updated_gap,
            evidence_record_id=str(evidence_oid),
            evidence_type="CAPABILITY_ASSESSMENT",
            evidence_confidence=0.85,
            completed_at=now.isoformat(),
            status="COMPLETED",
        )
