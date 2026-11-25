"""Dashboard service – role-specific overview aggregations."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import Assignment, Quiz, QuizAttempt, Submission
from app.models.content import Lecture, LectureProgress
from app.models.course import Batch, BatchStudent, Course, CourseInstructor, Enrollment
from app.models.operations import Attendance, Payment
from app.models.user import Role, User
from app.services.authorization import get_user_role


def admin_dashboard(db: Session) -> dict:
    """Full institute summary for admins."""
    student_role_id = db.execute(select(Role.id).where(Role.name == "student")).scalar_one_or_none()
    instructor_role_id = db.execute(select(Role.id).where(Role.name == "instructor")).scalar_one_or_none()

    total_students = db.execute(
        select(func.count(User.id)).where(User.role_id == student_role_id, User.is_active.is_(True))
    ).scalar_one() if student_role_id else 0

    total_instructors = db.execute(
        select(func.count(User.id)).where(User.role_id == instructor_role_id, User.is_active.is_(True))
    ).scalar_one() if instructor_role_id else 0

    total_courses = db.execute(
        select(func.count(Course.id)).where(Course.is_deleted.is_(False))
    ).scalar_one()

    published_courses = db.execute(
        select(func.count(Course.id)).where(Course.is_deleted.is_(False), Course.status == "published")
    ).scalar_one()

    total_batches = db.execute(select(func.count(Batch.id))).scalar_one()
    active_batches = db.execute(
        select(func.count(Batch.id)).where(Batch.status == "active")
    ).scalar_one()

    total_enrollments = db.execute(select(func.count(Enrollment.id))).scalar_one()
    active_enrollments = db.execute(
        select(func.count(Enrollment.id)).where(Enrollment.status == "active")
    ).scalar_one()

    total_revenue = Decimal(
        str(
            db.execute(
                select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
                    Payment.status.in_(["paid", "partially_paid"])
                )
            ).scalar_one()
        )
    )

    pending_payments = Decimal(
        str(
            db.execute(
                select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(Payment.status == "pending")
            ).scalar_one()
        )
    )

    recent_enrollments = db.execute(
        select(Enrollment).order_by(Enrollment.enrolled_at.desc()).limit(10)
    ).scalars().all()

    recent_items = []
    for e in recent_enrollments:
        student_name = db.execute(select(User.full_name).where(User.id == e.student_id)).scalar_one_or_none()
        course_name = db.execute(select(Course.name).where(Course.id == e.course_id)).scalar_one_or_none()
        recent_items.append({
            "enrollment_id": e.id,
            "student_name": student_name,
            "course_name": course_name,
            "status": e.status,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        })

    return {
        "total_students": total_students,
        "total_instructors": total_instructors,
        "total_courses": total_courses,
        "published_courses": published_courses,
        "total_batches": total_batches,
        "active_batches": active_batches,
        "total_enrollments": total_enrollments,
        "active_enrollments": active_enrollments,
        "total_revenue": float(total_revenue),
        "pending_payments": float(pending_payments),
        "recent_enrollments": recent_items,
    }


def instructor_dashboard(db: Session, current_user: User) -> dict:
    """Instructor-specific summary."""
    if not current_user.instructor_profile:
        return {"assigned_courses": 0, "assigned_batches": 0, "pending_evaluations": 0}

    inst_id = current_user.instructor_profile.id

    assigned_course_ids = set()
    # Primary
    primary = db.execute(
        select(Course.id).where(Course.primary_instructor_id == inst_id, Course.is_deleted.is_(False))
    ).scalars().all()
    assigned_course_ids.update(primary)
    # Co-instructor
    co = db.execute(
        select(CourseInstructor.course_id).where(CourseInstructor.instructor_id == inst_id)
    ).scalars().all()
    assigned_course_ids.update(co)
    # Batch instructor
    batch_course_ids = db.execute(
        select(Batch.course_id).where(Batch.instructor_id == inst_id)
    ).scalars().all()
    assigned_course_ids.update(batch_course_ids)

    assigned_batches = db.execute(
        select(func.count(Batch.id)).where(Batch.instructor_id == inst_id)
    ).scalar_one()

    # Pending evaluations: submitted but not yet evaluated submissions for instructor's courses
    pending_evals = 0
    if assigned_course_ids:
        pending_evals = db.execute(
            select(func.count(Submission.id)).where(
                Submission.assignment_id.in_(
                    select(Assignment.id).where(Assignment.course_id.in_(assigned_course_ids))
                ),
                Submission.status == "submitted",
            )
        ).scalar_one()

    return {
        "assigned_courses": len(assigned_course_ids),
        "assigned_batches": assigned_batches,
        "pending_evaluations": pending_evals,
    }


def student_dashboard(db: Session, current_user: User) -> dict:
    """Student-specific summary."""
    student_id = current_user.id

    enrollments = db.execute(
        select(Enrollment).where(Enrollment.student_id == student_id)
    ).scalars().all()

    enrolled_courses = []
    for e in enrollments:
        course_name = db.execute(select(Course.name).where(Course.id == e.course_id)).scalar_one_or_none()
        enrolled_courses.append({
            "enrollment_id": e.id,
            "course_id": e.course_id,
            "course_name": course_name,
            "status": e.status,
            "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
        })

    # Pending assignments
    course_ids = [e.course_id for e in enrollments if e.status == "active"]
    pending_assignments = 0
    if course_ids:
        all_assignment_ids = db.execute(
            select(Assignment.id).where(Assignment.course_id.in_(course_ids))
        ).scalars().all()
        submitted_ids = db.execute(
            select(Submission.assignment_id).where(
                Submission.student_id == student_id,
                Submission.assignment_id.in_(all_assignment_ids),
            )
        ).scalars().all()
        pending_assignments = len(set(all_assignment_ids) - set(submitted_ids))

    # Attendance summary across active batches
    batch_ids = db.execute(
        select(BatchStudent.batch_id).where(
            BatchStudent.student_id == student_id, BatchStudent.status == "active"
        )
    ).scalars().all()
    attendance_pct = 0.0
    if batch_ids:
        statuses = db.execute(
            select(Attendance.status).where(
                Attendance.student_id == student_id, Attendance.batch_id.in_(batch_ids)
            )
        ).scalars().all()
        present = sum(1 for s in statuses if s == "present")
        absent = sum(1 for s in statuses if s == "absent")
        eligible = present + absent
        if eligible > 0:
            attendance_pct = round((present / eligible) * 100, 2)

    return {
        "enrolled_courses": enrolled_courses,
        "total_enrollments": len(enrollments),
        "active_enrollments": sum(1 for e in enrollments if e.status == "active"),
        "completed_enrollments": sum(1 for e in enrollments if e.status == "completed"),
        "pending_assignments": pending_assignments,
        "attendance_percentage": attendance_pct,
    }
