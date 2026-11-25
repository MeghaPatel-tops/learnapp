"""Payments router – record, list, update payments and download receipts."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.payment import PaymentCreateRequest, PaymentOut, PaymentUpdateRequest
from app.services import payment_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("", response_model=PaymentOut, status_code=201, summary="Record a payment")
def create_payment(
    payload: PaymentCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return payment_service.create_payment(db, payload, current_user)


@router.get("", summary="List payments")
def list_payments(
    enrollment_id: Optional[int] = None,
    student_id: Optional[int] = None,
    paging: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payment_service.list_payments(
        db,
        current_user=current_user,
        page=paging.page,
        page_size=paging.page_size,
        enrollment_id=enrollment_id,
        student_id=student_id,
        sort_by=paging.sort_by,
        sort_order=paging.sort_order,
    )


@router.get("/{payment_id}", response_model=PaymentOut, summary="Get payment details")
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payment_service.get_payment(db, payment_id, current_user)


@router.put("/{payment_id}", response_model=PaymentOut, summary="Update payment status")
def update_payment(
    payment_id: int,
    payload: PaymentUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return payment_service.update_payment(db, payment_id, payload, current_user)


@router.get("/{payment_id}/receipt", summary="Download receipt PDF")
def download_receipt(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return payment_service.download_receipt(db, payment_id, current_user)
