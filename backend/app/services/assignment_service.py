from typing import Optional

from fastapi import UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.middleware.exceptions import AppException
from app.models.assessment import Assignment, AssignmentFeedback, Submission
from app.models.course import Batch, BatchStudent, Course, Enrollment
from app.models.mixins import utcnow
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreateRequest,
    AssignmentOut,
    AssignmentUpdateRequest,
    EvaluateSubmissionRequest,
    FeedbackOut,
    SubmissionOut,
)
from app.services.authorization import (
    assert_can_access_course_content,
    assert_instructor_assigned_to_batch,
    assert_instructor_assigned_to_course,
    assert_student_enrolled_in_course,
    get_user_role,
)
from app.services.notification_service import create_notification, notify_course_students
from app.services.progress_service import compute_course_progress
from app.utils.file_storage import (
    ASSIGNMENT_EXTENSIONS,
    delete_stored_file,
    resolve_storage_path,
    save_upload_file,
)
from app.utils.pagination import apply_sorting, paginate_query


def _get_assignment_or_404(db: Session, assignment_id: int) -> Assignment:
    item = db.execute(select(Assignment).where(Assignment.id == assignment_id)).scalar_one_or_none()
    if item is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ASSIGNMENT_NOT_FOUND", message="Assignment not found.")
    return item


def _authorize_assignment_manage(db: Session, user: User, course_id: int, batch_id: Optional[int]) -> None:
    if batch_id is not None:
        batch = db.execute(select(Batch).where(Batch.id == batch_id)).scalar_one_or_none()
        if batch is None or batch.course_id != course_id:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_BATCH",
                message="Batch not found for the specified course.",
            )
        assert_instructor_assigned_to_batch(db, user, batch)
    else:
        assert_instructor_assigned_to_course(db, user, course_id)


def _serialize_submission(db: Session, sub: Submission) -> SubmissionOut:
    student_name = db.execute(select(User.full_name).where(User.id == sub.student_id)).scalar_one_or_none()
    fb = FeedbackOut.model_validate(sub.feedback) if sub.feedback else None
    return SubmissionOut(
        id=sub.id,
        assignment_id=sub.assignment_id,
        student_id=sub.student_id,
        student_name=student_name,
        version=sub.version,
        submission_text=sub.submission_text,
        file_name=sub.file_name,
        mime_type=sub.mime_type,
        file_size=sub.file_size,
        status=sub.status,
        is_late=sub.is_late,
        submitted_at=sub.submitted_at,
        feedback=fb,
    )


def list_assignments(
    db: Session,
    current_user: User,
    course_id: Optional[int],
    batch_id: Optional[int],
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Assignment)

    if role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_id = current_user.instructor_profile.id
        course_ids = select(Course.id).where(Course.primary_instructor_id == inst_id)
        batch_ids = select(Batch.id).where(Batch.instructor_id == inst_id)
        stmt = stmt.where(
            or_(Assignment.course_id.in_(course_ids), Assignment.batch_id.in_(batch_ids))
        )
    elif role == "student":
        enrolled_courses = select(Enrollment.course_id).where(
            Enrollment.student_id == current_user.id,
            or_(Enrollment.status == "active", Enrollment.status == "completed"),
        )
        my_batches = select(BatchStudent.batch_id).where(
            BatchStudent.student_id == current_user.id,
            BatchStudent.status != "removed",
        )
        stmt = stmt.where(
            Assignment.course_id.in_(enrolled_courses),
            or_(Assignment.batch_id.is_(None), Assignment.batch_id.in_(my_batches)),
        )

    if course_id is not None:
        stmt = stmt.where(Assignment.course_id == course_id)
    if batch_id is not None:
        stmt = stmt.where(Assignment.batch_id == batch_id)

    stmt = apply_sorting(
        stmt,
        Assignment,
        sort_by,
        sort_order,
        {"id": Assignment.id, "due_date": Assignment.due_date, "created_at": Assignment.created_at},
        Assignment.due_date,
    )
    return paginate_query(db, stmt, page, page_size, serializer=AssignmentOut.model_validate)


