from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.middleware.exceptions import AppException
from app.models.content import Lecture, LectureProgress, StudyMaterial
from app.models.course import Course, CourseModule
from app.models.mixins import utcnow
from app.models.user import User
from app.schemas.content import (
    LectureCompletionOut,
    LectureCreateRequest,
    LectureOut,
    LectureReorderRequest,
    LectureUpdateRequest,
    StudyMaterialOut,
)
from app.services.authorization import (
    assert_can_access_course_content,
    assert_instructor_assigned_to_course,
    assert_student_enrolled_in_course,
    get_user_role,
)
from app.services.notification_service import notify_course_students
from app.services.progress_service import compute_course_progress
from app.utils.file_storage import (
    MATERIAL_EXTENSIONS,
    VIDEO_EXTENSIONS,
    delete_stored_file,
    resolve_storage_path,
    save_upload_file,
)
from app.utils.pagination import apply_sorting, paginate_query


def _serialize_lecture(lec: Lecture, completed_ids: Optional[set[int]] = None) -> LectureOut:
    return LectureOut(
        id=lec.id,
        course_id=lec.course_id,
        module_id=lec.module_id,
        title=lec.title,
        description=lec.description,
        sequence_order=lec.sequence_order,
        video_url=lec.video_url,
        has_uploaded_video=bool(lec.video_storage_key),
        video_file_name=lec.video_file_name,
        video_file_size=lec.video_file_size,
        duration_minutes=lec.duration_minutes,
        is_published=lec.is_published,
        is_completed=(lec.id in completed_ids) if completed_ids is not None else None,
        created_at=lec.created_at,
        updated_at=lec.updated_at,
    )


def _get_lecture_or_404(db: Session, lecture_id: int) -> Lecture:
    lec = db.execute(select(Lecture).where(Lecture.id == lecture_id)).scalar_one_or_none()
    if lec is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="LECTURE_NOT_FOUND", message="Lecture not found.")
    return lec


def list_lectures(
    db: Session,
    course_id: int,
    module_id: Optional[int],
    current_user: User,
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    assert_can_access_course_content(db, current_user, course_id)
    role = get_user_role(current_user)

    stmt = select(Lecture).where(Lecture.course_id == course_id)
    if role == "student":
        stmt = stmt.where(Lecture.is_published.is_(True))
    if module_id is not None:
        stmt = stmt.where(Lecture.module_id == module_id)

    stmt = apply_sorting(
        stmt,
        Lecture,
        sort_by,
        sort_order if sort_by else "asc",
        {"sequence_order": Lecture.sequence_order, "id": Lecture.id, "created_at": Lecture.created_at},
        Lecture.sequence_order,
    )

    completed_ids: Optional[set[int]] = None
    if role == "student":
        completed_ids = set(
            db.execute(
                select(LectureProgress.lecture_id).where(
                    LectureProgress.student_id == current_user.id,
                    LectureProgress.is_completed.is_(True),
                )
            ).scalars().all()
        )

    return paginate_query(db, stmt, page, page_size, serializer=lambda l: _serialize_lecture(l, completed_ids))


def create_lecture(db: Session, payload: LectureCreateRequest, current_user: User) -> LectureOut:
    assert_instructor_assigned_to_course(db, current_user, payload.course_id)
    mod = db.execute(
        select(CourseModule).where(
            CourseModule.id == payload.module_id,
            CourseModule.course_id == payload.course_id,
        )
    ).scalar_one_or_none()
    if mod is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="MODULE_NOT_FOUND",
            message="Course module not found for this course.",
        )

    lec = Lecture(
        course_id=payload.course_id,
        module_id=payload.module_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        sequence_order=payload.sequence_order,
        video_url=payload.video_url.strip() if payload.video_url else None,
        duration_minutes=payload.duration_minutes,
        is_published=payload.is_published,
        created_by=current_user.id,
    )
    db.add(lec)
    db.flush()

    if lec.is_published:
        notify_course_students(
            db,
            course_id=lec.course_id,
            title="New Lecture Published",
            message=f"A new lecture '{lec.title}' has been published.",
            event_type="lecture_published",
            reference_type="lecture",
            reference_id=lec.id,
        )

    db.commit()
    db.refresh(lec)
    return _serialize_lecture(lec)


def get_lecture(db: Session, lecture_id: int, current_user: User) -> LectureOut:
    lec = _get_lecture_or_404(db, lecture_id)
    assert_can_access_course_content(db, current_user, lec.course_id)
    role = get_user_role(current_user)
    if role == "student" and not lec.is_published:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="LECTURE_NOT_FOUND", message="Lecture not found.")

    completed_ids = None
    if role == "student":
        prog = db.execute(
            select(LectureProgress.id).where(
                LectureProgress.student_id == current_user.id,
                LectureProgress.lecture_id == lec.id,
                LectureProgress.is_completed.is_(True),
            )
        ).scalar_one_or_none()
        completed_ids = {lec.id} if prog is not None else set()

    return _serialize_lecture(lec, completed_ids)


