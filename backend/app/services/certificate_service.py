import uuid
from datetime import datetime
from typing import Optional

from fastapi import status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Course, Enrollment
from app.models.mixins import utcnow
from app.models.operations import Certificate
from app.models.user import User
from app.services.authorization import get_user_role
from app.services.notification_service import create_notification
from app.services.progress_service import compute_course_progress
from app.utils.file_storage import resolve_storage_path, save_bytes
from app.utils.pagination import apply_sorting, paginate_query
from app.utils.pdf_export import generate_certificate_pdf


class CertificateGenerateRequest(BaseModel):
    course_id: int
    student_id: Optional[int] = None


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    certificate_number: str
    verification_code: str
    student_id: int
    student_name: Optional[str] = None
    course_id: int
    course_name: Optional[str] = None
    enrollment_id: int
    issued_at: datetime
    created_at: datetime


class CertificateVerifyOut(BaseModel):
    valid: bool
    certificate_number: str
    verification_code: str
    student_name: str
    course_name: str
    issued_at: datetime


def _serialize_certificate(db: Session, cert: Certificate) -> CertificateOut:
    student_name = db.execute(select(User.full_name).where(User.id == cert.student_id)).scalar_one_or_none()
    course_name = db.execute(select(Course.name).where(Course.id == cert.course_id)).scalar_one_or_none()
    return CertificateOut(
        id=cert.id,
        certificate_number=cert.certificate_number,
        verification_code=cert.verification_code,
        student_id=cert.student_id,
        student_name=student_name,
        course_id=cert.course_id,
        course_name=course_name,
        enrollment_id=cert.enrollment_id,
        issued_at=cert.issued_at,
        created_at=cert.created_at,
    )


def generate_certificate(
    db: Session, payload: CertificateGenerateRequest, current_user: User
) -> CertificateOut:
    role = get_user_role(current_user)
    if role == "student":
        if payload.student_id is not None and payload.student_id != current_user.id:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="Students can only generate their own certificates.",
            )
        target_student_id = current_user.id
    elif role == "admin":
        if payload.student_id is None:
            raise AppException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                code="STUDENT_ID_REQUIRED",
                message="student_id is required when an admin generates a certificate.",
            )
        target_student_id = payload.student_id
    else:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message="Only admins or eligible students can generate certificates.",
        )

    existing = db.execute(
        select(Certificate).where(
            Certificate.student_id == target_student_id,
            Certificate.course_id == payload.course_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="CERTIFICATE_ALREADY_ISSUED",
            message="A certificate has already been issued for this student and course.",
        )

    progress = compute_course_progress(db, target_student_id, payload.course_id)
    if not progress.is_course_completed:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="COURSE_NOT_COMPLETED",
            message="Course completion requirements (100% lectures and all assignments/quizzes passed) are not yet met.",
        )

    enrollment = db.execute(
        select(Enrollment).where(
            Enrollment.student_id == target_student_id,
            Enrollment.course_id == payload.course_id,
        )
    ).scalar_one()
    student_user = db.execute(select(User).where(User.id == target_student_id)).scalar_one()
    course = db.execute(select(Course).where(Course.id == payload.course_id)).scalar_one()

    now = utcnow()
    cert_number = f"CERT-{now.year}-{uuid.uuid4().hex[:6].upper()}"
    verif_code = uuid.uuid4().hex[:12].upper()

    pdf_bytes = generate_certificate_pdf(
        student_name=student_user.full_name,
        course_name=course.name,
        completion_date=enrollment.completed_at or now,
        certificate_number=cert_number,
        verification_code=verif_code,
    )
    storage_key = f"certificates/{cert_number}.pdf"
    save_bytes(storage_key, pdf_bytes)

    cert = Certificate(
        certificate_number=cert_number,
        verification_code=verif_code,
        student_id=target_student_id,
        course_id=payload.course_id,
        enrollment_id=enrollment.id,
        issued_at=now,
        pdf_storage_key=storage_key,
    )
    db.add(cert)
    db.flush()

    create_notification(
        db,
        user_id=target_student_id,
        title="Certificate Issued",
        message=f"Congratulations! Your certificate ({cert_number}) for '{course.name}' is ready to download.",
        event_type="certificate_issued",
        reference_type="certificate",
        reference_id=cert.id,
    )
    db.commit()
    db.refresh(cert)
    return _serialize_certificate(db, cert)


def list_certificates(
    db: Session,
    current_user: User,
    course_id: Optional[int],
    page: int,
    page_size: int,
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Certificate)
    if role == "student":
        stmt = stmt.where(Certificate.student_id == current_user.id)
    if course_id is not None:
        stmt = stmt.where(Certificate.course_id == course_id)

    stmt = apply_sorting(
        stmt,
        Certificate,
        sort_by,
        sort_order,
        {"id": Certificate.id, "issued_at": Certificate.issued_at},
        Certificate.issued_at,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda c: _serialize_certificate(db, c))


def download_certificate_pdf(db: Session, certificate_id: int, current_user: User) -> FileResponse:
    cert = db.execute(select(Certificate).where(Certificate.id == certificate_id)).scalar_one_or_none()
    if cert is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="CERTIFICATE_NOT_FOUND", message="Certificate not found.")

    role = get_user_role(current_user)
    if role == "student" and cert.student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="You cannot download another student's certificate.")
    if role == "instructor":
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")

    if not cert.pdf_storage_key:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_MISSING", message="Certificate PDF not found.")
    path = resolve_storage_path(cert.pdf_storage_key)
    if not path.exists():
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="FILE_MISSING", message="Certificate PDF file missing on disk.")
    return FileResponse(path=str(path), media_type="application/pdf", filename=f"{cert.certificate_number}.pdf")


def verify_certificate_public(db: Session, code: str) -> CertificateVerifyOut:
    cleaned = code.strip().upper()
    cert = db.execute(
        select(Certificate).where(
            (Certificate.verification_code == cleaned) | (Certificate.certificate_number == cleaned)
        )
    ).scalar_one_or_none()
    if cert is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="CERTIFICATE_NOT_FOUND", message="No valid certificate matches the provided code.")

    student_name = db.execute(select(User.full_name).where(User.id == cert.student_id)).scalar_one()
    course_name = db.execute(select(Course.name).where(Course.id == cert.course_id)).scalar_one()
    return CertificateVerifyOut(
        valid=True,
        certificate_number=cert.certificate_number,
        verification_code=cert.verification_code,
        student_name=student_name,
        course_name=course_name,
        issued_at=cert.issued_at,
    )
