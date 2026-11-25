from typing import Optional

from fastapi import status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Batch, BatchStudent, Course, Enrollment
from app.models.mixins import utcnow
from app.models.user import Instructor, Role, Student, User
from app.schemas.batch import (
    BatchCreateRequest,
    BatchDetailOut,
    BatchOut,
    BatchRosterItem,
    BatchUpdateRequest,
    EnrollmentCreateRequest,
    EnrollmentOut,
    EnrollmentUpdateRequest,
)
from app.services.authorization import assert_instructor_assigned_to_batch, get_user_role
from app.utils.pagination import apply_sorting, paginate_query


def _get_batch_or_404(db: Session, batch_id: int) -> Batch:
    batch = db.execute(select(Batch).where(Batch.id == batch_id)).scalar_one_or_none()
    if batch is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="BATCH_NOT_FOUND", message="Batch not found.")
    return batch


def _serialize_batch(db: Session, batch: Batch) -> BatchOut:
    course_name = db.execute(select(Course.name).where(Course.id == batch.course_id)).scalar_one_or_none()
    inst_name = db.execute(
        select(User.full_name)
        .join(Instructor, Instructor.user_id == User.id)
        .where(Instructor.id == batch.instructor_id)
    ).scalar_one_or_none()
    enrolled_count = db.execute(
        select(func.count(BatchStudent.id)).where(
            BatchStudent.batch_id == batch.id,
            BatchStudent.status == "active",
        )
    ).scalar_one()
    return BatchOut(
        id=batch.id,
        batch_code=batch.batch_code,
        name=batch.name,
        course_id=batch.course_id,
        course_name=course_name,
        instructor_id=batch.instructor_id,
        instructor_name=inst_name,
        start_date=batch.start_date,
        end_date=batch.end_date,
        class_days=batch.class_days,
        class_timing=batch.class_timing,
        capacity=batch.capacity,
        enrolled_count=enrolled_count,
        status=batch.status,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


def list_batches(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    search: Optional[str],
    course_id: Optional[int],
    status_filter: Optional[str],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Batch)

    if role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        stmt = stmt.where(Batch.instructor_id == current_user.instructor_profile.id)
    elif role == "student":
        my_batch_ids = select(BatchStudent.batch_id).where(
            BatchStudent.student_id == current_user.id,
            BatchStudent.status != "removed",
        )
        stmt = stmt.where(Batch.id.in_(my_batch_ids))

    if course_id is not None:
        stmt = stmt.where(Batch.course_id == course_id)
    if status_filter:
        stmt = stmt.where(Batch.status == status_filter)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Batch.name.ilike(pattern), Batch.batch_code.ilike(pattern)))

    stmt = apply_sorting(
        stmt,
        Batch,
        sort_by,
        sort_order,
        {"id": Batch.id, "name": Batch.name, "start_date": Batch.start_date, "created_at": Batch.created_at},
        Batch.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda b: _serialize_batch(db, b))


def create_batch(db: Session, payload: BatchCreateRequest) -> BatchDetailOut:
    code = payload.batch_code.strip().upper()
    dup = db.execute(select(Batch.id).where(Batch.batch_code == code)).scalar_one_or_none()
    if dup is not None:
        raise AppException(status_code=status.HTTP_409_CONFLICT, code="BATCH_CODE_EXISTS", message="Batch code already exists.")

    course = db.execute(
        select(Course).where(Course.id == payload.course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")

    inst = db.execute(
        select(Instructor)
        .join(User, User.id == Instructor.user_id)
        .where(Instructor.id == payload.instructor_id, User.is_active.is_(True))
    ).scalar_one_or_none()
    if inst is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="INSTRUCTOR_NOT_FOUND", message="Active instructor not found.")

    batch = Batch(
        batch_code=code,
        name=payload.name.strip(),
        course_id=payload.course_id,
        instructor_id=payload.instructor_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        class_days=payload.class_days.strip(),
        class_timing=payload.class_timing.strip(),
        capacity=payload.capacity,
        status=payload.status,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return get_batch_detail_internal(db, batch)


def get_batch_detail_internal(db: Session, batch: Batch) -> BatchDetailOut:
    roster_rows = db.execute(
        select(BatchStudent, User.full_name, User.email, Student.student_code)
        .join(User, User.id == BatchStudent.student_id)
        .join(Student, Student.user_id == User.id)
        .where(BatchStudent.batch_id == batch.id, BatchStudent.status != "removed")
        .order_by(User.full_name.asc())
    ).all()
    roster = [
        BatchRosterItem(
            student_id=bs.student_id,
            full_name=full_name,
            email=email,
            student_code=student_code,
            status=bs.status,
            joined_at=bs.joined_at,
        )
        for bs, full_name, email, student_code in roster_rows
    ]
    base = _serialize_batch(db, batch)
    return BatchDetailOut(**base.model_dump(), roster=roster)


def get_batch_detail(db: Session, batch_id: int, current_user: User) -> BatchDetailOut:
    batch = _get_batch_or_404(db, batch_id)
    role = get_user_role(current_user)
    if role == "instructor":
        assert_instructor_assigned_to_batch(db, current_user, batch)
    elif role == "student":
        member = db.execute(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == batch_id,
                BatchStudent.student_id == current_user.id,
                BatchStudent.status != "removed",
            )
        ).scalar_one_or_none()
        if member is None:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You are not enrolled in this batch.",
            )
    return get_batch_detail_internal(db, batch)


