from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.quizzes import repository as quiz_repo
from app.quizzes.service import QuizService, QuizServiceError
from app.quizzes.schemas import (
    QuizCreateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizQuestionResponse,
)
from app.trainer.repository import TrainerRepository


router = APIRouter(prefix="/quizzes", tags=["quizzes"])
CurrentUser = Annotated[dict, Depends(get_current_user)]


@router.get("/assigned", response_model=list[QuizResponse])
def get_assigned_quizzes(
    request: Request,
    current_user: CurrentUser,
) -> list[dict]:
    """
    List all trainer-assigned and published quizzes available for the current learner.
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available",
        )
    user_id = str(current_user["_id"])
    quizzes = TrainerRepository.list_assigned_quizzes_for_learner(database, user_id)
    
    result = []
    for quiz in quizzes:
        questions_response = []
        for q in quiz.get("questions", []):
            questions_response.append(QuizQuestionResponse(
                question_id=str(q.get("question_id", q.get("_id", ""))),
                question=q.get("question", ""),
                options=q.get("options", []),
                difficulty=q.get("difficulty", "MEDIUM"),
                source_chunks=q.get("source_chunks", []),
            ))
        result.append(QuizResponse(
            _id=str(quiz["_id"]),
            title=quiz.get("title", ""),
            competency_code=quiz.get("competency_code", ""),
            question_count=quiz.get("question_count", len(questions_response)),
            status=quiz.get("status", "PUBLISHED"),
            questions=questions_response,
            created_at=quiz.get("created_at", datetime.now(UTC)),
        ))
    return result



@router.post("", response_model=QuizResponse)
def create_quiz(
    request: Request,
    payload: QuizCreateRequest,
    current_user: CurrentUser,
) -> dict:
    """
    Create a quiz from learning material.
    
    The quiz will have questions generated from the material using Phase 6.
    Correct answers are hidden until submission.
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available",
        )
    
    # Initialize quiz indexes
    quiz_repo.create_quiz_indexes(database)
    quiz_repo.create_quiz_attempt_indexes(database)

    service = QuizService(database)
    
    try:
        quiz = service.create_quiz(
            user_id=str(current_user["_id"]),
            material_id=payload.material_id,
            competency_code=payload.competency_code,
            questions=[{
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "source_chunks": q.source_chunks,
            } for q in payload.questions],
        )

        # Convert questions to response schema (hide correct answers)
        questions_response = []
        for q in quiz["questions"]:
            questions_response.append(QuizQuestionResponse(
                question_id=q["question_id"],
                question=q["question"],
                options=q["options"],
                difficulty=q["difficulty"],
                source_chunks=q.get("source_chunks", []),
            ))

        return QuizResponse(
            _id=str(quiz["_id"]),
            title=quiz["title"],
            competency_code=quiz["competency_code"],
            question_count=quiz["question_count"],
            status=quiz["status"],
            questions=questions_response,
            created_at=quiz["created_at"],
        )

    except QuizServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quiz",
        )


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    request: Request,
    quiz_id: str,
    current_user: CurrentUser,
) -> dict:
    """
    Retrieve a quiz by ID.
    
    Correct answers are hidden before submission.
    User can only retrieve their own quizzes.
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available",
        )
    
    service = QuizService(database)
    
    try:
        quiz = service.get_quiz(
            user_id=str(current_user["_id"]),
            quiz_id=quiz_id,
        )

        # Convert questions to response schema (hide correct answers)
        questions_response = []
        for q in quiz["questions"]:
            questions_response.append(QuizQuestionResponse(
                question_id=q["question_id"],
                question=q["question"],
                options=q["options"],
                difficulty=q["difficulty"],
                source_chunks=q.get("source_chunks", []),
            ))

        return QuizResponse(
            _id=str(quiz["_id"]),
            title=quiz["title"],
            competency_code=quiz["competency_code"],
            question_count=quiz["question_count"],
            status=quiz["status"],
            questions=questions_response,
            created_at=quiz["created_at"],
        )

    except QuizServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quiz",
        )


@router.post("/{quiz_id}/submit", response_model=QuizResultResponse)
def submit_quiz(
    request: Request,
    quiz_id: str,
    payload: QuizSubmitRequest,
    current_user: CurrentUser,
) -> dict:
    """
    Submit quiz answers.
    
    Server calculates score server-side (client score is ignored).
    Correct answers are revealed in the response.
    Competency profile is updated deterministically.
    Evidence is created and linked to the quiz attempt.
    """
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not available",
        )
    
    service = QuizService(database)
    
    try:
        result = service.submit_quiz(
            user_id=str(current_user["_id"]),
            quiz_id=quiz_id,
            answers=[{"question_id": a.question_id, "selected_answer": a.selected_answer} for a in payload.answers],
        )

        return QuizResultResponse(
            _id=str(result["_id"]),
            quiz_id=result["quiz_id"],
            score=result["score"],
            percentage=result["percentage"],
            correct_count=result["correct_count"],
            total_questions=result["total_questions"],
            competency=result["competency"],
            skill_gap=result["skill_gap"],
            explanations=result["explanations"],
            submitted_at=result["submitted_at"],
        )

    except QuizServiceError as e:
        if "already submitted" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit quiz",
        )
