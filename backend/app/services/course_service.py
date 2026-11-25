from typing import List, Optional

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Batch, Course, CourseInstructor, CourseModule, Enrollment
from app.models.operations import Payment
from app.models.user import Instructor, User
from app.schemas.course import (
    CourseCreateRequest,
    CourseDetailOut,
    CourseInstructorBrief,
    CourseModuleCreateRequest,
    CourseModuleOut,
    CourseModuleUpdateRequest,
    CourseOut,
    CourseUpdateRequest,
)
from app.services.authorization import (
    assert_can_access_course_content,
    assert_instructor_assigned_to_course,
    get_user_role,
)
from app.utils.pagination import apply_sorting, paginate_query


def _serialize_course(course: Course) -> CourseOut:
    return CourseOut.model_validate(course)


def _get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.execute(
        select(Course).where(Course.id == course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")
    return course


def _validate_instructor_exists(db: Session, instructor_id: int) -> Instructor:
    inst = db.execute(
        select(Instructor).join(User, User.id == Instructor.user_id).where(Instructor.id == instructor_id, User.is_active.is_(True))
    ).scalar_one_or_none()
    if inst is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="INSTRUCTOR_NOT_FOUND",
            message=f"Active instructor profile {instructor_id} not found.",
        )
    return inst


def list_courses(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    search: Optional[str],
    category: Optional[str],
    status_filter: Optional[str],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Course).where(Course.is_deleted.is_(False))

    if role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_id = current_user.instructor_profile.id
        co_ids = select(CourseInstructor.course_id).where(CourseInstructor.instructor_id == inst_id)
        batch_ids = select(Batch.course_id).where(Batch.instructor_id == inst_id)
        stmt = stmt.where(
            or_(
                Course.primary_instructor_id == inst_id,
                Course.id.in_(co_ids),
                Course.id.in_(batch_ids),
            )
        )
    elif role == "student":
        enrolled_ids = select(Enrollment.course_id).where(
            Enrollment.student_id == current_user.id,
            or_(Enrollment.status == "active", Enrollment.status == "completed"),
        )
        stmt = stmt.where(Course.id.in_(enrolled_ids))

    if category:
        stmt = stmt.where(Course.category == category)
    if status_filter:
        stmt = stmt.where(Course.status == status_filter)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Course.name.ilike(pattern),
                Course.course_code.ilike(pattern),
                Course.category.ilike(pattern),
            )
        )

    stmt = apply_sorting(
        stmt,
        Course,
        sort_by,
        sort_order,
        {"id": Course.id, "name": Course.name, "fee": Course.fee, "created_at": Course.created_at},
        Course.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=_serialize_course)


def create_course(db: Session, payload: CourseCreateRequest) -> CourseDetailOut:
    code = payload.course_code.strip().upper()
    dup = db.execute(select(Course.id).where(Course.course_code == code)).scalar_one_or_none()
    if dup is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="COURSE_CODE_EXISTS",
            message=f"Course code '{code}' already exists.",
        )

    if payload.primary_instructor_id is not None:
        _validate_instructor_exists(db, payload.primary_instructor_id)

    for iid in payload.instructor_ids:
        _validate_instructor_exists(db, iid)

    course = Course(
        course_code=code,
        name=payload.name.strip(),
        description=payload.description.strip(),
        category=payload.category.strip(),
        duration_hours=payload.duration_hours,
        fee=payload.fee,
        thumbnail_url=payload.thumbnail_url,
        status=payload.status,
        primary_instructor_id=payload.primary_instructor_id,
    )
    db.add(course)
    db.flush()

    unique_ids = set(payload.instructor_ids)
    if payload.primary_instructor_id is not None:
        unique_ids.add(payload.primary_instructor_id)
    for iid in unique_ids:
        db.add(CourseInstructor(course_id=course.id, instructor_id=iid))

    db.commit()
    return get_course_detail_internal(db, course.id)


def get_course_detail_internal(db: Session, course_id: int) -> CourseDetailOut:
    course = _get_course_or_404(db, course_id)
    modules = db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.sequence_order.asc(), CourseModule.id.asc())
    ).scalars().all()

    inst_rows = db.execute(
        select(Instructor, User.full_name)
        .join(CourseInstructor, CourseInstructor.instructor_id == Instructor.id)
        .join(User, User.id == Instructor.user_id)
        .where(CourseInstructor.course_id == course_id)
    ).all()

    assigned = [
        CourseInstructorBrief(
            instructor_id=inst.id,
            user_id=inst.user_id,
            full_name=full_name,
            employee_code=inst.employee_code,
        )
        for inst, full_name in inst_rows
    ]
    return CourseDetailOut(
        **CourseOut.model_validate(course).model_dump(),
        modules=[CourseModuleOut.model_validate(m) for m in modules],
        assigned_instructors=assigned,
    )


def get_course_detail(db: Session, course_id: int, current_user: User) -> CourseDetailOut:
    _get_course_or_404(db, course_id)
    assert_can_access_course_content(db, current_user, course_id)
    return get_course_detail_internal(db, course_id)


