from typing import Optional

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.exceptions import AppException
from app.models.course import Batch, BatchStudent, Course, CourseInstructor, Enrollment
from app.models.operations import Attendance
from app.models.user import Instructor, Role, Student, User
from app.schemas.auth import UserCreateRequest
from app.schemas.profiles import (
    InstructorCreateRequest,
    InstructorDetailOut,
    InstructorOut,
    InstructorUpdateRequest,
    StudentCreateRequest,
    StudentDetailOut,
    StudentOut,
    StudentUpdateRequest,
)
from app.services import auth_service
from app.services.authorization import get_user_role
from app.utils.pagination import apply_sorting, paginate_query


def _serialize_student(user: User) -> StudentOut:
    sp = user.student_profile
    return StudentOut(
        user_id=user.id,
        student_profile_id=sp.id if sp else 0,
        student_code=sp.student_code if sp else "",
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        date_of_birth=sp.date_of_birth if sp else None,
        address=sp.address if sp else None,
        guardian_name=sp.guardian_name if sp else None,
        guardian_phone=sp.guardian_phone if sp else None,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _serialize_instructor(user: User) -> InstructorOut:
    ip = user.instructor_profile
    return InstructorOut(
        user_id=user.id,
        instructor_profile_id=ip.id if ip else 0,
        employee_code=ip.employee_code if ip else "",
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        expertise=ip.expertise if ip else None,
        qualification=ip.qualification if ip else None,
        bio=ip.bio if ip else None,
        experience_years=ip.experience_years if ip else 0,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _instructor_course_ids(db: Session, inst_profile_id: int) -> list[int]:
    c1 = db.execute(select(Course.id).where(Course.primary_instructor_id == inst_profile_id)).scalars().all()
    c2 = db.execute(select(CourseInstructor.course_id).where(CourseInstructor.instructor_id == inst_profile_id)).scalars().all()
    c3 = db.execute(select(Batch.course_id).where(Batch.instructor_id == inst_profile_id)).scalars().all()
    return list({*c1, *c2, *c3})


def list_students(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    search: Optional[str],
    is_active: Optional[bool],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    stmt = (
        select(User)
        .join(Role, User.role_id == Role.id)
        .join(Student, Student.user_id == User.id)
        .options(joinedload(User.student_profile), joinedload(User.role))
        .where(Role.name == "student")
    )

    if get_user_role(current_user) == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        course_ids = _instructor_course_ids(db, current_user.instructor_profile.id)
        if not course_ids:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        enrolled_student_ids = (
            select(Enrollment.student_id)
            .where(Enrollment.course_id.in_(course_ids))
            .distinct()
        )
        stmt = stmt.where(User.id.in_(enrolled_student_ids))

    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                Student.student_code.ilike(pattern),
            )
        )

    stmt = apply_sorting(
        stmt,
        User,
        sort_by,
        sort_order,
        {"id": User.id, "full_name": User.full_name, "email": User.email, "created_at": User.created_at},
        User.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=_serialize_student)


def create_student(db: Session, payload: StudentCreateRequest) -> StudentOut:
    user = auth_service.create_user_account(
        db,
        UserCreateRequest(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role="student",
            phone=payload.phone,
            is_active=payload.is_active,
            student_code=payload.student_code,
            date_of_birth=payload.date_of_birth,
            address=payload.address,
            guardian_name=payload.guardian_name,
            guardian_phone=payload.guardian_phone,
        ),
    )
    user = auth_service.get_user_by_id(db, user.id)
    return _serialize_student(user)


def get_student_detail(db: Session, student_user_id: int, current_user: User) -> StudentDetailOut:
    role = get_user_role(current_user)
    if role == "student" and current_user.id != student_user_id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="You can only view your own student profile.",
        )

    user = db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.student_profile), joinedload(User.role))
        .where(User.id == student_user_id, Role.name == "student")
    ).scalar_one_or_none()
    if user is None or user.student_profile is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="STUDENT_NOT_FOUND", message="Student not found.")

    if role == "instructor":
        if not current_user.instructor_profile:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")
        course_ids = _instructor_course_ids(db, current_user.instructor_profile.id)
        shared = db.execute(
            select(Enrollment.id).where(
                Enrollment.student_id == student_user_id,
                Enrollment.course_id.in_(course_ids or [-1]),
            )
        ).first()
        if shared is None:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You can only view students enrolled in your assigned courses.",
            )

    enrollments_rows = db.execute(
        select(Enrollment, Course.name, Course.course_code)
        .join(Course, Course.id == Enrollment.course_id)
        .where(Enrollment.student_id == student_user_id)
    ).all()
    enrollments = [
        {
            "enrollment_id": e.id,
            "course_id": e.course_id,
            "course_code": c_code,
            "course_name": c_name,
            "status": e.status,
            "enrolled_at": e.enrolled_at,
            "completed_at": e.completed_at,
        }
        for e, c_name, c_code in enrollments_rows
    ]

    batch_rows = db.execute(
        select(BatchStudent, Batch.name, Batch.batch_code)
        .join(Batch, Batch.id == BatchStudent.batch_id)
        .where(BatchStudent.student_id == student_user_id)
    ).all()
    batches = [
        {
            "batch_id": bs.batch_id,
            "batch_code": b_code,
            "batch_name": b_name,
            "status": bs.status,
            "joined_at": bs.joined_at,
        }
        for bs, b_name, b_code in batch_rows
    ]

    att_records = db.execute(select(Attendance.status).where(Attendance.student_id == student_user_id)).scalars().all()
    present_cnt = sum(1 for s in att_records if s == "present")
    absent_cnt = sum(1 for s in att_records if s == "absent")
    eligible = present_cnt + absent_cnt
    att_pct = round((present_cnt / eligible) * 100, 2) if eligible > 0 else 0.0

    base = _serialize_student(user)
    return StudentDetailOut(
        **base.model_dump(),
        enrollments=enrollments,
        batches=batches,
        attendance_percentage=att_pct,
    )


