from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.profiles import (
    StudentCreateRequest,
    StudentDetailOut,
    StudentOut,
    StudentUpdateRequest,
)
from app.services import profile_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=PaginatedResponse[StudentOut])
def list_students(
    pagination: PaginationParams = Depends(),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """List students (Admin: all; Instructor: students in assigned courses)."""
    return profile_service.list_students(
        db=db,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        is_active=is_active,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Create a student account and profile (Admin only)."""
    return profile_service.create_student(db, payload)


@router.get("/{student_id}", response_model=StudentDetailOut)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View student profile, enrollments, batches, and attendance summary."""
    return profile_service.get_student_detail(db, student_id, current_user)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "student")),
):
    """Update student profile details."""
    return profile_service.update_student(db, student_id, payload, current_user)


@router.delete("/{student_id}", response_model=StudentOut)
def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Deactivate a student account (Admin only)."""
    return profile_service.deactivate_student(db, student_id, admin.id)
