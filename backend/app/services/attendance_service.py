from collections import defaultdict
from datetime import date
from typing import List, Optional

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Batch, BatchStudent
from app.models.operations import Attendance, AttendanceAuditLog
from app.models.user import User
from app.schemas.attendance import (
    AttendanceAuditOut,
    AttendanceBulkMarkRequest,
    AttendanceOut,
    AttendanceSummaryOut,
    AttendanceUpdateRequest,
    MonthlyAttendanceSummary,
)
from app.services.authorization import assert_instructor_assigned_to_batch, get_user_role
from app.utils.pagination import apply_sorting, paginate_query


def _serialize_attendance(db: Session, rec: Attendance) -> AttendanceOut:
    student_name = db.execute(select(User.full_name).where(User.id == rec.student_id)).scalar_one_or_none()
    return AttendanceOut(
        id=rec.id,
        batch_id=rec.batch_id,
        student_id=rec.student_id,
        student_name=student_name,
        session_date=rec.session_date,
        status=rec.status,
        remarks=rec.remarks,
        marked_by=rec.marked_by,
        updated_by=rec.updated_by,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )


def mark_attendance(
    db: Session, payload: AttendanceBulkMarkRequest, current_user: User
) -> List[AttendanceOut]:
    batch = db.execute(select(Batch).where(Batch.id == payload.batch_id)).scalar_one_or_none()
    if batch is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="BATCH_NOT_FOUND", message="Batch not found.")

    assert_instructor_assigned_to_batch(db, current_user, batch)

    active_roster_ids = set(
        db.execute(
            select(BatchStudent.student_id).where(
                BatchStudent.batch_id == payload.batch_id,
                BatchStudent.status != "removed",
            )
        ).scalars().all()
    )

    seen_students = set()
    created_records: List[Attendance] = []
    for entry in payload.records:
        if entry.student_id in seen_students:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DUPLICATE_STUDENT_IN_REQUEST",
                message=f"Duplicate student_id {entry.student_id} in attendance payload.",
            )
        seen_students.add(entry.student_id)

        if entry.student_id not in active_roster_ids:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="STUDENT_NOT_IN_BATCH",
                message=f"Student {entry.student_id} is not in batch {payload.batch_id}.",
            )

        existing = db.execute(
            select(Attendance.id).where(
                Attendance.batch_id == payload.batch_id,
                Attendance.student_id == entry.student_id,
                Attendance.session_date == payload.session_date,
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DUPLICATE_ATTENDANCE",
                message=f"Attendance already recorded for student {entry.student_id} on {payload.session_date}.",
            )

        rec = Attendance(
            batch_id=payload.batch_id,
            student_id=entry.student_id,
            session_date=payload.session_date,
            status=entry.status,
            remarks=entry.remarks.strip() if entry.remarks else None,
            marked_by=current_user.id,
            updated_by=current_user.id,
        )
        db.add(rec)
        created_records.append(rec)

    db.commit()
    for r in created_records:
        db.refresh(r)
    return [_serialize_attendance(db, r) for r in created_records]


def update_attendance(
    db: Session, attendance_id: int, payload: AttendanceUpdateRequest, current_user: User
) -> AttendanceOut:
    rec = db.execute(select(Attendance).where(Attendance.id == attendance_id)).scalar_one_or_none()
    if rec is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ATTENDANCE_NOT_FOUND", message="Attendance record not found.")

    batch = db.execute(select(Batch).where(Batch.id == rec.batch_id)).scalar_one()
    assert_instructor_assigned_to_batch(db, current_user, batch)

    old_status = rec.status
    rec.status = payload.status
    if payload.remarks is not None:
        rec.remarks = payload.remarks.strip() or None
    rec.updated_by = current_user.id

    db.add(
        AttendanceAuditLog(
            attendance_id=rec.id,
            old_status=old_status,
            new_status=payload.status,
            changed_by=current_user.id,
            reason=payload.reason.strip(),
        )
    )
    db.commit()
    db.refresh(rec)
    return _serialize_attendance(db, rec)


def list_attendance(
    db: Session,
    current_user: User,
    batch_id: Optional[int],
    student_id: Optional[int],
    date_from: Optional[date],
    date_to: Optional[date],
    status_filter: Optional[str],
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Attendance)

    if role == "student":
        stmt = stmt.where(Attendance.student_id == current_user.id)
    elif role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        my_batch_ids = select(Batch.id).where(Batch.instructor_id == current_user.instructor_profile.id)
        stmt = stmt.where(Attendance.batch_id.in_(my_batch_ids))

    if batch_id is not None:
        stmt = stmt.where(Attendance.batch_id == batch_id)
    if student_id is not None and role != "student":
        stmt = stmt.where(Attendance.student_id == student_id)
    if date_from is not None:
        stmt = stmt.where(Attendance.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Attendance.session_date <= date_to)
    if status_filter:
        stmt = stmt.where(Attendance.status == status_filter)

    stmt = apply_sorting(
        stmt,
        Attendance,
        sort_by,
        sort_order,
        {"id": Attendance.id, "session_date": Attendance.session_date, "status": Attendance.status},
        Attendance.session_date,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda r: _serialize_attendance(db, r))


def get_attendance_audit(db: Session, attendance_id: int, current_user: User) -> List[AttendanceAuditOut]:
    rec = db.execute(select(Attendance).where(Attendance.id == attendance_id)).scalar_one_or_none()
    if rec is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ATTENDANCE_NOT_FOUND", message="Attendance record not found.")
    batch = db.execute(select(Batch).where(Batch.id == rec.batch_id)).scalar_one()
    assert_instructor_assigned_to_batch(db, current_user, batch)

    logs = db.execute(
        select(AttendanceAuditLog)
        .where(AttendanceAuditLog.attendance_id == attendance_id)
        .order_by(AttendanceAuditLog.changed_at.desc())
    ).scalars().all()
    return [AttendanceAuditOut.model_validate(l) for l in logs]


def get_attendance_summary(
    db: Session,
    current_user: User,
    student_id: Optional[int],
    batch_id: Optional[int],
) -> AttendanceSummaryOut:
    role = get_user_role(current_user)
    target_student_id = current_user.id if role == "student" else student_id
    if target_student_id is None:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="STUDENT_ID_REQUIRED",
            message="student_id query parameter is required.",
        )
    if role == "student" and student_id is not None and student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You can only view your own attendance summary.")

    stmt = select(Attendance).where(Attendance.student_id == target_student_id)
    if role == "instructor":
        if not current_user.instructor_profile:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")
        my_batch_ids = select(Batch.id).where(Batch.instructor_id == current_user.instructor_profile.id)
        stmt = stmt.where(Attendance.batch_id.in_(my_batch_ids))
    if batch_id is not None:
        stmt = stmt.where(Attendance.batch_id == batch_id)

    rows = db.execute(stmt).scalars().all()

    counts = defaultdict(int)
    monthly = defaultdict(lambda: defaultdict(int))
    for r in rows:
        counts[r.status] += 1
        month_key = r.session_date.strftime("%Y-%m")
        monthly[month_key][r.status] += 1

    eligible = counts["present"] + counts["absent"]
    pct = round((counts["present"] / eligible) * 100, 2) if eligible > 0 else 0.0

    monthly_list = []
    for m_key in sorted(monthly.keys()):
        mc = monthly[m_key]
        m_elig = mc["present"] + mc["absent"]
        m_pct = round((mc["present"] / m_elig) * 100, 2) if m_elig > 0 else 0.0
        monthly_list.append(
            MonthlyAttendanceSummary(
                month=m_key,
                present=mc["present"],
                absent=mc["absent"],
                cancelled=mc["cancelled"],
                holiday=mc["holiday"],
                approved_leave=mc["approved_leave"],
                eligible_classes=m_elig,
                attendance_percentage=m_pct,
            )
        )

    return AttendanceSummaryOut(
        student_id=target_student_id,
        batch_id=batch_id,
        present=counts["present"],
        absent=counts["absent"],
        cancelled=counts["cancelled"],
        holiday=counts["holiday"],
        approved_leave=counts["approved_leave"],
        eligible_classes=eligible,
        attendance_percentage=pct,
        monthly_breakdown=monthly_list,
    )
