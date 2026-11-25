from datetime import timedelta
from decimal import Decimal
from typing import List, Optional

from fastapi import status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.exceptions import AppException
from app.models.assessment import Question, Quiz, QuizAnswer, QuizAttempt, QuizOption
from app.models.course import Batch, BatchStudent, Course, Enrollment
from app.models.mixins import utcnow
from app.models.user import User
from app.schemas.quiz import (
    QuestionCreate,
    QuestionOut,
    QuizAnswerReviewOut,
    QuizAttemptOut,
    QuizCreateRequest,
    QuizDetailOut,
    QuizOptionOut,
    QuizOut,
    QuizUpdateRequest,
    SaveAnswerRequest,
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
from app.utils.pagination import apply_sorting, paginate_query


def _get_quiz_or_404(db: Session, quiz_id: int) -> Quiz:
    quiz = db.execute(
        select(Quiz)
        .options(joinedload(Quiz.questions).joinedload(Question.options))
        .where(Quiz.id == quiz_id)
    ).unique().scalar_one_or_none()
    if quiz is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="QUIZ_NOT_FOUND", message="Quiz not found.")
    return quiz


def _authorize_quiz_manage(db: Session, user: User, course_id: int, batch_id: Optional[int]) -> None:
    if batch_id is not None:
        batch = db.execute(select(Batch).where(Batch.id == batch_id)).scalar_one_or_none()
        if batch is None or batch.course_id != course_id:
            raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_BATCH", message="Batch not found for this course.")
        assert_instructor_assigned_to_batch(db, user, batch)
    else:
        assert_instructor_assigned_to_course(db, user, course_id)


def _serialize_questions(questions: List[Question], expose_correct: bool) -> List[QuestionOut]:
    result = []
    for q in sorted(questions, key=lambda item: (item.sequence_order, item.id)):
        opts = [
            QuizOptionOut(
                id=o.id,
                option_text=o.option_text,
                sequence_order=o.sequence_order,
                is_correct=o.is_correct if expose_correct else None,
            )
            for o in sorted(q.options, key=lambda item: (item.sequence_order, item.id))
        ]
        result.append(
            QuestionOut(
                id=q.id,
                quiz_id=q.quiz_id,
                question_text=q.question_text,
                marks=q.marks,
                sequence_order=q.sequence_order,
                options=opts,
            )
        )
    return result


def _serialize_quiz_summary(db: Session, quiz: Quiz) -> QuizOut:
    q_count = db.execute(select(func.count(Question.id)).where(Question.quiz_id == quiz.id)).scalar_one()
    return QuizOut(
        id=quiz.id,
        course_id=quiz.course_id,
        batch_id=quiz.batch_id,
        title=quiz.title,
        description=quiz.description,
        total_marks=quiz.total_marks,
        passing_marks=quiz.passing_marks,
        duration_minutes=quiz.duration_minutes,
        available_from=quiz.available_from,
        available_until=quiz.available_until,
        allow_retakes=quiz.allow_retakes,
        max_attempts=quiz.max_attempts,
        show_correct_answers=quiz.show_correct_answers,
        is_published=quiz.is_published,
        question_count=q_count,
        created_at=quiz.created_at,
    )


def list_quizzes(
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
    stmt = select(Quiz)

    if role == "instructor":
        if not current_user.instructor_profile:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        inst_id = current_user.instructor_profile.id
        course_ids = select(Course.id).where(Course.primary_instructor_id == inst_id)
        batch_ids = select(Batch.id).where(Batch.instructor_id == inst_id)
        stmt = stmt.where(or_(Quiz.course_id.in_(course_ids), Quiz.batch_id.in_(batch_ids)))
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
            Quiz.is_published.is_(True),
            Quiz.course_id.in_(enrolled_courses),
            or_(Quiz.batch_id.is_(None), Quiz.batch_id.in_(my_batches)),
        )

    if course_id is not None:
        stmt = stmt.where(Quiz.course_id == course_id)
    if batch_id is not None:
        stmt = stmt.where(Quiz.batch_id == batch_id)

    stmt = apply_sorting(
        stmt,
        Quiz,
        sort_by,
        sort_order,
        {"id": Quiz.id, "available_from": Quiz.available_from, "created_at": Quiz.created_at},
        Quiz.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda q: _serialize_quiz_summary(db, q))


