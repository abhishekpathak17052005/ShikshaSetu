"""Service layer for capability assessments."""
from datetime import UTC, datetime

from bson import ObjectId
from fastapi import HTTPException, status

from app.assessments import repository as assessment_repo
from app.assessments.schemas import AssessmentScoringConfig
from app.assessments.scoring import prototype_confidence, weighted_competency_score
from app.capability_assessments import repository
from app.capability_assessments.models import CapabilityAssessment, CapabilityAssessmentStatus
from app.capability_assessments.scoring import (
    calculate_assessment_percentage,
    calculate_normalized_score_from_percentage,
    calculate_question_score,
)
from app.questions import repository as question_repo


def _database_or_error(database):
    """Ensure database is available."""
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable"
        )
    return database


def _format_question_for_response(question: dict) -> dict:
    """Format question for response (hide correct answer)."""
    return {
        "question_id": question.get("question_id"),
        "question_type": question.get("question_type"),
        "question_text": question.get("question_text"),
        "options": question.get("options", []),
        "difficulty": question.get("difficulty"),
        "weight": question.get("weight", 1.0),
        "scenario_context": question.get("scenario_context"),
    }


def _format_assessment_for_response(assessment: dict) -> dict:
    """Format assessment document for response (hide internal data)."""
    questions = [_format_question_for_response(q) for q in assessment.get("questions", [])]
    
    return {
        "id": str(assessment.get("_id")),
        "competency_code": assessment.get("competency_code"),
        "assessment_type": assessment.get("assessment_type"),
        "title": assessment.get("title"),
        "questions": questions,
        "status": assessment.get("status"),
        "started_at": assessment.get("started_at"),
        "submitted_at": assessment.get("submitted_at"),
        "score": assessment.get("score"),
        "percentage": assessment.get("percentage"),
        "normalized_score": assessment.get("normalized_score"),
        "duration_seconds": assessment.get("duration_seconds"),
    }


def create_capability_assessment(
    database,
    user_id: str,
    competency_code: str
) -> dict:
    """
    Create a new capability assessment for a user and competency.
    
    Flow:
    1. Validate database
    2. Get assessment configuration for competency
    3. Check for existing IN_PROGRESS assessment (if retake not allowed)
    4. Load questions from question bank based on config
    5. Create assessment document
    6. Return assessment (no answer keys)
    
    Args:
        database: MongoDB database connection
        user_id: User ID creating the assessment
        competency_code: Competency code to assess
    
    Returns:
        Assessment response dict
    
    Raises:
        HTTPException: For validation or database errors
    """
    database = _database_or_error(database)
    user_oid = repository.object_id(user_id)
    
    if user_oid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    # Get configuration for this competency
    config = assessment_repo.get_assessment_configuration(database, competency_code)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment configuration not found for competency {competency_code}"
        )
    
    config_oid = repository.object_id(str(config["_id"]))
    
    # Check for existing IN_PROGRESS assessment (if retake not allowed)
    if not config.get("allow_retake", True):
        existing = repository.get_in_progress_assessment_for_user_and_competency(
            database, user_id, competency_code
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assessment already in progress for this competency. Complete or cancel first."
            )
    
    # Load questions from question bank
    question_types = config.get("assessment_types", ["MCQ", "SCENARIO"])
    num_questions = config.get("number_of_questions", 10)
    difficulty_levels = []
    
    # Map difficulty config to levels
    if config.get("difficulty") == "MIXED":
        difficulty_levels = ["EASY", "MEDIUM", "HARD"]
    elif config.get("difficulty"):
        difficulty_levels = [config.get("difficulty")]
    
    # Get random questions from bank
    questions_from_bank = question_repo.get_random_questions_for_assessment(
        database,
        competency_code=competency_code,
        count=num_questions,
        question_types=question_types,
        difficulties=difficulty_levels if difficulty_levels else None
    )
    
    if not questions_from_bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No questions available for {competency_code} assessment"
        )
    
    # Format questions for storage (without correct answers)
    assessment_questions = []
    for q in questions_from_bank:
        assessment_questions.append({
            "question_id": q.get("question_id"),
            "question_type": q.get("question_type"),
            "question_text": q.get("question_text"),
            "options": q.get("options", []),
            "difficulty": q.get("difficulty"),
            "weight": q.get("weight", 1.0),
            "scenario_context": q.get("scenario_context"),
        })
    
    # Create assessment document
    assessment_doc = CapabilityAssessment.create(
        user_id=user_oid,
        competency_code=competency_code,
        configuration_id=config_oid,
        title=f"{competency_code} Capability Assessment",
        questions=assessment_questions
    )
    
    # Insert into database
    assessment_id = repository.insert_capability_assessment(database, assessment_doc)
    
    # Return formatted response
    assessment_doc["_id"] = repository.object_id(assessment_id)
    return _format_assessment_for_response(assessment_doc)


