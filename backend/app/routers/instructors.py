from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.profiles import (
    InstructorCreateRequest,
    InstructorDetailOut,
    InstructorOut,
    InstructorUpdateRequest,
)
from app.services import profile_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/instructors", tags=["Instructors"])


@router.get("", response_model=PaginatedResponse[InstructorOut])
def list_instructors(
    pagination: PaginationParams = Depends(),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "instructor")),
):
    """List instructors (Admin and Instructor access)."""
    return profile_service.list_instructors(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        is_active=is_active,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=InstructorOut, status_code=status.HTTP_201_CREATED)
def create_instructor(
    payload: InstructorCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Create an instructor account and profile (Admin only)."""
    return profile_service.create_instructor(db, payload)


@router.get("/{instructor_id}", response_model=InstructorDetailOut)
def get_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("admin", "instructor")),
):
    """View instructor profile with assigned courses and batches."""
    return profile_service.get_instructor_detail(db, instructor_id)


@router.put("/{instructor_id}", response_model=InstructorOut)
def update_instructor(
    instructor_id: int,
    payload: InstructorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update instructor profile details."""
    return profile_service.update_instructor(db, instructor_id, payload, current_user)


@router.delete("/{instructor_id}", response_model=InstructorOut)
def deactivate_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Deactivate an instructor account (Admin only)."""
    return profile_service.deactivate_instructor(db, instructor_id, admin.id)