def _add_question_entity(db: Session, quiz_id: int, q_data: QuestionCreate) -> Question:
    question = Question(
        quiz_id=quiz_id,
        question_text=q_data.question_text.strip(),
        marks=q_data.marks,
        sequence_order=q_data.sequence_order,
    )
    db.add(question)
    db.flush()
    for opt in q_data.options:
        db.add(
            QuizOption(
                question_id=question.id,
                option_text=opt.option_text.strip(),
                is_correct=opt.is_correct,
                sequence_order=opt.sequence_order,
            )
        )
    return question


def create_quiz(db: Session, payload: QuizCreateRequest, current_user: User) -> QuizDetailOut:
    course = db.execute(
        select(Course).where(Course.id == payload.course_id, Course.is_deleted.is_(False))
    ).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")

    _authorize_quiz_manage(db, current_user, payload.course_id, payload.batch_id)

    av_from = payload.available_from.replace(tzinfo=None) if payload.available_from.tzinfo else payload.available_from
    av_until = payload.available_until.replace(tzinfo=None) if payload.available_until.tzinfo else payload.available_until

    quiz = Quiz(
        course_id=payload.course_id,
        batch_id=payload.batch_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        total_marks=payload.total_marks,
        passing_marks=payload.passing_marks,
        duration_minutes=payload.duration_minutes,
        available_from=av_from,
        available_until=av_until,
        allow_retakes=payload.allow_retakes,
        max_attempts=payload.max_attempts if payload.allow_retakes else 1,
        show_correct_answers=payload.show_correct_answers,
        is_published=payload.is_published,
        created_by=current_user.id,
    )
    db.add(quiz)
    db.flush()

    for q_item in payload.questions:
        _add_question_entity(db, quiz.id, q_item)

    if quiz.is_published:
        notify_course_students(
            db,
            course_id=quiz.course_id,
            batch_id=quiz.batch_id,
            title=f"New Quiz Available: {quiz.title}",
            message=f"Quiz '{quiz.title}' is scheduled from {av_from.strftime('%Y-%m-%d %H:%M UTC')} to {av_until.strftime('%Y-%m-%d %H:%M UTC')}.",
            event_type="quiz_announced",
            reference_type="quiz",
            reference_id=quiz.id,
        )

    db.commit()
    loaded = _get_quiz_or_404(db, quiz.id)
    summary = _serialize_quiz_summary(db, loaded)
    return QuizDetailOut(**summary.model_dump(), questions=_serialize_questions(loaded.questions, expose_correct=True))


def get_quiz_detail(db: Session, quiz_id: int, current_user: User) -> QuizDetailOut:
    quiz = _get_quiz_or_404(db, quiz_id)
    assert_can_access_course_content(db, current_user, quiz.course_id)
    role = get_user_role(current_user)
    if role == "student":
        if not quiz.is_published:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="QUIZ_NOT_FOUND", message="Quiz not found.")
        if quiz.batch_id is not None:
            member = db.execute(
                select(BatchStudent.id).where(
                    BatchStudent.batch_id == quiz.batch_id,
                    BatchStudent.student_id == current_user.id,
                    BatchStudent.status != "removed",
                )
            ).scalar_one_or_none()
            if member is None:
                raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Quiz belongs to another batch.")

    expose_correct = role in {"admin", "instructor"}
    summary = _serialize_quiz_summary(db, quiz)
    return QuizDetailOut(
        **summary.model_dump(),
        questions=_serialize_questions(quiz.questions, expose_correct=expose_correct),
    )