def update_course(db: Session, course_id: int, payload: CourseUpdateRequest, current_user: User) -> CourseDetailOut:
    course = _get_course_or_404(db, course_id)
    assert_instructor_assigned_to_course(db, current_user, course_id)
    role = get_user_role(current_user)

    if role != "admin" and (
        payload.fee is not None or payload.status is not None or payload.primary_instructor_id is not None
    ):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only administrators can change course fee, status, or primary instructor.",
        )

    if payload.name is not None:
        course.name = payload.name.strip()
    if payload.description is not None:
        course.description = payload.description.strip()
    if payload.category is not None:
        course.category = payload.category.strip()
    if payload.duration_hours is not None:
        course.duration_hours = payload.duration_hours
    if payload.thumbnail_url is not None:
        course.thumbnail_url = payload.thumbnail_url
    if payload.fee is not None:
        course.fee = payload.fee
    if payload.status is not None:
        course.status = payload.status
    if payload.primary_instructor_id is not None:
        _validate_instructor_exists(db, payload.primary_instructor_id)
        course.primary_instructor_id = payload.primary_instructor_id
        exists_ci = db.execute(
            select(CourseInstructor.id).where(
                CourseInstructor.course_id == course_id,
                CourseInstructor.instructor_id == payload.primary_instructor_id,
            )
        ).scalar_one_or_none()
        if exists_ci is None:
            db.add(CourseInstructor(course_id=course_id, instructor_id=payload.primary_instructor_id))

    db.commit()
    return get_course_detail_internal(db, course_id)


def set_course_status(db: Session, course_id: int, new_status: str) -> CourseDetailOut:
    course = _get_course_or_404(db, course_id)
    course.status = new_status
    db.commit()
    return get_course_detail_internal(db, course_id)


def delete_course(db: Session, course_id: int) -> None:
    course = _get_course_or_404(db, course_id)

    active_enrollment = db.execute(
        select(Enrollment.id).where(Enrollment.course_id == course_id)
    ).first()
    has_batch = db.execute(select(Batch.id).where(Batch.course_id == course_id)).first()
    has_payment = db.execute(select(Payment.id).where(Payment.course_id == course_id)).first()

    if active_enrollment is not None or has_batch is not None or has_payment is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="COURSE_HAS_DEPENDENCIES",
            message="Cannot delete course with existing enrollments, batches, or payment records. Archive it instead.",
        )

    course.is_deleted = True
    course.status = "archived"
    db.commit()


def assign_instructor(db: Session, course_id: int, instructor_id: int) -> CourseDetailOut:
    _get_course_or_404(db, course_id)
    _validate_instructor_exists(db, instructor_id)
    dup = db.execute(
        select(CourseInstructor.id).where(
            CourseInstructor.course_id == course_id,
            CourseInstructor.instructor_id == instructor_id,
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="INSTRUCTOR_ALREADY_ASSIGNED",
            message="Instructor is already assigned to this course.",
        )
    db.add(CourseInstructor(course_id=course_id, instructor_id=instructor_id))
    db.commit()
    return get_course_detail_internal(db, course_id)


def remove_instructor(db: Session, course_id: int, instructor_id: int) -> CourseDetailOut:
    course = _get_course_or_404(db, course_id)
    link = db.execute(
        select(CourseInstructor).where(
            CourseInstructor.course_id == course_id,
            CourseInstructor.instructor_id == instructor_id,
        )
    ).scalar_one_or_none()
    if link is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ASSIGNMENT_NOT_FOUND",
            message="Instructor is not assigned to this course.",
        )
    if course.primary_instructor_id == instructor_id:
        course.primary_instructor_id = None
    db.delete(link)
    db.commit()
    return get_course_detail_internal(db, course_id)


def list_modules(db: Session, course_id: int, current_user: User) -> List[CourseModuleOut]:
    _get_course_or_404(db, course_id)
    assert_can_access_course_content(db, current_user, course_id)
    modules = db.execute(
        select(CourseModule)
        .where(CourseModule.course_id == course_id)
        .order_by(CourseModule.sequence_order.asc(), CourseModule.id.asc())
    ).scalars().all()
    return [CourseModuleOut.model_validate(m) for m in modules]


def create_module(
    db: Session, course_id: int, payload: CourseModuleCreateRequest, current_user: User
) -> CourseModuleOut:
    _get_course_or_404(db, course_id)
    assert_instructor_assigned_to_course(db, current_user, course_id)
    mod = CourseModule(
        course_id=course_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        sequence_order=payload.sequence_order,
    )
    db.add(mod)
    db.commit()
    db.refresh(mod)
    return CourseModuleOut.model_validate(mod)


def update_module(
    db: Session,
    course_id: int,
    module_id: int,
    payload: CourseModuleUpdateRequest,
    current_user: User,
) -> CourseModuleOut:
    _get_course_or_404(db, course_id)
    assert_instructor_assigned_to_course(db, current_user, course_id)
    mod = db.execute(
        select(CourseModule).where(CourseModule.id == module_id, CourseModule.course_id == course_id)
    ).scalar_one_or_none()
    if mod is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="MODULE_NOT_FOUND", message="Course module not found.")
    if payload.title is not None:
        mod.title = payload.title.strip()
    if payload.description is not None:
        mod.description = payload.description.strip() or None
    if payload.sequence_order is not None:
        mod.sequence_order = payload.sequence_order
    db.commit()
    db.refresh(mod)
    return CourseModuleOut.model_validate(mod)


def delete_module(db: Session, course_id: int, module_id: int, current_user: User) -> None:
    _get_course_or_404(db, course_id)
    assert_instructor_assigned_to_course(db, current_user, course_id)
    mod = db.execute(
        select(CourseModule).where(CourseModule.id == module_id, CourseModule.course_id == course_id)
    ).scalar_one_or_none()
    if mod is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="MODULE_NOT_FOUND", message="Course module not found.")
    db.delete(mod)
    db.commit()