def create_assignment(db: Session, payload: AssignmentCreateRequest, current_user: User) -> AssignmentOut:
    course = db.execute(
        select(Course).where(Course.id == payload.course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")

    _authorize_assignment_manage(db, current_user, payload.course_id, payload.batch_id)

    if payload.passing_marks > payload.max_marks:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_MARKS",
            message="passing_marks cannot exceed max_marks.",
        )

    due_naive = payload.due_date.replace(tzinfo=None) if payload.due_date.tzinfo else payload.due_date
    assignment = Assignment(
        course_id=payload.course_id,
        batch_id=payload.batch_id,
        title=payload.title.strip(),
        instructions=payload.instructions.strip(),
        max_marks=payload.max_marks,
        passing_marks=payload.passing_marks,
        due_date=due_naive,
        allow_late=payload.allow_late,
        created_by=current_user.id,
    )
    db.add(assignment)
    db.flush()

    notify_course_students(
        db,
        course_id=assignment.course_id,
        batch_id=assignment.batch_id,
        title=f"New Assignment: {assignment.title}",
        message=f"Assignment '{assignment.title}' is due on {assignment.due_date.strftime('%Y-%m-%d %H:%M UTC')}.",
        event_type="assignment_created",
        reference_type="assignment",
        reference_id=assignment.id,
    )
    db.commit()
    db.refresh(assignment)
    return AssignmentOut.model_validate(assignment)


def get_assignment(db: Session, assignment_id: int, current_user: User) -> AssignmentOut:
    assignment = _get_assignment_or_404(db, assignment_id)
    assert_can_access_course_content(db, current_user, assignment.course_id)
    if get_user_role(current_user) == "student" and assignment.batch_id is not None:
        member = db.execute(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == assignment.batch_id,
                BatchStudent.student_id == current_user.id,
                BatchStudent.status != "removed",
            )
        ).scalar_one_or_none()
        if member is None:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Assignment belongs to another batch.")
    return AssignmentOut.model_validate(assignment)


def update_assignment(
    db: Session, assignment_id: int, payload: AssignmentUpdateRequest, current_user: User
) -> AssignmentOut:
    assignment = _get_assignment_or_404(db, assignment_id)
    _authorize_assignment_manage(db, current_user, assignment.course_id, payload.batch_id or assignment.batch_id)

    new_max = payload.max_marks if payload.max_marks is not None else assignment.max_marks
    new_pass = payload.passing_marks if payload.passing_marks is not None else assignment.passing_marks
    if new_pass > new_max:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="INVALID_MARKS",
            message="passing_marks cannot exceed max_marks.",
        )

    if payload.batch_id is not None:
        assignment.batch_id = payload.batch_id
    if payload.title is not None:
        assignment.title = payload.title.strip()
    if payload.instructions is not None:
        assignment.instructions = payload.instructions.strip()
    if payload.max_marks is not None:
        assignment.max_marks = payload.max_marks
    if payload.passing_marks is not None:
        assignment.passing_marks = payload.passing_marks
    if payload.due_date is not None:
        assignment.due_date = payload.due_date.replace(tzinfo=None) if payload.due_date.tzinfo else payload.due_date
    if payload.allow_late is not None:
        assignment.allow_late = payload.allow_late

    db.commit()
    db.refresh(assignment)
    return AssignmentOut.model_validate(assignment)


async def upload_assignment_attachment(
    db: Session, assignment_id: int, file: UploadFile, current_user: User
) -> AssignmentOut:
    assignment = _get_assignment_or_404(db, assignment_id)
    _authorize_assignment_manage(db, current_user, assignment.course_id, assignment.batch_id)

    settings = get_settings()
    clean_name, storage_key, mime_type, file_size = await save_upload_file(
        file,
        category_dir=f"assignments/course_{assignment.course_id}",
        allowed_extensions=ASSIGNMENT_EXTENSIONS,
        max_size_mb=settings.MAX_ASSIGNMENT_FILE_SIZE_MB,
    )
    old_key = assignment.attachment_key
    assignment.attachment_name = clean_name
    assignment.attachment_key = storage_key
    assignment.attachment_mime = mime_type
    assignment.attachment_size = file_size
    db.commit()
    db.refresh(assignment)
    delete_stored_file(old_key)
    return AssignmentOut.model_validate(assignment)


