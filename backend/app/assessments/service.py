from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status

from app.assessments import repository
from app.assessments.schemas import AssessmentAnswer, AssessmentScoringConfig, QuestionType, SubmitAssessmentRequest
from app.assessments.scoring import prototype_confidence, score_ratio, weighted_competency_score


def database_or_error(database):
    if database is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    return database


def public_question(question: dict) -> dict:
    return {
        key: str(value) if key == "competency_id" else value
        for key, value in question.items()
        if key != "correct_answer"
    }


def public_attempt(attempt: dict) -> dict:
    return {
        "id": str(attempt["_id"]),
        "assessment_id": str(attempt["assessment_id"]),
        "assessment_type": attempt["assessment_type"],
        "assessment_version": attempt["assessment_version"],
        "status": attempt["status"],
        "questions": [public_question(question) for question in attempt["questions"]],
        "started_at": attempt["started_at"],
        "submitted_at": attempt.get("submitted_at"),
        "competency_results": attempt.get("competency_results", []),
    }


def start_assessment(database, user_id: str, assessment_key: str) -> dict:
    database = database_or_error(database)
    assessment = repository.get_assessment(database, assessment_key)
    user_object_id = repository.object_id(user_id)
    if assessment is None or user_object_id is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    now = datetime.now(UTC)
    attempt = {
        "_id": ObjectId(),
        "user_id": user_object_id,
        "assessment_id": assessment["_id"],
        "assessment_type": assessment["assessment_type"],
        "assessment_version": assessment["version"],
        "questions": assessment["questions"],
        "responses": [],
        "self_ratings": {},
        "training_evidence": [],
        "status": "IN_PROGRESS",
        "started_at": now,
        "submitted_at": None,
        "competency_results": [],
    }
    repository.insert_attempt(database, attempt)
    return public_attempt(attempt)


