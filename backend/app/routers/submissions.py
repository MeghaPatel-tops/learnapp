from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.assignment import EvaluateSubmissionRequest, SubmissionOut
from app.schemas.common import PaginatedResponse
from app.services import assignment_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/submissions", tags=["Submissions & Evaluation"])


@router.get("", response_model=PaginatedResponse[SubmissionOut])
def list_submissions(
    assignment_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List submissions (Student: own only; Instructor: assigned courses/batches; Admin: all)."""
    return assignment_service.list_submissions(
        db=db,
        current_user=current_user,
        assignment_id=assignment_id,
        status_filter=status_filter,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def submit_assignment(
    assignment_id: int = Form(...),
    submission_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("student")),
):
    """Submit an assignment answer (Student only)."""
    return await assignment_service.submit_assignment(
        db=db,
        assignment_id=assignment_id,
        submission_text=submission_text,
        file=file,
        current_user=current_user,
    )


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View submission details and feedback."""
    return assignment_service.get_submission_detail(db, submission_id, current_user)


@router.get("/{submission_id}/download")
def download_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a submission attachment file (owner student, assigned instructor, or admin)."""
    return assignment_service.download_submission_file(db, submission_id, current_user)


@router.patch("/{submission_id}/review", response_model=SubmissionOut)
def mark_under_review(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Mark a submission as under_review."""
    return assignment_service.mark_under_review(db, submission_id, current_user)


@router.post("/{submission_id}/evaluate", response_model=SubmissionOut)
def evaluate_submission(
    submission_id: int,
    payload: EvaluateSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Evaluate a student submission and assign marks/feedback."""
    return assignment_service.evaluate_submission(db, submission_id, payload, current_user)