def update_quiz(db: Session, quiz_id: int, payload: QuizUpdateRequest, current_user: User) -> QuizDetailOut:
    quiz = _get_quiz_or_404(db, quiz_id)
    _authorize_quiz_manage(db, current_user, quiz.course_id, quiz.batch_id)

    new_from = (
        payload.available_from.replace(tzinfo=None)
        if payload.available_from and payload.available_from.tzinfo
        else (payload.available_from or quiz.available_from)
    )
    new_until = (
        payload.available_until.replace(tzinfo=None)
        if payload.available_until and payload.available_until.tzinfo
        else (payload.available_until or quiz.available_until)
    )
    if new_until <= new_from:
        raise AppException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="INVALID_WINDOW", message="available_until must be after available_from.")

    new_total = payload.total_marks if payload.total_marks is not None else quiz.total_marks
    new_pass = payload.passing_marks if payload.passing_marks is not None else quiz.passing_marks
    if new_pass > new_total:
        raise AppException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="INVALID_MARKS", message="passing_marks cannot exceed total_marks.")

    if payload.title is not None:
        quiz.title = payload.title.strip()
    if payload.description is not None:
        quiz.description = payload.description.strip() or None
    quiz.total_marks = new_total
    quiz.passing_marks = new_pass
    quiz.available_from = new_from
    quiz.available_until = new_until
    if payload.duration_minutes is not None:
        quiz.duration_minutes = payload.duration_minutes
    if payload.allow_retakes is not None:
        quiz.allow_retakes = payload.allow_retakes
        if not quiz.allow_retakes:
            quiz.max_attempts = 1
    if payload.max_attempts is not None and quiz.allow_retakes:
        quiz.max_attempts = payload.max_attempts
    if payload.show_correct_answers is not None:
        quiz.show_correct_answers = payload.show_correct_answers
    if payload.is_published is not None:
        quiz.is_published = payload.is_published

    db.commit()
    loaded = _get_quiz_or_404(db, quiz.id)
    summary = _serialize_quiz_summary(db, loaded)
    return QuizDetailOut(**summary.model_dump(), questions=_serialize_questions(loaded.questions, expose_correct=True))


def add_question_to_quiz(db: Session, quiz_id: int, payload: QuestionCreate, current_user: User) -> QuestionOut:
    quiz = _get_quiz_or_404(db, quiz_id)
    _authorize_quiz_manage(db, current_user, quiz.course_id, quiz.batch_id)

    question = _add_question_entity(db, quiz.id, payload)
    db.commit()
    loaded = db.execute(
        select(Question).options(joinedload(Question.options)).where(Question.id == question.id)
    ).unique().scalar_one()
    return _serialize_questions([loaded], expose_correct=True)[0]


def _finalize_and_grade_attempt(db: Session, attempt: QuizAttempt, quiz: Quiz, final_status: str) -> QuizAttempt:
    """Calculate score strictly on the backend from DB QuizOption.is_correct flags."""
    answers = db.execute(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt.id)).scalars().all()
    ans_by_q = {a.question_id: a for a in answers}

    total_score = Decimal("0.00")
    for q in quiz.questions:
        ans = ans_by_q.get(q.id)
        if ans is None or ans.selected_option_id is None:
            continue
        opt = next((o for o in q.options if o.id == ans.selected_option_id), None)
        if opt is not None and opt.is_correct:
            ans.is_correct = True
            ans.marks_awarded = q.marks
            total_score += q.marks
        else:
            ans.is_correct = False
            ans.marks_awarded = Decimal("0.00")

    attempt.score = total_score
    attempt.is_passed = total_score >= quiz.passing_marks
    attempt.status = final_status
    attempt.submitted_at = utcnow()
    db.flush()

    compute_course_progress(db, attempt.student_id, quiz.course_id)
    create_notification(
        db,
        user_id=attempt.student_id,
        title=f"Quiz Graded: {quiz.title}",
        message=f"You scored {total_score}/{quiz.total_marks} ({'Passed' if attempt.is_passed else 'Not Passed'}).",
        event_type="quiz_result",
        reference_type="quiz_attempt",
        reference_id=attempt.id,
    )
    return attempt


