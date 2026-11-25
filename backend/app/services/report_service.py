"""Report service – tabular data extraction for CSV/XLSX/PDF export."""

from decimal import Decimal
from typing import List, Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import Assignment, Submission
from app.models.course import Batch, BatchStudent, Course, Enrollment
from app.models.operations import Attendance, Payment
from app.models.user import Role, User

Headers = List[str]
Rows = List[Sequence]


def _students_report(db: Session) -> Tuple[Headers, Rows]:
    """All active students with code, email, phone."""
    student_role = db.execute(select(Role).where(Role.name == "student")).scalar_one_or_none()
    if student_role is None:
        return ["No Data"], []

    from app.models.user import Student

    users = db.execute(
        select(User, Student)
        .outerjoin(Student, Student.user_id == User.id)
        .where(User.role_id == student_role.id, User.is_active.is_(True))
        .order_by(User.full_name)
    ).all()

    headers = ["Student Code", "Full Name", "Email", "Phone", "DOB", "Guardian"]
    rows = []
    for u, s in users:
        rows.append([
            s.student_code if s else "",
            u.full_name,
            u.email,
            u.phone or "",
            str(s.date_of_birth) if s and s.date_of_birth else "",
            s.guardian_name if s else "",
        ])
    return headers, rows


def _enrollments_report(db: Session, course_id: Optional[int] = None) -> Tuple[Headers, Rows]:
    """Enrollment listing optionally filtered by course."""
    stmt = (
        select(Enrollment, User.full_name, Course.name)
        .join(User, User.id == Enrollment.student_id)
        .join(Course, Course.id == Enrollment.course_id)
    )
    if course_id:
        stmt = stmt.where(Enrollment.course_id == course_id)
    stmt = stmt.order_by(Enrollment.enrolled_at.desc())

    rows_raw = db.execute(stmt).all()
    headers = ["Enrollment ID", "Student", "Course", "Status", "Enrolled At", "Completed At"]
    rows = []
    for enr, student_name, course_name in rows_raw:
        rows.append([
            enr.id,
            student_name,
            course_name,
            enr.status,
            enr.enrolled_at.strftime("%Y-%m-%d") if enr.enrolled_at else "",
            enr.completed_at.strftime("%Y-%m-%d") if enr.completed_at else "",
        ])
    return headers, rows


def _payments_report(db: Session, course_id: Optional[int] = None) -> Tuple[Headers, Rows]:
    """Payment / revenue report."""
    stmt = (
        select(Payment, User.full_name, Course.name)
        .join(User, User.id == Payment.student_id)
        .join(Course, Course.id == Payment.course_id)
    )
    if course_id:
        stmt = stmt.where(Payment.course_id == course_id)
    stmt = stmt.order_by(Payment.payment_date.desc())

    rows_raw = db.execute(stmt).all()
    headers = ["Receipt #", "Student", "Course", "Total Fee", "Amount Paid", "Method", "Status", "Date"]
    rows = []
    for pay, student_name, course_name in rows_raw:
        rows.append([
            pay.receipt_number,
            student_name,
            course_name,
            str(pay.total_fee),
            str(pay.amount_paid),
            pay.payment_method,
            pay.status,
            pay.payment_date.strftime("%Y-%m-%d %H:%M") if pay.payment_date else "",
        ])
    return headers, rows


def _attendance_report(db: Session, batch_id: Optional[int] = None) -> Tuple[Headers, Rows]:
    """Attendance records with student names."""
    stmt = (
        select(Attendance, User.full_name, Batch.name)
        .join(User, User.id == Attendance.student_id)
        .join(Batch, Batch.id == Attendance.batch_id)
    )
    if batch_id:
        stmt = stmt.where(Attendance.batch_id == batch_id)
    stmt = stmt.order_by(Attendance.session_date.desc())

    rows_raw = db.execute(stmt).all()
    headers = ["Batch", "Student", "Date", "Status", "Remarks"]
    rows = []
    for att, student_name, batch_name in rows_raw:
        rows.append([
            batch_name,
            student_name,
            str(att.session_date),
            att.status,
            att.remarks or "",
        ])
    return headers, rows


def _course_progress_report(db: Session, course_id: Optional[int] = None) -> Tuple[Headers, Rows]:
    """High-level course progress: enrollment count, completion count, revenue."""
    stmt = select(Course).where(Course.is_deleted.is_(False))
    if course_id:
        stmt = stmt.where(Course.id == course_id)
    courses = db.execute(stmt.order_by(Course.name)).scalars().all()

    headers = ["Course", "Code", "Status", "Enrollments", "Completed", "Revenue"]
    rows = []
    for c in courses:
        enr_total = db.execute(
            select(func.count(Enrollment.id)).where(Enrollment.course_id == c.id)
        ).scalar_one()
        enr_completed = db.execute(
            select(func.count(Enrollment.id)).where(Enrollment.course_id == c.id, Enrollment.status == "completed")
        ).scalar_one()
        revenue = db.execute(
            select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
                Payment.course_id == c.id, Payment.status.in_(["paid", "partially_paid"])
            )
        ).scalar_one()
        rows.append([c.name, c.course_code, c.status, enr_total, enr_completed, str(revenue)])
    return headers, rows


REPORT_TYPES = {
    "students": _students_report,
    "enrollments": _enrollments_report,
    "payments": _payments_report,
    "attendance": _attendance_report,
    "course-progress": _course_progress_report,
}


def get_report_data(
    db: Session, report_type: str, course_id: Optional[int] = None, batch_id: Optional[int] = None
) -> Tuple[str, Headers, Rows]:
    """Return (title, headers, rows) for a given report type."""
    if report_type not in REPORT_TYPES:
        from fastapi import status as http_status
        from app.middleware.exceptions import AppException
        raise AppException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            code="INVALID_REPORT_TYPE",
            message=f"Unknown report type '{report_type}'. Valid types: {', '.join(REPORT_TYPES.keys())}.",
        )

    fn = REPORT_TYPES[report_type]
    import inspect
    sig = inspect.signature(fn)
    kwargs = {"db": db}
    if "course_id" in sig.parameters and course_id is not None:
        kwargs["course_id"] = course_id
    if "batch_id" in sig.parameters and batch_id is not None:
        kwargs["batch_id"] = batch_id

    headers, rows = fn(**kwargs)
    title = report_type.replace("-", " ").title() + " Report"
    return title, headers, rows
