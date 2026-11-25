from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.services import certificate_service
from app.services.certificate_service import (
    CertificateGenerateRequest,
    CertificateOut,
    CertificateVerifyOut,
)
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get("/verify/{code}", response_model=CertificateVerifyOut)
def verify_certificate(code: str, db: Session = Depends(get_db)):
    """Public certificate verification endpoint by verification_code or certificate_number."""
    return certificate_service.verify_certificate_public(db, code)


@router.get("", response_model=PaginatedResponse[CertificateOut])
def list_certificates(
    course_id: Optional[int] = Query(None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "student")),
):
    """List certificates (Student: own; Admin: all)."""
    return certificate_service.list_certificates(
        db=db,
        current_user=current_user,
        course_id=course_id,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("/generate", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
def generate_certificate(
    payload: CertificateGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "student")),
):
    """Generate a PDF certificate once course completion rules are met."""
    return certificate_service.generate_certificate(db, payload, current_user)


@router.get("/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "student")),
):
    """Download the generated PDF certificate."""
    return certificate_service.download_certificate_pdf(db, certificate_id, current_user)