def get_attempt(database, user_id: str, attempt_id: str) -> dict:
    database = database_or_error(database)
    attempt = repository.get_attempt_for_user(database, attempt_id, user_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    return public_attempt(attempt)


def _validate_answers(attempt: dict, submission: SubmitAssessmentRequest) -> None:
    questions = {question["question_id"]: question for question in attempt["questions"]}
    answers: list[AssessmentAnswer] = submission.answers
    if len({answer.question_id for answer in answers}) != len(answers):
        raise HTTPException(status_code=422, detail="Duplicate question response")
    for answer in answers:
        question = questions.get(answer.question_id)
        if question is None or question["question_type"] == QuestionType.SELF_RATING.value:
            raise HTTPException(status_code=422, detail="Invalid question response")
        if answer.answer not in question["options"]:
            raise HTTPException(status_code=422, detail="Answer is not a valid option")

    expected_question_ids = {
        question["question_id"]
        for question in attempt["questions"]
        if question["question_type"] != QuestionType.SELF_RATING.value
    }
    if expected_question_ids - {answer.question_id for answer in answers}:
        raise HTTPException(status_code=422, detail="All knowledge and scenario questions are required")

    competency_ids = {str(question["competency_id"]) for question in attempt["questions"]}
    if set(submission.self_ratings) - competency_ids:
        raise HTTPException(status_code=422, detail="Invalid competency in self assessment")
    self_question_competencies = {
        str(question["competency_id"])
        for question in attempt["questions"]
        if question["question_type"] == QuestionType.SELF_RATING.value
    }
    if self_question_competencies - set(submission.self_ratings):
        raise HTTPException(status_code=422, detail="Self assessment is required for each competency")
    if any(
        competency_id not in competency_ids
        for evidence in submission.training_evidence
        for competency_id in evidence.competencies
    ):
        raise HTTPException(status_code=422, detail="Invalid competency in training evidence")


def submit_assessment(database, user_id: str, attempt_id: str, submission: SubmitAssessmentRequest) -> dict:
    database = database_or_error(database)
    attempt = repository.get_attempt_for_user(database, attempt_id, user_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found")
    if attempt["status"] != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Assessment attempt is already submitted")
    _validate_answers(attempt, submission)

    config = AssessmentScoringConfig()
    answer_map = {answer.question_id: answer.answer for answer in submission.answers}
    grouped: dict[str, dict[str, float | None]] = {}
    for competency_id, rating in submission.self_ratings.items():
        grouped.setdefault(competency_id, {})["self_assessment"] = rating
    for question in attempt["questions"]:
        competency_id = str(question["competency_id"])
        if question["question_type"] == QuestionType.MCQ.value:
            grouped.setdefault(competency_id, {})["knowledge_test"] = score_ratio(float(answer_map.get(question["question_id"]) == question["correct_answer"]))
        elif question["question_type"] == QuestionType.SCENARIO.value:
            grouped.setdefault(competency_id, {})["scenario_test"] = score_ratio(float(answer_map.get(question["question_id"]) == question["correct_answer"]))
    for evidence in submission.training_evidence:
        for competency_id in evidence.competencies:
            if competency_id in grouped:
                grouped[competency_id]["training_evidence"] = config.training_evidence_score

    now = datetime.now(UTC)
    results = []
    evidence_documents = []
    for competency_id, components in grouped.items():
        score = weighted_competency_score(components, config)
        confidence = prototype_confidence(components, config)
        results.append({"competency_id": competency_id, "score": score, "confidence": confidence})
        competency_object_id = repository.object_id(competency_id)
        user_object_id = repository.object_id(user_id)
        if competency_object_id is None or user_object_id is None:
            raise HTTPException(status_code=422, detail="Invalid competency reference")
        for evidence_type, component_score in components.items():
            evidence_documents.append({
                "user_id": user_object_id,
                "competency_id": competency_object_id,
                "evidence_type": {"self_assessment": "SELF_ASSESSMENT", "knowledge_test": "KNOWLEDGE_TEST", "scenario_test": "SCENARIO_TEST", "training_evidence": "TRAINING"}[evidence_type],
                "score": component_score,
                "weight": {"self_assessment": config.self_assessment_weight, "knowledge_test": config.knowledge_test_weight, "scenario_test": config.scenario_test_weight, "training_evidence": config.training_evidence_weight}[evidence_type],
                "source": "initial_assessment",
                "assessment_id": attempt["assessment_id"],
                "metadata": {"assessment_version": attempt["assessment_version"]},
                "created_at": now,
            })
        repository.upsert_profile(database, user_object_id, competency_object_id, {"current_level": score, "confidence": confidence, "last_assessed_at": now, "status": "active", "updated_at": now})
    for evidence in evidence_documents:
        repository.insert_evidence(database, evidence)

    update = {"responses": submission.answers and [answer.model_dump() for answer in submission.answers] or [], "self_ratings": submission.self_ratings, "training_evidence": [item.model_dump() for item in submission.training_evidence], "scores": grouped, "competency_scores": results, "competency_results": results, "status": "SUBMITTED", "submitted_at": now}
    updated_attempt = repository.submit_attempt(database, attempt_id, user_id, update)
    if updated_attempt is None:
        raise HTTPException(status_code=409, detail="Assessment attempt is already submitted")
    return {"attempt_id": str(updated_attempt["_id"]), "status": updated_attempt["status"], "competency_results": results}


def get_assessment_configuration(database, competency_code: str) -> dict:
    database = database_or_error(database)
    config = repository.get_assessment_configuration(database, competency_code)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment configuration not found")
    result = dict(config)
    result["id"] = str(result.pop("_id"))
    return result


def get_all_assessment_configurations(database) -> list[dict]:
    database = database_or_error(database)
    configs = repository.get_all_assessment_configurations(database)
    results = []
    for c in configs:
        item = dict(c)
        item["id"] = str(item.pop("_id"))
        results.append(item)
    return results