def update_batch(
    db: Session, batch_id: int, payload: BatchUpdateRequest, current_user: User
) -> BatchDetailOut:
    batch = _get_batch_or_404(db, batch_id)
    assert_instructor_assigned_to_batch(db, current_user, batch)
    role = get_user_role(current_user)

    if role != "admin" and (
        payload.instructor_id is not None or payload.capacity is not None or payload.status is not None
    ):
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only administrators can modify batch instructor, capacity, or status.",
        )

    new_start = payload.start_date if payload.start_date is not None else batch.start_date
    new_end = payload.end_date if payload.end_date is not None else batch.end_date
    if new_end < new_start:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_DATE_RANGE",
            message="end_date must be greater than or equal to start_date.",
        )

    if payload.capacity is not None:
        active_count = db.execute(
            select(func.count(BatchStudent.id)).where(
                BatchStudent.batch_id == batch.id,
                BatchStudent.status == "active",
            )
        ).scalar_one()
        if payload.capacity < active_count:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="CAPACITY_BELOW_ENROLLED",
                message=f"Capacity cannot be less than currently enrolled students ({active_count}).",
            )
        batch.capacity = payload.capacity

    if payload.instructor_id is not None:
        inst = db.execute(
            select(Instructor)
            .join(User, User.id == Instructor.user_id)
            .where(Instructor.id == payload.instructor_id, User.is_active.is_(True))
        ).scalar_one_or_none()
        if inst is None:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="INSTRUCTOR_NOT_FOUND", message="Active instructor not found.")
        batch.instructor_id = payload.instructor_id

    if payload.name is not None:
        batch.name = payload.name.strip()
    if payload.start_date is not None:
        batch.start_date = payload.start_date
    if payload.end_date is not None:
        batch.end_date = payload.end_date
    if payload.class_days is not None:
        batch.class_days = payload.class_days.strip()
    if payload.class_timing is not None:
        batch.class_timing = payload.class_timing.strip()
    if payload.status is not None:
        batch.status = payload.status

    db.commit()
    db.refresh(batch)
    return get_batch_detail_internal(db, batch)


def set_batch_status(db: Session, batch_id: int, new_status: str) -> BatchDetailOut:
    batch = _get_batch_or_404(db, batch_id)
    batch.status = new_status
    db.commit()
    db.refresh(batch)
    return get_batch_detail_internal(db, batch)


def add_student_to_batch(db: Session, batch_id: int, student_user_id: int) -> BatchDetailOut:
    batch = _get_batch_or_404(db, batch_id)
    if batch.status in {"closed", "archived"}:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="BATCH_NOT_OPEN",
            message=f"Cannot add students to a {batch.status} batch.",
        )

    student_user = db.execute(
        select(User)
        .join(Role, Role.id == User.role_id)
        .where(User.id == student_user_id, Role.name == "student", User.is_active.is_(True))
    ).scalar_one_or_none()
    if student_user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="STUDENT_NOT_FOUND",
            message="Active student not found.",
        )

    active_count = db.execute(
        select(func.count(BatchStudent.id)).where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.status == "active",
        )
    ).scalar_one()
    if active_count >= batch.capacity:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="BATCH_CAPACITY_FULL",
            message=f"Batch capacity ({batch.capacity}) has been reached.",
        )

    existing_member = db.execute(
        select(BatchStudent).where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.student_id == student_user_id,
        )
    ).scalar_one_or_none()
    if existing_member is not None and existing_member.status == "active":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ALREADY_IN_BATCH",
            message="Student is already active in this batch.",
        )

    # Ensure course enrollment exists inside the same transaction
    enrollment = db.execute(
        select(Enrollment).where(
            Enrollment.student_id == student_user_id,
            Enrollment.course_id == batch.course_id,
        )
    ).scalar_one_or_none()

    if enrollment is None:
        course = db.execute(
            select(Course).where(Course.id == batch.course_id, Course.is_deleted.is_(False))
        ).scalar_one_or_none()
        if course is None or course.status != "published":
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="COURSE_NOT_PUBLISHED",
                message="Cannot enroll student because the linked course is not published.",
            )
        enrollment = Enrollment(
            student_id=student_user_id,
            course_id=batch.course_id,
            status="active",
        )
        db.add(enrollment)
        db.flush()
    elif enrollment.status == "dropped":
        enrollment.status = "active"

    if existing_member is not None:
        existing_member.status = "active"
        existing_member.enrollment_id = enrollment.id
        existing_member.joined_at = utcnow()
    else:
        db.add(
            BatchStudent(
                batch_id=batch_id,
                student_id=student_user_id,
                enrollment_id=enrollment.id,
                status="active",
            )
        )

    db.commit()
    return get_batch_detail_internal(db, batch)