def download_assignment_attachment(db: Session, assignment_id: int, current_user: User) -> FileResponse:
    assignment = get_assignment(db, assignment_id, current_user)
    row = _get_assignment_or_404(db, assignment.id)
    if not row.attachment_key:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ATTACHMENT_NOT_FOUND", message="No attachment on this assignment.")
    path = resolve_storage_path(row.attachment_key)
    if not path.exists():
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_MISSING", message="Attachment file missing on storage.")
    return FileResponse(path=str(path), media_type=row.attachment_mime or "application/octet-stream", filename=row.attachment_name or "attachment")


async def submit_assignment(
    db: Session,
    assignment_id: int,
    submission_text: Optional[str],
    file: Optional[UploadFile],
    current_user: User,
) -> SubmissionOut:
    assignment = _get_assignment_or_404(db, assignment_id)
    assert_student_enrolled_in_course(db, current_user.id, assignment.course_id)

    if assignment.batch_id is not None:
        member = db.execute(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == assignment.batch_id,
                BatchStudent.student_id == current_user.id,
                BatchStudent.status != "removed",
            )
        ).scalar_one_or_none()
        if member is None:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You are not in the target batch for this assignment.")

    clean_text = submission_text.strip() if submission_text and submission_text.strip() else None
    if clean_text is None and file is None:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="EMPTY_SUBMISSION",
            message="Provide submission_text or upload a submission file.",
        )

    now = utcnow()
    is_late = now > assignment.due_date
    if is_late and not assignment.allow_late:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="DEADLINE_PASSED",
            message="The assignment deadline has passed and late submissions are not permitted.",
        )

    latest = db.execute(
        select(Submission)
        .where(Submission.assignment_id == assignment_id, Submission.student_id == current_user.id)
        .order_by(Submission.version.desc())
        .limit(1)
    ).scalar_one_or_none()

    if latest is not None and latest.status == "evaluated":
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="ALREADY_EVALUATED",
            message="Submission has already been evaluated; new versions cannot be submitted.",
        )

    next_version = (latest.version + 1) if latest is not None else 1

    file_name = storage_key = mime_type = None
    file_size = None
    if file is not None:
        settings = get_settings()
        file_name, storage_key, mime_type, file_size = await save_upload_file(
            file,
            category_dir=f"submissions/assignment_{assignment_id}",
            allowed_extensions=ASSIGNMENT_EXTENSIONS,
            max_size_mb=settings.MAX_ASSIGNMENT_FILE_SIZE_MB,
        )

    sub = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        version=next_version,
        submission_text=clean_text,
        file_name=file_name,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size=file_size,
        status="late_submission" if is_late else "submitted",
        is_late=is_late,
        submitted_at=now,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return _serialize_submission(db, sub)


def list_submissions(
    db: Session,
    current_user: User,
    assignment_id: Optional[int],
    status_filter: Optional[str],
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Submission).options(joinedload(Submission.feedback))

    if role == "student":
        stmt = stmt.where(Submission.student_id == current_user.id)
    elif role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_id = current_user.instructor_profile.id
        course_ids = select(Course.id).where(Course.primary_instructor_id == inst_id)
        batch_ids = select(Batch.id).where(Batch.instructor_id == inst_id)
        allowed_assign_ids = select(Assignment.id).where(
            or_(Assignment.course_id.in_(course_ids), Assignment.batch_id.in_(batch_ids))
        )
        stmt = stmt.where(Submission.assignment_id.in_(allowed_assign_ids))

    if assignment_id is not None:
        stmt = stmt.where(Submission.assignment_id == assignment_id)
    if status_filter:
        stmt = stmt.where(Submission.status == status_filter)

    stmt = apply_sorting(
        stmt,
        Submission,
        sort_by,
        sort_order,
        {"id": Submission.id, "submitted_at": Submission.submitted_at, "version": Submission.version},
        Submission.submitted_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda s: _serialize_submission(db, s))


