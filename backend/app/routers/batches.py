from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.batch import (
    BatchCreateRequest,
    BatchDetailOut,
    BatchOut,
    BatchStatus,
    BatchStudentAddRequest,
    BatchUpdateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services import batch_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/batches", tags=["Batches"])


@router.get("", response_model=PaginatedResponse[BatchOut])
def list_batches(
    pagination: PaginationParams = Depends(),
    course_id: Optional[int] = Query(None),
    status_filter: Optional[BatchStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List batches scoped by role (Admin: all; Instructor: assigned; Student: own)."""
    return batch_service.list_batches(
        db=db,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        course_id=course_id,
        status_filter=status_filter,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=BatchDetailOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Create a course batch (Admin only)."""
    return batch_service.create_batch(db, payload)


@router.get("/{batch_id}", response_model=BatchDetailOut)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get batch details and student roster."""
    return batch_service.get_batch_detail(db, batch_id, current_user)


@router.put("/{batch_id}", response_model=BatchDetailOut)
def update_batch(
    batch_id: int,
    payload: BatchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update batch metadata (Admin or assigned Instructor)."""
    return batch_service.update_batch(db, batch_id, payload, current_user)


@router.post("/{batch_id}/close", response_model=BatchDetailOut)
def close_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Close a batch to further enrollments (Admin only)."""
    return batch_service.set_batch_status(db, batch_id, "closed")


@router.post("/{batch_id}/archive", response_model=BatchDetailOut)
def archive_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Archive a batch (Admin only)."""
    return batch_service.set_batch_status(db, batch_id, "archived")


@router.post("/{batch_id}/students", response_model=BatchDetailOut, status_code=status.HTTP_201_CREATED)
def add_student_to_batch(
    batch_id: int,
    payload: BatchStudentAddRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Add a student to a batch with capacity and course-enrollment validation (Admin only)."""
    return batch_service.add_student_to_batch(db, batch_id, payload.student_id)


@router.delete("/{batch_id}/students/{student_id}", response_model=BatchDetailOut)
def remove_student_from_batch(
    batch_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Remove a student from a batch (Admin only)."""
    return batch_service.remove_student_from_batch(db, batch_id, student_id)