def _serialize_attempt(attempt: QuizAttempt, quiz: Quiz, is_staff: bool) -> QuizAttemptOut:
    finalized = attempt.status in {"submitted", "timed_out"}
    expose_correct = is_staff or (finalized and quiz.show_correct_answers)
    q_outs = _serialize_questions(quiz.questions, expose_correct=expose_correct)

    correct_map = {}
    if expose_correct:
        for q in quiz.questions:
            for o in q.options:
                if o.is_correct:
                    correct_map[q.id] = o.id

    ans_outs = [
        QuizAnswerReviewOut(
            question_id=a.question_id,
            selected_option_id=a.selected_option_id,
            is_correct=a.is_correct if finalized or is_staff else None,
            marks_awarded=a.marks_awarded if finalized or is_staff else Decimal("0.00"),
            correct_option_id=correct_map.get(a.question_id) if expose_correct else None,
        )
        for a in attempt.answers
    ]

    return QuizAttemptOut(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        student_id=attempt.student_id,
        attempt_number=attempt.attempt_number,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        submitted_at=attempt.submitted_at,
        status=attempt.status,
        score=attempt.score,
        is_passed=attempt.is_passed,
        questions=q_outs,
        answers=ans_outs,
    )


def start_quiz_attempt(db: Session, quiz_id: int, current_user: User) -> QuizAttemptOut:
    quiz = _get_quiz_or_404(db, quiz_id)
    assert_student_enrolled_in_course(db, current_user.id, quiz.course_id)

    if not quiz.is_published:
        raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code="QUIZ_UNPUBLISHED", message="Quiz is not published.")
    if not quiz.questions:
        raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code="NO_QUESTIONS", message="Quiz has no questions.")

    if quiz.batch_id is not None:
        member = db.execute(
            select(BatchStudent.id).where(
                BatchStudent.batch_id == quiz.batch_id,
                BatchStudent.student_id == current_user.id,
                BatchStudent.status != "removed",
            )
        ).scalar_one_or_none()
        if member is None:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Quiz belongs to another batch.")

    now = utcnow()
    if now < quiz.available_from or now > quiz.available_until:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="QUIZ_OUTSIDE_WINDOW",
            message="Quiz is not currently within its availability window.",
        )

    existing_attempts = db.execute(
        select(QuizAttempt)
        .options(joinedload(QuizAttempt.answers))
        .where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.student_id == current_user.id)
        .order_by(QuizAttempt.attempt_number.asc())
    ).unique().scalars().all()

    for att in existing_attempts:
        if att.status == "in_progress":
            if now <= att.expires_at:
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="ATTEMPT_IN_PROGRESS",
                    message=f"You already have an active attempt (id={att.id}).",
                )
            _finalize_and_grade_attempt(db, att, quiz, "timed_out")
            db.commit()

    max_allowed = quiz.max_attempts if quiz.allow_retakes else 1
    if len(existing_attempts) >= max_allowed:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="MAX_ATTEMPTS_REACHED",
            message=f"Maximum allowed attempts ({max_allowed}) reached for this quiz.",
        )

    expires_at = min(now + timedelta(minutes=quiz.duration_minutes), quiz.available_until)
    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.id,
        attempt_number=len(existing_attempts) + 1,
        started_at=now,
        expires_at=expires_at,
        status="in_progress",
    )
    db.add(attempt)
    db.commit()
    loaded = db.execute(
        select(QuizAttempt).options(joinedload(QuizAttempt.answers)).where(QuizAttempt.id == attempt.id)
    ).unique().scalar_one()
    return _serialize_attempt(loaded, quiz, is_staff=False)


