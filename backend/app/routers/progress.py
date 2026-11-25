from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.progress import CourseProgressOut
from app.services import progress_service
from app.services.authorization import get_user_role

router = APIRouter(prefix="/api/progress", tags=["Student Progress"])


@router.get("/courses/{course_id}", response_model=CourseProgressOut)
def get_course_progress(
    course_id: int,
    student_id: Optional[int] = Query(None, description="Student user ID (for Admin/Instructor)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate and return student progress metrics for a course."""
    target_id = current_user.id if get_user_role(current_user) == "student" else (student_id or current_user.id)
    return progress_service.get_student_course_progress(db, target_id, course_id, current_user)