def get_capability_assessment(
    database,
    user_id: str,
    assessment_id: str
) -> dict:
    """
    Retrieve an assessment (in progress or submitted).
    
    Args:
        database: MongoDB database connection
        user_id: User retrieving the assessment
        assessment_id: Assessment ID
    
    Returns:
        Assessment response dict
    
    Raises:
        HTTPException: If not found or user not authorized
    """
    database = _database_or_error(database)
    
    assessment = repository.get_capability_assessment_for_user(
        database, assessment_id, user_id
    )
    
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    return _format_assessment_for_response(assessment)


def submit_capability_assessment(
    database,
    user_id: str,
    assessment_id: str,
    answers: list[dict]
) -> dict:
    """
    Submit answers for a capability assessment.
    
    Flow:
    1. Validate database and user
    2. Load assessment (verify ownership, status IN_PROGRESS)
    3. Validate all answers provided and valid
    4. Load original questions from question bank (for correct answers)
    5. Score each answer (binary: correct/incorrect)
    6. Calculate percentage and normalized score
    7. Create evidence records (append-only)
    8. Update competency profile
    9. Update assessment status to SUBMITTED
    10. Return results
    
    Args:
        database: MongoDB database connection
        user_id: User submitting answers
        assessment_id: Assessment ID
        answers: List of {question_id, selected_answer} dicts
    
    Returns:
        Submission response dict with scores and competency results
    
    Raises:
        HTTPException: For validation or database errors
    """
    database = _database_or_error(database)
    
    # Load assessment
    assessment = repository.get_capability_assessment_for_user(
        database, assessment_id, user_id
    )
    
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Check status
    if assessment.get("status") != CapabilityAssessmentStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment has already been submitted"
        )
    
    # Validate answers
    assessment_questions = {q["question_id"]: q for q in assessment.get("questions", [])}
    
    if not answers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No answers provided"
        )
    
    # Check all questions answered
    answer_question_ids = {a["question_id"] for a in answers}
    assessment_question_ids = set(assessment_questions.keys())
    
    if answer_question_ids != assessment_question_ids:
        missing = assessment_question_ids - answer_question_ids
        extra = answer_question_ids - assessment_question_ids
        
        if missing:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing answers for questions: {missing}"
            )
        if extra:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown questions in answers: {extra}"
            )
    
    # Check for duplicate answers
    if len(answer_question_ids) != len(answers):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Duplicate question answers"
        )
    
    # Load original questions from question bank to get correct answers
    # (questions in assessment don't have correct_answer for security)
    original_questions = {}
    for question_id in assessment_question_ids:
        original_question = question_repo.get_question_by_id(database, question_id)
        if original_question is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Question not found in database: {question_id}"
            )
        original_questions[question_id] = original_question
    
    # Score each answer (server-side only)
    scored_answers = []
    correct_count = 0
    
    for answer in answers:
        question_id = answer["question_id"]
        selected_answer = answer["selected_answer"]
        original_question = original_questions[question_id]
        correct_answer = original_question.get("correct_answer")
        
        # Validate selected answer is a valid option
        if selected_answer not in original_question.get("options", []):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid option for question {question_id}: {selected_answer}"
            )
        
        is_correct = calculate_question_score(selected_answer, correct_answer) == 1.0
        
        scored_answers.append({
            "question_id": question_id,
            "selected_answer": selected_answer,
            "is_correct": is_correct,
        })
        
        if is_correct:
            correct_count += 1
    
    # Calculate scores
    percentage = calculate_assessment_percentage(scored_answers)
    normalized_score = calculate_normalized_score_from_percentage(percentage)
    
    # Calculate duration
    started_at = assessment.get("started_at")
    if started_at and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    duration_seconds = int((now - started_at).total_seconds()) if started_at else None
    
    # Create evidence records (append-only)
    # Use same pattern as Phase 1 initial assessment
    config = AssessmentScoringConfig()  # Use default weights
    
    user_oid = repository.object_id(user_id)
    competency_code = assessment.get("competency_code")
    
    # Get competency ID from competencies collection
    competency = database.competencies.find_one({"code": competency_code})
    if competency is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Competency not found: {competency_code}"
        )
    
    competency_oid = competency["_id"]
    
    # Create evidence record for this assessment
    # All answers treated as KNOWLEDGE_TEST (MCQ + SCENARIO combined)
    evidence_doc = {
        "user_id": user_oid,
        "competency_id": competency_oid,
        "evidence_type": "KNOWLEDGE_TEST",  # Covers MCQ and SCENARIO
        "score": normalized_score,  # 1-5 scale
        "weight": config.knowledge_test_weight,  # 40%
        "source": "capability_assessment",
        "assessment_id": repository.object_id(assessment_id),
        "metadata": {
            "percentage": percentage,
            "correct_answers": correct_count,
            "total_questions": len(scored_answers),
            "competency_code": competency_code,
        },
        "created_at": now,
    }
    
    assessment_repo.insert_evidence(database, evidence_doc)
    
    # Get all evidence for this competency to recalculate profile
    all_evidence_docs = list(database.competency_evidence.find({
        "user_id": user_oid,
        "competency_id": competency_oid
    }))
    
    # Aggregate evidence into components
    components = {}
    for evidence in all_evidence_docs:
        evidence_type = evidence.get("evidence_type")
        # Map evidence type to component
        component_name = {
            "SELF_ASSESSMENT": "self_assessment",
            "KNOWLEDGE_TEST": "knowledge_test",
            "SCENARIO_TEST": "scenario_test",
            "TRAINING": "training_evidence",
            "QUIZ": "knowledge_test",  # Quiz counts as knowledge test
        }.get(evidence_type)
        
        if component_name:
            # Take average if multiple evidence of same type
            if component_name not in components:
                components[component_name] = []
            components[component_name].append(evidence.get("score"))
    
    # Average multiple evidence of same type
    component_averages = {}
    for component, scores in components.items():
        component_averages[component] = sum(scores) / len(scores) if scores else None
    
    # Calculate final competency score and confidence
    final_score = weighted_competency_score(component_averages, config)
    final_confidence = prototype_confidence(component_averages, config)
    
    # Update competency profile
    assessment_repo.upsert_profile(
        database,
        user_oid,
        competency_oid,
        {
            "current_level": final_score,
            "confidence": final_confidence,
            "last_assessed_at": now,
            "status": "active",
            "updated_at": now,
        }
    )
    
    # Update assessment with results
    update_dict = {
        "answers": scored_answers,
        "status": CapabilityAssessmentStatus.SUBMITTED,
        "score": percentage,  # Raw score (0-1)
        "percentage": percentage,
        "normalized_score": normalized_score,
        "submitted_at": now,
        "duration_seconds": duration_seconds,
        "competency_results": [
            {
                "competency_code": competency_code,
                "score": final_score,
                "confidence": final_confidence,
            }
        ],
        "updated_at": now,
    }
    
    updated_assessment = repository.update_assessment_status_and_submit(
        database, assessment_id, user_id, update_dict
    )
    
    if updated_assessment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Assessment was already submitted by another request"
        )
    
    # Return submission response
    return {
        "assessment_id": assessment_id,
        "competency_code": competency_code,
        "status": CapabilityAssessmentStatus.SUBMITTED,
        "score": percentage,
        "percentage": percentage,
        "normalized_score": normalized_score,
        "competency_results": [
            {
                "competency_code": competency_code,
                "score": final_score,
                "confidence": final_confidence,
            }
        ],
        "submitted_at": now,
    }


