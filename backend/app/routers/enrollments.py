from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.batch import (
    EnrollmentCreateRequest,
    EnrollmentOut,
    EnrollmentStatus,
    EnrollmentUpdateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services import batch_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/enrollments", tags=["Enrollments"])


@router.get("", response_model=PaginatedResponse[EnrollmentOut])
def list_enrollments(
    pagination: PaginationParams = Depends(),
    course_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    status_filter: Optional[EnrollmentStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List enrollments scoped by role."""
    return batch_service.list_enrollments(
        db=db,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        course_id=course_id,
        student_id=student_id,
        status_filter=status_filter,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    payload: EnrollmentCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Enroll a student into a published course (Admin only)."""
    return batch_service.create_enrollment(db, payload)


@router.put("/{enrollment_id}", response_model=EnrollmentOut)
def update_enrollment(
    enrollment_id: int,
    payload: EnrollmentUpdateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Update an enrollment status (Admin only)."""
    return batch_service.update_enrollment(db, enrollment_id, payload)
