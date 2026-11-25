from typing import List, Optional

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.assessment import Assignment, AssignmentFeedback, Quiz, QuizAttempt, Submission
from app.models.content import Lecture, LectureProgress
from app.models.course import BatchStudent, Course, Enrollment
from app.models.mixins import utcnow
from app.models.operations import Attendance
from app.models.user import User
from app.schemas.progress import AssignmentProgressItem, CourseProgressOut, QuizProgressItem
from app.services.authorization import assert_can_access_course_content, get_user_role


def compute_course_progress(db: Session, student_id: int, course_id: int) -> CourseProgressOut:
    """
    Compute academic progress and verify course completion criteria from real DB records:
    - 100% of published lectures completed (and >= 1 published lecture exists)
    - All applicable assignments evaluated and passed (marks_obtained >= passing_marks)
    - All applicable published quizzes passed (best finalized attempt score >= passing_marks)
    """
    course = db.execute(
        select(Course).where(Course.id == course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")

    enrollment = db.execute(
        select(Enrollment).where(Enrollment.student_id == student_id, Enrollment.course_id == course_id)
    ).scalar_one_or_none()
    if enrollment is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ENROLLMENT_NOT_FOUND", message="Student is not enrolled in this course.")

    # 1. Lectures
    published_lecture_ids = db.execute(
        select(Lecture.id).where(Lecture.course_id == course_id, Lecture.is_published.is_(True))
    ).scalars().all()
    total_lectures = len(published_lecture_ids)

    completed_lectures = 0
    if published_lecture_ids:
        completed_lectures = len(
            db.execute(
                select(LectureProgress.lecture_id).where(
                    LectureProgress.student_id == student_id,
                    LectureProgress.lecture_id.in_(published_lecture_ids),
                    LectureProgress.is_completed.is_(True),
                )
            ).scalars().all()
        )
    pending_lectures = max(0, total_lectures - completed_lectures)
    lecture_pct = round((completed_lectures / total_lectures) * 100, 2) if total_lectures > 0 else 0.0

    # Student's active/completed batches in this course
    student_batch_ids = db.execute(
        select(BatchStudent.batch_id).where(
            BatchStudent.student_id == student_id,
            BatchStudent.status != "removed",
        )
    ).scalars().all()

    # 2. Applicable assignments (course-wide OR targeted to student's batch)
    assign_q = select(Assignment).where(Assignment.course_id == course_id)
    if student_batch_ids:
        assign_q = assign_q.where(or_(Assignment.batch_id.is_(None), Assignment.batch_id.in_(student_batch_ids)))
    else:
        assign_q = assign_q.where(Assignment.batch_id.is_(None))
    assignments = db.execute(assign_q).scalars().all()

    assignment_items: List[AssignmentProgressItem] = []
    assignments_passed = 0
    for a in assignments:
        latest_sub = db.execute(
            select(Submission)
            .where(Submission.assignment_id == a.id, Submission.student_id == student_id)
            .order_by(Submission.version.desc())
            .limit(1)
        ).scalar_one_or_none()
        marks_val: Optional[float] = None
        passed = False
        latest_status = "pending"
        if latest_sub is not None:
            latest_status = latest_sub.status
            fb = db.execute(
                select(AssignmentFeedback).where(AssignmentFeedback.submission_id == latest_sub.id)
            ).scalar_one_or_none()
            if fb is not None:
                marks_val = float(fb.marks_obtained)
                if fb.marks_obtained >= a.passing_marks:
                    passed = True
        if passed:
            assignments_passed += 1
        assignment_items.append(
            AssignmentProgressItem(
                assignment_id=a.id,
                title=a.title,
                max_marks=float(a.max_marks),
                passing_marks=float(a.passing_marks),
                latest_status=latest_status,
                marks_obtained=marks_val,
                passed=passed,
            )
        )

    # 3. Applicable published quizzes
    quiz_q = select(Quiz).where(Quiz.course_id == course_id, Quiz.is_published.is_(True))
    if student_batch_ids:
        quiz_q = quiz_q.where(or_(Quiz.batch_id.is_(None), Quiz.batch_id.in_(student_batch_ids)))
    else:
        quiz_q = quiz_q.where(Quiz.batch_id.is_(None))
    quizzes = db.execute(quiz_q).scalars().all()

    quiz_items: List[QuizProgressItem] = []
    quizzes_passed = 0
    for q in quizzes:
        attempts = db.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == q.id,
                QuizAttempt.student_id == student_id,
                QuizAttempt.status.in_(["submitted", "timed_out"]),
            )
        ).scalars().all()
        best_score = max((float(at.score) for at in attempts), default=None)
        passed = best_score is not None and best_score >= float(q.passing_marks)
        if passed:
            quizzes_passed += 1
        quiz_items.append(
            QuizProgressItem(
                quiz_id=q.id,
                title=q.title,
                total_marks=float(q.total_marks),
                passing_marks=float(q.passing_marks),
                attempts_used=len(attempts),
                best_score=best_score,
                passed=passed,
            )
        )

    # 4. Attendance percentage across student's batches in this course
    att_pct = 0.0
    if student_batch_ids:
        att_statuses = db.execute(
            select(Attendance.status).where(
                Attendance.student_id == student_id,
                Attendance.batch_id.in_(student_batch_ids),
            )
        ).scalars().all()
        present_cnt = sum(1 for s in att_statuses if s == "present")
        absent_cnt = sum(1 for s in att_statuses if s == "absent")
        eligible = present_cnt + absent_cnt
        if eligible > 0:
            att_pct = round((present_cnt / eligible) * 100, 2)

    total_units = total_lectures + len(assignments) + len(quizzes)
    completed_units = completed_lectures + assignments_passed + quizzes_passed
    overall_pct = round((completed_units / total_units) * 100, 2) if total_units > 0 else 0.0

    # Reviewer-agreed completion criteria: 100% lectures + all assignments & quizzes passed
    is_completed = (
        total_lectures > 0
        and completed_lectures == total_lectures
        and assignments_passed == len(assignments)
        and quizzes_passed == len(quizzes)
    )

    if is_completed and enrollment.status == "active":
        enrollment.status = "completed"
        enrollment.completed_at = utcnow()
        db.flush()

    return CourseProgressOut(
        student_id=student_id,
        course_id=course_id,
        course_name=course.name,
        enrollment_status=enrollment.status,
        completed_lectures=completed_lectures,
        total_lectures=total_lectures,
        pending_lectures=pending_lectures,
        lecture_completion_pct=lecture_pct,
        assignments_passed=assignments_passed,
        total_assignments=len(assignments),
        assignment_items=assignment_items,
        quizzes_passed=quizzes_passed,
        total_quizzes=len(quizzes),
        quiz_items=quiz_items,
        attendance_percentage=att_pct,
        overall_progress_pct=overall_pct,
        is_course_completed=is_completed,
        completed_at=enrollment.completed_at,
    )


def get_student_course_progress(
    db: Session, student_id: int, course_id: int, current_user: User
) -> CourseProgressOut:
    role = get_user_role(current_user)
    if role == "student" and current_user.id != student_id:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="You can only view your own progress.",
        )
    if role == "instructor":
        assert_can_access_course_content(db, current_user, course_id)

    progress = compute_course_progress(db, student_id, course_id)
    db.commit()
    return progress