def _get_authorized_submission(db: Session, submission_id: int, current_user: User) -> tuple[Submission, Assignment]:
    sub = db.execute(
        select(Submission).options(joinedload(Submission.feedback)).where(Submission.id == submission_id)
    ).scalar_one_or_none()
    if sub is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="SUBMISSION_NOT_FOUND", message="Submission not found.")

    assignment = _get_assignment_or_404(db, sub.assignment_id)
    role = get_user_role(current_user)
    if role == "student":
        if sub.student_id != current_user.id:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You cannot access another student's submission.")
    elif role == "instructor":
        _authorize_assignment_manage(db, current_user, assignment.course_id, assignment.batch_id)

    return sub, assignment


def get_submission_detail(db: Session, submission_id: int, current_user: User) -> SubmissionOut:
    sub, _ = _get_authorized_submission(db, submission_id, current_user)
    return _serialize_submission(db, sub)


def download_submission_file(db: Session, submission_id: int, current_user: User) -> FileResponse:
    sub, _ = _get_authorized_submission(db, submission_id, current_user)
    if not sub.storage_key:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_NOT_FOUND", message="No file uploaded for this submission.")
    path = resolve_storage_path(sub.storage_key)
    if not path.exists():
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_MISSING", message="Submission file missing on storage.")
    return FileResponse(path=str(path), media_type=sub.mime_type or "application/octet-stream", filename=sub.file_name or "submission")


def mark_under_review(db: Session, submission_id: int, current_user: User) -> SubmissionOut:
    sub, assignment = _get_authorized_submission(db, submission_id, current_user)
    _authorize_assignment_manage(db, current_user, assignment.course_id, assignment.batch_id)
    if sub.status == "evaluated":
        raise AppException(status_code=status.HTTP_409_CONFLICT, code="ALREADY_EVALUATED", message="Submission is already evaluated.")
    sub.status = "under_review"
    db.commit()
    db.refresh(sub)
    return _serialize_submission(db, sub)


def evaluate_submission(
    db: Session, submission_id: int, payload: EvaluateSubmissionRequest, current_user: User
) -> SubmissionOut:
    sub, assignment = _get_authorized_submission(db, submission_id, current_user)
    _authorize_assignment_manage(db, current_user, assignment.course_id, assignment.batch_id)

    if payload.marks_obtained > assignment.max_marks:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="MARKS_EXCEED_MAX",
            message=f"marks_obtained ({payload.marks_obtained}) cannot exceed assignment max_marks ({assignment.max_marks}).",
        )

    now = utcnow()
    if sub.feedback is None:
        fb = AssignmentFeedback(
            submission_id=sub.id,
            evaluator_id=current_user.id,
            marks_obtained=payload.marks_obtained,
            feedback_text=payload.feedback_text.strip() if payload.feedback_text else None,
            evaluated_at=now,
        )
        db.add(fb)
    else:
        sub.feedback.evaluator_id = current_user.id
        sub.feedback.marks_obtained = payload.marks_obtained
        sub.feedback.feedback_text = payload.feedback_text.strip() if payload.feedback_text else None
        sub.feedback.evaluated_at = now

    sub.status = "evaluated"
    db.flush()

    compute_course_progress(db, sub.student_id, assignment.course_id)
    create_notification(
        db,
        user_id=sub.student_id,
        title=f"Assignment Evaluated: {assignment.title}",
        message=f"Your submission was evaluated with {payload.marks_obtained}/{assignment.max_marks} marks.",
        event_type="assignment_evaluated",
        reference_type="submission",
        reference_id=sub.id,
    )

    db.commit()
    db.refresh(sub)
    return _serialize_submission(db, sub)
