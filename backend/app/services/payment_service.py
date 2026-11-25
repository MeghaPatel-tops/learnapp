"""Payment business logic – create payments, manage refunds, generate receipts."""

import uuid
from decimal import Decimal
from typing import Optional

from fastapi import status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.middleware.exceptions import AppException
from app.models.course import Course, Enrollment
from app.models.mixins import utcnow
from app.models.operations import Payment
from app.models.user import User
from app.schemas.payment import PaymentCreateRequest, PaymentOut, PaymentUpdateRequest
from app.services.authorization import get_user_role
from app.services.notification_service import create_notification
from app.utils.pagination import apply_sorting, paginate_query
from app.utils.pdf_export import generate_receipt_pdf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _receipt_number() -> str:
    now = utcnow()
    return f"REC-{now.year}-{uuid.uuid4().hex[:8].upper()}"


def _serialize(db: Session, pay: Payment) -> PaymentOut:
    student_name = db.execute(
        select(User.full_name).where(User.id == pay.student_id)
    ).scalar_one_or_none()
    course_name = db.execute(
        select(Course.name).where(Course.id == pay.course_id)
    ).scalar_one_or_none()

    total_paid = db.execute(
        select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
            Payment.enrollment_id == pay.enrollment_id,
            Payment.status.in_(["paid", "partially_paid"]),
        )
    ).scalar_one()
    pending = max(Decimal("0.00"), pay.total_fee - Decimal(str(total_paid)))

    return PaymentOut(
        id=pay.id,
        receipt_number=pay.receipt_number,
        student_id=pay.student_id,
        student_name=student_name,
        course_id=pay.course_id,
        course_name=course_name,
        enrollment_id=pay.enrollment_id,
        total_fee=pay.total_fee,
        amount_paid=pay.amount_paid,
        pending_amount=pending,
        payment_method=pay.payment_method,
        transaction_ref=pay.transaction_ref,
        status=pay.status,
        payment_date=pay.payment_date,
        notes=pay.notes,
        recorded_by=pay.recorded_by,
        created_at=pay.created_at,
        updated_at=pay.updated_at,
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_payment(
    db: Session, payload: PaymentCreateRequest, current_user: User
) -> PaymentOut:
    enrollment = db.execute(
        select(Enrollment).where(Enrollment.id == payload.enrollment_id)
    ).scalar_one_or_none()
    if enrollment is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ENROLLMENT_NOT_FOUND",
            message="Enrollment not found.",
        )

    course = db.execute(
        select(Course).where(Course.id == enrollment.course_id)
    ).scalar_one()

    # Total already paid for this enrollment
    already_paid = Decimal(
        str(
            db.execute(
                select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
                    Payment.enrollment_id == enrollment.id,
                    Payment.status.in_(["paid", "partially_paid"]),
                )
            ).scalar_one()
        )
    )
    remaining = course.fee - already_paid
    if payload.amount_paid > remaining:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="OVERPAYMENT",
            message=f"Amount exceeds the pending balance of {remaining:.2f}.",
        )

    new_total = already_paid + payload.amount_paid
    pay_status = "paid" if new_total >= course.fee else "partially_paid"

    pay = Payment(
        receipt_number=_receipt_number(),
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        enrollment_id=enrollment.id,
        total_fee=course.fee,
        amount_paid=payload.amount_paid,
        payment_method=payload.payment_method,
        transaction_ref=payload.transaction_ref,
        status=pay_status,
        payment_date=utcnow(),
        notes=payload.notes,
        recorded_by=current_user.id,
    )
    db.add(pay)
    db.flush()

    create_notification(
        db,
        user_id=enrollment.student_id,
        title="Payment Received",
        message=f"Payment of {payload.amount_paid:.2f} recorded for '{course.name}' (Receipt: {pay.receipt_number}).",
        event_type="payment_received",
        reference_type="payment",
        reference_id=pay.id,
    )

    db.commit()
    db.refresh(pay)
    return _serialize(db, pay)


def list_payments(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    enrollment_id: Optional[int],
    student_id: Optional[int],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    role = get_user_role(current_user)
    stmt = select(Payment)
    if role == "student":
        stmt = stmt.where(Payment.student_id == current_user.id)
    if enrollment_id is not None:
        stmt = stmt.where(Payment.enrollment_id == enrollment_id)
    if student_id is not None and role != "student":
        stmt = stmt.where(Payment.student_id == student_id)

    stmt = apply_sorting(
        stmt,
        Payment,
        sort_by,
        sort_order,
        {"id": Payment.id, "payment_date": Payment.payment_date, "amount_paid": Payment.amount_paid},
        Payment.payment_date,
    )
    return paginate_query(db, stmt, page, page_size, serializer=lambda p: _serialize(db, p))


def get_payment(db: Session, payment_id: int, current_user: User) -> PaymentOut:
    pay = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
    if pay is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="PAYMENT_NOT_FOUND", message="Payment not found.")
    role = get_user_role(current_user)
    if role == "student" and pay.student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")
    return _serialize(db, pay)


def update_payment(db: Session, payment_id: int, payload: PaymentUpdateRequest, current_user: User) -> PaymentOut:
    pay = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
    if pay is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="PAYMENT_NOT_FOUND", message="Payment not found.")

    pay.status = payload.status
    if payload.notes is not None:
        pay.notes = payload.notes
    db.commit()
    db.refresh(pay)
    return _serialize(db, pay)


def download_receipt(db: Session, payment_id: int, current_user: User) -> Response:
    pay = db.execute(select(Payment).where(Payment.id == payment_id)).scalar_one_or_none()
    if pay is None:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND, code="PAYMENT_NOT_FOUND", message="Payment not found.")

    role = get_user_role(current_user)
    if role == "student" and pay.student_id != current_user.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Access denied.")

    student_name = db.execute(select(User.full_name).where(User.id == pay.student_id)).scalar_one()
    student_email = db.execute(select(User.email).where(User.id == pay.student_id)).scalar_one()
    course_name = db.execute(select(Course.name).where(Course.id == pay.course_id)).scalar_one()

    already_paid = Decimal(
        str(
            db.execute(
                select(func.coalesce(func.sum(Payment.amount_paid), 0)).where(
                    Payment.enrollment_id == pay.enrollment_id,
                    Payment.status.in_(["paid", "partially_paid"]),
                )
            ).scalar_one()
        )
    )
    pending = max(Decimal("0.00"), pay.total_fee - already_paid)

    pdf_bytes = generate_receipt_pdf(
        receipt_number=pay.receipt_number,
        student_name=student_name,
        student_email=student_email,
        course_name=course_name,
        total_fee=str(pay.total_fee),
        amount_paid=str(pay.amount_paid),
        pending_amount=str(pending),
        payment_method=pay.payment_method,
        status_label=pay.status,
        payment_date=pay.payment_date,
        transaction_ref=pay.transaction_ref,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{pay.receipt_number}.pdf"'},
    )
