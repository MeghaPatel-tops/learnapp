from typing import Iterable, Optional

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Batch, BatchStudent, Course, Enrollment
from app.models.mixins import utcnow
from app.models.operations import Announcement, Notification
from app.models.user import Role, User
from app.schemas.notification import AnnouncementCreateRequest, AnnouncementOut, NotificationOut
from app.services.authorization import (
    assert_instructor_assigned_to_batch,
    assert_instructor_assigned_to_course,
    get_user_role,
)
from app.utils.email_service import send_email_notification
from app.utils.pagination import apply_sorting, paginate_query


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    event_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    send_email: bool = False,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title[:200],
        message=message,
        event_type=event_type[:60],
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(notif)
    if send_email:
        email = db.execute(select(User.email).where(User.id == user_id, User.is_active.is_(True))).scalar_one_or_none()
        if email:
            send_email_notification(email, title, message)
    return notif


def notify_course_students(
    db: Session,
    course_id: int,
    title: str,
    message: str,
    event_type: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
    batch_id: Optional[int] = None,
) -> None:
    if batch_id is not None:
        student_ids = db.execute(
            select(BatchStudent.student_id).where(
                BatchStudent.batch_id == batch_id,
                BatchStudent.status == "active",
            )
        ).scalars().all()
    else:
        student_ids = db.execute(
            select(Enrollment.student_id).where(
                Enrollment.course_id == course_id,
                Enrollment.status == "active",
            )
        ).scalars().all()

    for sid in set(student_ids):
        create_notification(db, sid, title, message, event_type, reference_type, reference_id)


def list_my_notifications(
    db: Session,
    user_id: int,
    page: int,
    page_size: int,
    is_read: Optional[bool],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read.is_(is_read))
    stmt = apply_sorting(
        stmt,
        Notification,
        sort_by,
        sort_order,
        {"id": Notification.id, "created_at": Notification.created_at},
        Notification.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=NotificationOut.model_validate)


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> NotificationOut:
    notif = db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    ).scalar_one_or_none()
    if notif is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="NOTIFICATION_NOT_FOUND", message="Notification not found.")
    notif.is_read = True
    notif.read_at = utcnow()
    db.commit()
    db.refresh(notif)
    return NotificationOut.model_validate(notif)


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    rows = db.execute(
        select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
    ).scalars().all()
    now = utcnow()
    for n in rows:
        n.is_read = True
        n.read_at = now
    db.commit()
    return len(rows)


def create_announcement(db: Session, payload: AnnouncementCreateRequest, current_user: User) -> AnnouncementOut:
    role = get_user_role(current_user)
    if role == "instructor":
        if payload.batch_id is not None:
            batch = db.execute(select(Batch).where(Batch.id == payload.batch_id)).scalar_one_or_none()
            if batch is None:
                raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="BATCH_NOT_FOUND", message="Batch not found.")
            assert_instructor_assigned_to_batch(db, current_user, batch)
        elif payload.course_id is not None:
            assert_instructor_assigned_to_course(db, current_user, payload.course_id)
        else:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Instructors can only publish announcements for their assigned courses or batches.",
            )

    ann = Announcement(
        title=payload.title.strip(),
        content=payload.content.strip(),
        target_role=payload.target_role,
        course_id=payload.course_id,
        batch_id=payload.batch_id,
        created_by=current_user.id,
        published_at=utcnow(),
    )
    db.add(ann)
    db.flush()

    # Fan out in-app notifications
    recipient_ids: Iterable[int] = []
    if payload.batch_id is not None:
        recipient_ids = db.execute(
            select(BatchStudent.student_id).where(
                BatchStudent.batch_id == payload.batch_id,
                BatchStudent.status == "active",
            )
        ).scalars().all()
    elif payload.course_id is not None:
        recipient_ids = db.execute(
            select(Enrollment.student_id).where(
                Enrollment.course_id == payload.course_id,
                Enrollment.status == "active",
            )
        ).scalars().all()
    else:
        q = select(User.id).join(Role, Role.id == User.role_id).where(User.is_active.is_(True))
        if payload.target_role and payload.target_role != "all":
            q = q.where(Role.name == payload.target_role)
        recipient_ids = db.execute(q).scalars().all()

    for uid in set(recipient_ids):
        if uid != current_user.id:
            create_notification(
                db,
                user_id=uid,
                title=f"Announcement: {ann.title}",
                message=ann.content[:400],
                event_type="announcement",
                reference_type="announcement",
                reference_id=ann.id,
            )

    db.commit()
    db.refresh(ann)
    return AnnouncementOut.model_validate(ann)


def list_announcements(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    course_id: Optional[int],
    batch_id: Optional[int],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Announcement)

    if role == "student":
        enrolled_courses = select(Enrollment.course_id).where(
            Enrollment.student_id == current_user.id,
            or_(Enrollment.status == "active", Enrollment.status == "completed"),
        )
        my_batches = select(BatchStudent.batch_id).where(
            BatchStudent.student_id == current_user.id,
            BatchStudent.status != "removed",
        )
        stmt = stmt.where(
            or_(
                Announcement.target_role.in_(["all", "student"]),
                Announcement.course_id.in_(enrolled_courses),
                Announcement.batch_id.in_(my_batches),
            )
        )
    elif role == "instructor":
        stmt = stmt.where(
            or_(
                Announcement.target_role.in_(["all", "instructor"]),
                Announcement.target_role.is_(None),
                Announcement.created_by == current_user.id,
            )
        )

    if course_id is not None:
        stmt = stmt.where(Announcement.course_id == course_id)
    if batch_id is not None:
        stmt = stmt.where(Announcement.batch_id == batch_id)

    stmt = apply_sorting(
        stmt,
        Announcement,
        sort_by,
        sort_order,
        {"id": Announcement.id, "published_at": Announcement.published_at},
        Announcement.published_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=AnnouncementOut.model_validate)
