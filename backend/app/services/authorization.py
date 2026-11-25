from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Batch, Course, CourseInstructor, Enrollment
from app.models.user import User


def get_user_role(user: User) -> str:
    return user.role.name if user.role else ""


def is_instructor_assigned_to_course(db: Session, user: User, course_id: int) -> bool:
    """Return True if the instructor is primary, co-instructor, or batch instructor for course_id."""
    if not user.instructor_profile:
        return False
    inst_id = user.instructor_profile.id

    course = db.execute(
        select(Course).where(Course.id == course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if not course:
        return False

    if course.primary_instructor_id == inst_id:
        return True

    co_assigned = db.execute(
        select(CourseInstructor.id).where(
            CourseInstructor.course_id == course_id,
            CourseInstructor.instructor_id == inst_id,
        )
    ).scalar_one_or_none()
    if co_assigned is not None:
        return True

    batch_assigned = db.execute(
        select(Batch.id).where(
            Batch.course_id == course_id,
            Batch.instructor_id == inst_id,
        )
    ).scalar_one_or_none()
    return batch_assigned is not None


def assert_instructor_assigned_to_course(db: Session, user: User, course_id: int) -> None:
    """Allow admin or instructor assigned to the course; raise 403 otherwise."""
    role = get_user_role(user)
    if role == "admin":
        return
    if role == "instructor" and is_instructor_assigned_to_course(db, user, course_id):
        return
    raise AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code="FORBIDDEN",
        message="You are not authorized to manage this course.",
    )


def assert_instructor_assigned_to_batch(db: Session, user: User, batch: Batch) -> None:
    """Allow admin or the instructor assigned to this batch."""
    role = get_user_role(user)
    if role == "admin":
        return
    if (
        role == "instructor"
        and user.instructor_profile is not None
        and batch.instructor_id == user.instructor_profile.id
    ):
        return
    raise AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code="FORBIDDEN",
        message="You are not authorized to access or manage this batch.",
    )


def assert_student_enrolled_in_course(db: Session, student_id: int, course_id: int) -> Enrollment:
    """Verify student has an active or completed enrollment in course_id."""
    enrollment = db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            or_(Enrollment.status == "active", Enrollment.status == "completed"),
        )
    ).scalar_one_or_none()
    if enrollment is None:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="NOT_ENROLLED",
            message="You must be enrolled in this course to access its resources.",
        )
    return enrollment


def assert_can_access_course_content(db: Session, user: User, course_id: int) -> None:
    """Allow admin, assigned instructor, or enrolled student to read course content."""
    role = get_user_role(user)
    if role == "admin":
        return
    if role == "instructor":
        assert_instructor_assigned_to_course(db, user, course_id)
        return
    if role == "student":
        assert_student_enrolled_in_course(db, user.id, course_id)
        return
    raise AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code="FORBIDDEN",
        message="You do not have permission to access this course.",
    )