def save_quiz_answer(
    db: Session, attempt_id: int, payload: SaveAnswerRequest, current_user: User
) -> QuizAttemptOut:
    attempt = db.execute(
        select(QuizAttempt).options(joinedload(QuizAttempt.answers)).where(QuizAttempt.id == attempt_id)
    ).unique().scalar_one_or_none()
    if attempt is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ATTEMPT_NOT_FOUND", message="Quiz attempt not found.")
    if attempt.student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You cannot modify another student's attempt.")

    if attempt.status != "in_progress":
        raise AppException(status_code=status.HTTP_409_CONFLICT, code="ATTEMPT_CLOSED", message="Quiz attempt has already been finalized.")

    quiz = _get_quiz_or_404(db, attempt.quiz_id)
    now = utcnow()
    if now > attempt.expires_at:
        _finalize_and_grade_attempt(db, attempt, quiz, "timed_out")
        db.commit()
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="ATTEMPT_TIMED_OUT",
            message="Quiz attempt time expired and has been auto-submitted.",
        )

    question = next((q for q in quiz.questions if q.id == payload.question_id), None)
    if question is None:
        raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_QUESTION", message="Question does not belong to this quiz.")
    option = next((o for o in question.options if o.id == payload.selected_option_id), None)
    if option is None:
        raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_OPTION", message="Selected option does not belong to this question.")

    existing = db.execute(
        select(QuizAnswer).where(QuizAnswer.attempt_id == attempt_id, QuizAnswer.question_id == payload.question_id)
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            QuizAnswer(
                attempt_id=attempt_id,
                question_id=payload.question_id,
                selected_option_id=payload.selected_option_id,
                answered_at=now,
            )
        )
    else:
        existing.selected_option_id = payload.selected_option_id
        existing.answered_at = now

    db.commit()
    loaded = db.execute(
        select(QuizAttempt).options(joinedload(QuizAttempt.answers)).where(QuizAttempt.id == attempt_id)
    ).unique().scalar_one()
    return _serialize_attempt(loaded, quiz, is_staff=False)


def submit_quiz_attempt(db: Session, attempt_id: int, current_user: User) -> QuizAttemptOut:
    attempt = db.execute(
        select(QuizAttempt).options(joinedload(QuizAttempt.answers)).where(QuizAttempt.id == attempt_id)
    ).unique().scalar_one_or_none()
    if attempt is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ATTEMPT_NOT_FOUND", message="Quiz attempt not found.")
    if attempt.student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You cannot submit another student's attempt.")

    if attempt.status != "in_progress":
        raise AppException(status_code=status.HTTP_409_CONFLICT, code="ATTEMPT_ALREADY_SUBMITTED", message="Quiz attempt has already been submitted.")

    quiz = _get_quiz_or_404(db, attempt.quiz_id)
    final_status = "timed_out" if utcnow() > attempt.expires_at else "submitted"
    _finalize_and_grade_attempt(db, attempt, quiz, final_status)
    db.commit()

    loaded = db.execute(
        select(QuizAttempt).options(joinedload(QuizAttempt.answers)).where(QuizAttempt.id == attempt_id)
    ).unique().scalar_one()
    return _serialize_attempt(loaded, quiz, is_staff=False)


def get_attempt_detail(db: Session, attempt_id: int, current_user: User) -> QuizAttemptOut:
    attempt = db.execute(
        select(QuizAttempt).options(joinedload(QuizAttempt.answers)).where(QuizAttempt.id == attempt_id)
    ).unique().scalar_one_or_none()
    if attempt is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="ATTEMPT_NOT_FOUND", message="Quiz attempt not found.")

    quiz = _get_quiz_or_404(db, attempt.quiz_id)
    role = get_user_role(current_user)
    if role == "student" and attempt.student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You cannot view another student's quiz attempt.")
    elif role == "instructor":
        _authorize_quiz_manage(db, current_user, quiz.course_id, quiz.batch_id)

    return _serialize_attempt(attempt, quiz, is_staff=(role in {"admin", "instructor"}))


def list_quiz_attempts(db: Session, quiz_id: int, current_user: User) -> List[QuizAttemptOut]:
    quiz = _get_quiz_or_404(db, quiz_id)
    role = get_user_role(current_user)
    stmt = (
        select(QuizAttempt)
        .options(joinedload(QuizAttempt.answers))
        .where(QuizAttempt.quiz_id == quiz_id)
        .order_by(QuizAttempt.started_at.desc())
    )
    if role == "student":
        assert_student_enrolled_in_course(db, current_user.id, quiz.course_id)
        stmt = stmt.where(QuizAttempt.student_id == current_user.id)
    elif role == "instructor":
        _authorize_quiz_manage(db, current_user, quiz.course_id, quiz.batch_id)

    attempts = db.execute(stmt).unique().scalars().all()
    is_staff = role in {"admin", "instructor"}
    return [_serialize_attempt(att, quiz, is_staff=is_staff) for att in attempts]
