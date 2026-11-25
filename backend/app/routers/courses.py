from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.course import (
    AssignInstructorRequest,
    CourseCreateRequest,
    CourseDetailOut,
    CourseModuleCreateRequest,
    CourseModuleOut,
    CourseModuleUpdateRequest,
    CourseOut,
    CourseStatus,
    CourseUpdateRequest,
)
from app.services import course_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/courses", tags=["Courses & Modules"])


@router.get("", response_model=PaginatedResponse[CourseOut])
def list_courses(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(None),
    status_filter: Optional[CourseStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List courses scoped by role (Admin: all; Instructor: assigned; Student: enrolled)."""
    return course_service.list_courses(
        db=db,
        current_user=current_user,
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        category=category,
        status_filter=status_filter,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=CourseDetailOut, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Create a new course (Admin only)."""
    return course_service.create_course(db, payload)


@router.get("/{course_id}", response_model=CourseDetailOut)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get course details, modules, and assigned instructors."""
    return course_service.get_course_detail(db, course_id, current_user)


@router.put("/{course_id}", response_model=CourseDetailOut)
def update_course(
    course_id: int,
    payload: CourseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update course details (Admin or assigned Instructor)."""
    return course_service.update_course(db, course_id, payload, current_user)


@router.post("/{course_id}/publish", response_model=CourseDetailOut)
def publish_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Publish a course (Admin only)."""
    return course_service.set_course_status(db, course_id, "published")


@router.post("/{course_id}/unpublish", response_model=CourseDetailOut)
def unpublish_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Unpublish a course back to draft (Admin only)."""
    return course_service.set_course_status(db, course_id, "draft")


@router.post("/{course_id}/archive", response_model=CourseDetailOut)
def archive_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Archive a course (Admin only)."""
    return course_service.set_course_status(db, course_id, "archived")


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Delete a course if it has no enrollments, batches, or payments (Admin only)."""
    course_service.delete_course(db, course_id)


@router.post("/{course_id}/instructors", response_model=CourseDetailOut)
def assign_instructor(
    course_id: int,
    payload: AssignInstructorRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Assign an instructor to a course (Admin only)."""
    return course_service.assign_instructor(db, course_id, payload.instructor_id)


@router.delete("/{course_id}/instructors/{instructor_id}", response_model=CourseDetailOut)
def remove_instructor(
    course_id: int,
    instructor_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Remove an instructor assignment from a course (Admin only)."""
    return course_service.remove_instructor(db, course_id, instructor_id)


@router.get("/{course_id}/modules", response_model=List[CourseModuleOut])
def list_modules(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List modules for an authorized course."""
    return course_service.list_modules(db, course_id, current_user)


@router.post("/{course_id}/modules", response_model=CourseModuleOut, status_code=status.HTTP_201_CREATED)
def create_module(
    course_id: int,
    payload: CourseModuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Create a module in a course (Admin or assigned Instructor)."""
    return course_service.create_module(db, course_id, payload, current_user)


@router.put("/{course_id}/modules/{module_id}", response_model=CourseModuleOut)
def update_module(
    course_id: int,
    module_id: int,
    payload: CourseModuleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update a course module (Admin or assigned Instructor)."""
    return course_service.update_module(db, course_id, module_id, payload, current_user)


@router.delete("/{course_id}/modules/{module_id}", response_model=MessageResponse)
def delete_module(
    course_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Delete a course module (Admin or assigned Instructor)."""
    course_service.delete_module(db, course_id, module_id, current_user)
    return MessageResponse(message="Module deleted successfully.")