def remove_student_from_batch(db: Session, batch_id: int, student_user_id: int) -> BatchDetailOut:
    batch = _get_batch_or_404(db, batch_id)
    member = db.execute(
        select(BatchStudent).where(
            BatchStudent.batch_id == batch_id,
            BatchStudent.student_id == student_user_id,
            BatchStudent.status != "removed",
        )
    ).scalar_one_or_none()
    if member is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="BATCH_STUDENT_NOT_FOUND",
            message="Student is not enrolled in this batch.",
        )
    member.status = "removed"
    db.commit()
    return get_batch_detail_internal(db, batch)


def _serialize_enrollment(db: Session, enrollment: Enrollment) -> EnrollmentOut:
    student_name = db.execute(select(User.full_name).where(User.id == enrollment.student_id)).scalar_one_or_none()
    course_name = db.execute(select(Course.name).where(Course.id == enrollment.course_id)).scalar_one_or_none()
    return EnrollmentOut(
        id=enrollment.id,
        student_id=enrollment.student_id,
        student_name=student_name,
        course_id=enrollment.course_id,
        course_name=course_name,
        status=enrollment.status,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
        created_at=enrollment.created_at,
    )


def list_enrollments(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    course_id: Optional[int],
    student_id: Optional[int],
    status_filter: Optional[str],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Enrollment)

    if role == "student":
        stmt = stmt.where(Enrollment.student_id == current_user.id)
    elif role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_id = current_user.instructor_profile.id
        course_ids = select(Course.id).where(Course.primary_instructor_id == inst_id)
        batch_course_ids = select(Batch.course_id).where(Batch.instructor_id == inst_id)
        stmt = stmt.where(or_(Enrollment.course_id.in_(course_ids), Enrollment.course_id.in_(batch_course_ids)))

    if course_id is not None:
        stmt = stmt.where(Enrollment.course_id == course_id)
    if student_id is not None and role != "student":
        stmt = stmt.where(Enrollment.student_id == student_id)
    if status_filter:
        stmt = stmt.where(Enrollment.status == status_filter)

    stmt = apply_sorting(
        stmt,
        Enrollment,
        sort_by,
        sort_order,
        {"id": Enrollment.id, "enrolled_at": Enrollment.enrolled_at, "status": Enrollment.status},
        Enrollment.enrolled_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda e: _serialize_enrollment(db, e))


def create_enrollment(db: Session, payload: EnrollmentCreateRequest) -> EnrollmentOut:
    student_user = db.execute(
        select(User)
        .join(Role, Role.id == User.role_id)
        .where(User.id == payload.student_id, Role.name == "student", User.is_active.is_(True))
    ).scalar_one_or_none()
    if student_user is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="STUDENT_NOT_FOUND", message="Active student not found.")

    course = db.execute(
        select(Course).where(Course.id == payload.course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")
    if course.status != "published":
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="COURSE_NOT_PUBLISHED",
            message="Students can only be enrolled in published courses.",
        )

    dup = db.execute(
        select(Enrollment.id).where(
            Enrollment.student_id == payload.student_id,
            Enrollment.course_id == payload.course_id,
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_ENROLLMENT",
            message="Student is already enrolled in this course.",
        )

    enrollment = Enrollment(
        student_id=payload.student_id,
        course_id=payload.course_id,
        status="active",
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return _serialize_enrollment(db, enrollment)


def update_enrollment(db: Session, enrollment_id: int, payload: EnrollmentUpdateRequest) -> EnrollmentOut:
    enrollment = db.execute(select(Enrollment).where(Enrollment.id == enrollment_id)).scalar_one_or_none()
    if enrollment is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ENROLLMENT_NOT_FOUND", message="Enrollment not found.")
    enrollment.status = payload.status
    if payload.status == "completed" and enrollment.completed_at is None:
        enrollment.completed_at = utcnow()
    db.commit()
    db.refresh(enrollment)
    return _serialize_enrollment(db, enrollment)
