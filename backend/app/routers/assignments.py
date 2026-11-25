from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.assignment import AssignmentCreateRequest, AssignmentOut, AssignmentUpdateRequest
from app.schemas.common import PaginatedResponse
from app.services import assignment_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


@router.get("", response_model=PaginatedResponse[AssignmentOut])
def list_assignments(
    course_id: Optional[int] = Query(None),
    batch_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List assignments scoped by role and course/batch."""
    return assignment_service.list_assignments(
        db=db,
        current_user=current_user,
        course_id=course_id,
        batch_id=batch_id,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Create an assignment for a course or batch (Admin or assigned Instructor)."""
    return assignment_service.create_assignment(db, payload, current_user)


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get assignment details."""
    return assignment_service.get_assignment(db, assignment_id, current_user)


@router.put("/{assignment_id}", response_model=AssignmentOut)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update assignment details."""
    return assignment_service.update_assignment(db, assignment_id, payload, current_user)


@router.post("/{assignment_id}/attachment", response_model=AssignmentOut)
async def upload_assignment_attachment(
    assignment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Upload a reference attachment file for an assignment."""
    return await assignment_service.upload_assignment_attachment(db, assignment_id, file, current_user)


@router.get("/{assignment_id}/attachment")
def download_assignment_attachment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download an assignment's reference attachment."""
    return assignment_service.download_assignment_attachment(db, assignment_id, current_user)