def get_capability_assessment_results(
    database,
    user_id: str,
    assessment_id: str
) -> dict:
    """
    Get results of a submitted capability assessment.
    
    Args:
        database: MongoDB database connection
        user_id: User retrieving results
        assessment_id: Assessment ID
    
    Returns:
        Assessment results dict
    
    Raises:
        HTTPException: If not found, not submitted, or user not authorized
    """
    database = _database_or_error(database)
    
    assessment = repository.get_submitted_assessment_results(
        database, assessment_id, user_id
    )
    
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found or not yet submitted"
        )
    
    answers = assessment.get("answers", [])
    correct_count = sum(1 for a in answers if a.get("is_correct", False))
    total_questions = len(answers)
    
    return {
        "assessment_id": assessment_id,
        "competency_code": assessment.get("competency_code"),
        "status": assessment.get("status"),
        "score": assessment.get("score"),
        "percentage": assessment.get("percentage"),
        "normalized_score": assessment.get("normalized_score"),
        "duration_seconds": assessment.get("duration_seconds"),
        "correct_answers": correct_count,
        "total_questions": total_questions,
        "competency_results": assessment.get("competency_results", []),
        "submitted_at": assessment.get("submitted_at"),
        "started_at": assessment.get("started_at"),
    }


def list_user_capability_assessments(
    database,
    user_id: str,
    competency_code: str | None = None,
    status: str | None = None,
    limit: int = 100
) -> list[dict]:
    """
    List capability assessments for a user.
    
    Args:
        database: MongoDB database connection
        user_id: User ID
        competency_code: Optional filter by competency
        status: Optional filter by status (IN_PROGRESS, SUBMITTED)
        limit: Maximum results to return
    
    Returns:
        List of assessment summary dicts
    """
    database = _database_or_error(database)
    
    assessments = repository.get_user_capability_assessments(
        database, user_id, competency_code, status, limit
    )
    
    result = []
    for assessment in assessments:
        result.append({
            "id": str(assessment.get("_id")),
            "competency_code": assessment.get("competency_code"),
            "title": assessment.get("title"),
            "status": assessment.get("status"),
            "score": assessment.get("score"),
            "percentage": assessment.get("percentage"),
            "started_at": assessment.get("started_at"),
            "submitted_at": assessment.get("submitted_at"),
        })
    
    return result
