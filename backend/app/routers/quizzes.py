from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.quiz import (
    QuestionCreate,
    QuestionOut,
    QuizAttemptOut,
    QuizCreateRequest,
    QuizDetailOut,
    QuizOut,
    QuizUpdateRequest,
    SaveAnswerRequest,
)
from app.services import quiz_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes & Examinations"])


@router.get("", response_model=PaginatedResponse[QuizOut])
def list_quizzes(
    course_id: Optional[int] = Query(None),
    batch_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List quizzes scoped by role."""
    return quiz_service.list_quizzes(
        db=db,
        current_user=current_user,
        course_id=course_id,
        batch_id=batch_id,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=QuizDetailOut, status_code=status.HTTP_201_CREATED)
def create_quiz(
    payload: QuizCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Create a quiz with optional initial questions (Admin or assigned Instructor)."""
    return quiz_service.create_quiz(db, payload, current_user)


@router.get("/{quiz_id}", response_model=QuizDetailOut)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View quiz details (correct answers are hidden from students)."""
    return quiz_service.get_quiz_detail(db, quiz_id, current_user)


@router.put("/{quiz_id}", response_model=QuizDetailOut)
def update_quiz(
    quiz_id: int,
    payload: QuizUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update quiz configuration."""
    return quiz_service.update_quiz(db, quiz_id, payload, current_user)


@router.post("/{quiz_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def add_question(
    quiz_id: int,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Add an MCQ question with options to a quiz."""
    return quiz_service.add_question_to_quiz(db, quiz_id, payload, current_user)


@router.post("/{quiz_id}/attempts/start", response_model=QuizAttemptOut, status_code=status.HTTP_201_CREATED)
def start_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("student")),
):
    """Start a timed quiz attempt (Student only)."""
    return quiz_service.start_quiz_attempt(db, quiz_id, current_user)


@router.put("/attempts/{attempt_id}/answer", response_model=QuizAttemptOut)
def save_answer(
    attempt_id: int,
    payload: SaveAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("student")),
):
    """Save or update an answer during an active quiz attempt."""
    return quiz_service.save_quiz_answer(db, attempt_id, payload, current_user)


@router.post("/attempts/{attempt_id}/submit", response_model=QuizAttemptOut)
def submit_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("student")),
):
    """Submit a quiz attempt for server-side grading."""
    return quiz_service.submit_quiz_attempt(db, attempt_id, current_user)


@router.get("/attempts/{attempt_id}", response_model=QuizAttemptOut)
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View a specific quiz attempt and permitted results."""
    return quiz_service.get_attempt_detail(db, attempt_id, current_user)


@router.get("/{quiz_id}/attempts", response_model=List[QuizAttemptOut])
def list_quiz_attempts(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List attempts for a quiz (Student: own attempts; Instructor/Admin: all)."""
    return quiz_service.list_quiz_attempts(db, quiz_id, current_user)