def update_lecture(
    db: Session, lecture_id: int, payload: LectureUpdateRequest, current_user: User
) -> LectureOut:
    lec = _get_lecture_or_404(db, lecture_id)
    assert_instructor_assigned_to_course(db, current_user, lec.course_id)

    if payload.module_id is not None:
        mod = db.execute(
            select(CourseModule).where(
                CourseModule.id == payload.module_id,
                CourseModule.course_id == lec.course_id,
            )
        ).scalar_one_or_none()
        if mod is None:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="MODULE_NOT_FOUND", message="Module not found in course.")
        lec.module_id = payload.module_id

    if payload.title is not None:
        lec.title = payload.title.strip()
    if payload.description is not None:
        lec.description = payload.description.strip() or None
    if payload.sequence_order is not None:
        lec.sequence_order = payload.sequence_order
    if payload.video_url is not None:
        lec.video_url = payload.video_url.strip() or None
    if payload.duration_minutes is not None:
        lec.duration_minutes = payload.duration_minutes
    if payload.is_published is not None:
        lec.is_published = payload.is_published

    db.commit()
    db.refresh(lec)
    return _serialize_lecture(lec)


def reorder_lectures(db: Session, payload: LectureReorderRequest, current_user: User) -> List[LectureOut]:
    assert_instructor_assigned_to_course(db, current_user, payload.course_id)
    lectures = db.execute(
        select(Lecture).where(
            Lecture.course_id == payload.course_id,
            Lecture.module_id == payload.module_id,
        )
    ).scalars().all()
    lec_map = {l.id: l for l in lectures}

    for lid in payload.lecture_ids:
        if lid not in lec_map:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_LECTURE_ID",
                message=f"Lecture {lid} does not belong to course {payload.course_id} module {payload.module_id}.",
            )

    for idx, lid in enumerate(payload.lecture_ids, start=1):
        lec_map[lid].sequence_order = idx

    db.commit()
    ordered = db.execute(
        select(Lecture)
        .where(Lecture.course_id == payload.course_id, Lecture.module_id == payload.module_id)
        .order_by(Lecture.sequence_order.asc())
    ).scalars().all()
    return [_serialize_lecture(l) for l in ordered]


def delete_lecture(db: Session, lecture_id: int, current_user: User) -> None:
    lec = _get_lecture_or_404(db, lecture_id)
    assert_instructor_assigned_to_course(db, current_user, lec.course_id)
    storage_key = lec.video_storage_key
    db.delete(lec)
    db.commit()
    delete_stored_file(storage_key)


async def upload_lecture_video(
    db: Session, lecture_id: int, file: UploadFile, current_user: User
) -> LectureOut:
    lec = _get_lecture_or_404(db, lecture_id)
    assert_instructor_assigned_to_course(db, current_user, lec.course_id)

    settings = get_settings()
    clean_name, storage_key, mime_type, file_size = await save_upload_file(
        file,
        category_dir=f"videos/course_{lec.course_id}",
        allowed_extensions=VIDEO_EXTENSIONS,
        max_size_mb=settings.MAX_VIDEO_SIZE_MB,
    )
    old_key = lec.video_storage_key
    lec.video_storage_key = storage_key
    lec.video_file_name = clean_name
    lec.video_mime_type = mime_type
    lec.video_file_size = file_size
    db.commit()
    db.refresh(lec)
    delete_stored_file(old_key)
    return _serialize_lecture(lec)


def download_lecture_video(db: Session, lecture_id: int, current_user: User) -> FileResponse:
    lec = _get_lecture_or_404(db, lecture_id)
    assert_can_access_course_content(db, current_user, lec.course_id)
    if get_user_role(current_user) == "student" and not lec.is_published:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="LECTURE_NOT_FOUND", message="Lecture not found.")
    if not lec.video_storage_key:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="VIDEO_NOT_FOUND", message="No uploaded video for this lecture.")
    path = resolve_storage_path(lec.video_storage_key)
    if not path.exists():
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_MISSING", message="Video file not found on storage.")
    return FileResponse(path=str(path), media_type=lec.video_mime_type or "video/mp4", filename=lec.video_file_name or "video.mp4")