def update_student(
    db: Session, student_user_id: int, payload: StudentUpdateRequest, current_user: User
) -> StudentOut:
    role = get_user_role(current_user)
    if role == "student" and current_user.id != student_user_id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")
    if role == "instructor":
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")

    user = db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.student_profile), joinedload(User.role))
        .where(User.id == student_user_id, Role.name == "student")
    ).scalar_one_or_none()
    if user is None or user.student_profile is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="STUDENT_NOT_FOUND", message="Student not found.")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.is_active is not None:
        if role != "admin":
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Only admins can change account status.")
        user.is_active = payload.is_active

    sp = user.student_profile
    if payload.date_of_birth is not None:
        sp.date_of_birth = payload.date_of_birth
    if payload.address is not None:
        sp.address = payload.address.strip() or None
    if payload.guardian_name is not None:
        sp.guardian_name = payload.guardian_name.strip() or None
    if payload.guardian_phone is not None:
        sp.guardian_phone = payload.guardian_phone.strip() or None

    db.commit()
    db.refresh(user)
    return _serialize_student(user)


def deactivate_student(db: Session, student_user_id: int, admin_id: int) -> StudentOut:
    user = db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.student_profile), joinedload(User.role))
        .where(User.id == student_user_id, Role.name == "student")
    ).scalar_one_or_none()
    if user is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="STUDENT_NOT_FOUND", message="Student not found.")
    updated = auth_service.deactivate_user(db, student_user_id, admin_id)
    return _serialize_student(updated)


def list_instructors(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str],
    is_active: Optional[bool],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    stmt = (
        select(User)
        .join(Role, User.role_id == Role.id)
        .join(Instructor, Instructor.user_id == User.id)
        .options(joinedload(User.instructor_profile), joinedload(User.role))
        .where(Role.name == "instructor")
    )
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
                Instructor.employee_code.ilike(pattern),
                Instructor.expertise.ilike(pattern),
            )
        )
    stmt = apply_sorting(
        stmt,
        User,
        sort_by,
        sort_order,
        {"id": User.id, "full_name": User.full_name, "email": User.email, "created_at": User.created_at},
        User.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=_serialize_instructor)


def create_instructor(db: Session, payload: InstructorCreateRequest) -> InstructorOut:
    user = auth_service.create_user_account(
        db,
        UserCreateRequest(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role="instructor",
            phone=payload.phone,
            is_active=payload.is_active,
            employee_code=payload.employee_code,
            expertise=payload.expertise,
            qualification=payload.qualification,
            bio=payload.bio,
            experience_years=payload.experience_years,
        ),
    )
    user = auth_service.get_user_by_id(db, user.id)
    return _serialize_instructor(user)


def get_instructor_detail(db: Session, instructor_user_id: int) -> InstructorDetailOut:
    user = db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.instructor_profile), joinedload(User.role))
        .where(User.id == instructor_user_id, Role.name == "instructor")
    ).scalar_one_or_none()
    if user is None or user.instructor_profile is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code="INSTRUCTOR_NOT_FOUND", message="Instructor not found."
        )

    ip = user.instructor_profile
    course_ids = _instructor_course_ids(db, ip.id)
    courses_rows = (
        db.execute(
            select(Course).where(Course.id.in_(course_ids), Course.is_deleted.is_(False))
        ).scalars().all()
        if course_ids
        else []
    )
    batches_rows = db.execute(select(Batch).where(Batch.instructor_id == ip.id)).scalars().all()

    base = _serialize_instructor(user)
    return InstructorDetailOut(
        **base.model_dump(),
        assigned_courses=[
            {"id": c.id, "course_code": c.course_code, "name": c.name, "status": c.status}
            for c in courses_rows
        ],
        assigned_batches=[
            {"id": b.id, "batch_code": b.batch_code, "name": b.name, "status": b.status}
            for b in batches_rows
        ],
    )


def update_instructor(
    db: Session, instructor_user_id: int, payload: InstructorUpdateRequest, current_user: User
) -> InstructorOut:
    role = get_user_role(current_user)
    if role == "instructor" and current_user.id != instructor_user_id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")
    if role == "student":
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")

    user = db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.instructor_profile), joinedload(User.role))
        .where(User.id == instructor_user_id, Role.name == "instructor")
    ).scalar_one_or_none()
    if user is None or user.instructor_profile is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code="INSTRUCTOR_NOT_FOUND", message="Instructor not found."
        )

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.is_active is not None:
        if role != "admin":
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Only admins can change account status.")
        user.is_active = payload.is_active

    ip = user.instructor_profile
    if payload.expertise is not None:
        ip.expertise = payload.expertise.strip() or None
    if payload.qualification is not None:
        ip.qualification = payload.qualification.strip() or None
    if payload.bio is not None:
        ip.bio = payload.bio.strip() or None
    if payload.experience_years is not None:
        ip.experience_years = payload.experience_years

    db.commit()
    db.refresh(user)
    return _serialize_instructor(user)


def deactivate_instructor(db: Session, instructor_user_id: int, admin_id: int) -> InstructorOut:
    user = db.execute(
        select(User)
        .join(Role, User.role_id == Role.id)
        .options(joinedload(User.instructor_profile), joinedload(User.role))
        .where(User.id == instructor_user_id, Role.name == "instructor")
    ).scalar_one_or_none()
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND, code="INSTRUCTOR_NOT_FOUND", message="Instructor not found."
        )
    updated = auth_service.deactivate_user(db, instructor_user_id, admin_id)
    return _serialize_instructor(updated)