def mark_lecture_completed(db: Session, lecture_id: int, current_user: User) -> LectureCompletionOut:
    lec = _get_lecture_or_404(db, lecture_id)
    assert_student_enrolled_in_course(db, current_user.id, lec.course_id)
    if not lec.is_published:
        raise AppException(status_code=status.HTTP_400_BAD_REQUEST, code="LECTURE_UNPUBLISHED", message="Cannot complete an unpublished lecture.")

    prog = db.execute(
        select(LectureProgress).where(
            LectureProgress.student_id == current_user.id,
            LectureProgress.lecture_id == lecture_id,
        )
    ).scalar_one_or_none()

    now = utcnow()
    if prog is None:
        prog = LectureProgress(
            student_id=current_user.id,
            lecture_id=lecture_id,
            is_completed=True,
            completed_at=now,
        )
        db.add(prog)
    else:
        prog.is_completed = True
        if prog.completed_at is None:
            prog.completed_at = now
    db.flush()

    course_prog = compute_course_progress(db, current_user.id, lec.course_id)
    db.commit()
    return LectureCompletionOut(
        lecture_id=lecture_id,
        student_id=current_user.id,
        is_completed=True,
        completed_at=prog.completed_at,
        course_completed=course_prog.is_course_completed,
    )


def list_materials(
    db: Session,
    course_id: int,
    module_id: Optional[int],
    lecture_id: Optional[int],
    current_user: User,
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    assert_can_access_course_content(db, current_user, course_id)
    stmt = select(StudyMaterial).where(StudyMaterial.course_id == course_id)
    if module_id is not None:
        stmt = stmt.where(StudyMaterial.module_id == module_id)
    if lecture_id is not None:
        stmt = stmt.where(StudyMaterial.lecture_id == lecture_id)

    stmt = apply_sorting(
        stmt,
        StudyMaterial,
        sort_by,
        sort_order,
        {"id": StudyMaterial.id, "title": StudyMaterial.title, "created_at": StudyMaterial.created_at},
        StudyMaterial.created_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=StudyMaterialOut.model_validate)


async def upload_study_material(
    db: Session,
    course_id: int,
    title: str,
    description: Optional[str],
    module_id: Optional[int],
    lecture_id: Optional[int],
    file: UploadFile,
    current_user: User,
) -> StudyMaterialOut:
    assert_instructor_assigned_to_course(db, current_user, course_id)
    course = db.execute(select(Course.id).where(Course.id == course_id, Course.is_deleted.is_(False))).scalar_one_or_none()
    if course is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="COURSE_NOT_FOUND", message="Course not found.")

    if module_id is not None:
        mod = db.execute(
            select(CourseModule.id).where(CourseModule.id == module_id, CourseModule.course_id == course_id)
        ).scalar_one_or_none()
        if mod is None:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="MODULE_NOT_FOUND", message="Module not found in course.")

    if lecture_id is not None:
        lec = db.execute(
            select(Lecture.id).where(Lecture.id == lecture_id, Lecture.course_id == course_id)
        ).scalar_one_or_none()
        if lec is None:
            raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="LECTURE_NOT_FOUND", message="Lecture not found in course.")

    settings = get_settings()
    clean_name, storage_key, mime_type, file_size = await save_upload_file(
        file,
        category_dir=f"materials/course_{course_id}",
        allowed_extensions=MATERIAL_EXTENSIONS,
        max_size_mb=settings.MAX_MATERIAL_SIZE_MB,
    )

    mat = StudyMaterial(
        course_id=course_id,
        module_id=module_id,
        lecture_id=lecture_id,
        title=title.strip(),
        description=description.strip() if description else None,
        file_name=clean_name,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.add(mat)
    db.flush()

    notify_course_students(
        db,
        course_id=course_id,
        title="New Study Material Uploaded",
        message=f"Study material '{mat.title}' is now available.",
        event_type="material_published",
        reference_type="study_material",
        reference_id=mat.id,
    )
    db.commit()
    db.refresh(mat)
    return StudyMaterialOut.model_validate(mat)


def download_study_material(db: Session, material_id: int, current_user: User) -> FileResponse:
    mat = db.execute(select(StudyMaterial).where(StudyMaterial.id == material_id)).scalar_one_or_none()
    if mat is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="MATERIAL_NOT_FOUND", message="Study material not found.")
    assert_can_access_course_content(db, current_user, mat.course_id)
    path = resolve_storage_path(mat.storage_key)
    if not path.exists():
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_MISSING", message="Material file not found on storage.")
    return FileResponse(path=str(path), media_type=mat.mime_type, filename=mat.file_name)


def delete_study_material(db: Session, material_id: int, current_user: User) -> None:
    mat = db.execute(select(StudyMaterial).where(StudyMaterial.id == material_id)).scalar_one_or_none()
    if mat is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="MATERIAL_NOT_FOUND", message="Study material not found.")
    assert_instructor_assigned_to_course(db, current_user, mat.course_id)
    key = mat.storage_key
    db.delete(mat)
    db.commit()
    delete_stored_file(key)
