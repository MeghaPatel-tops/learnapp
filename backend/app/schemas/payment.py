"""Pydantic schemas for the Payment module."""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

PaymentMethodType = Literal["cash", "card", "bank_transfer", "upi", "online", "other"]
PaymentStatusType = Literal["paid", "partially_paid", "pending", "failed", "refunded"]


class PaymentCreateRequest(BaseModel):
    enrollment_id: int
    amount_paid: Decimal = Field(..., gt=0, decimal_places=2)
    payment_method: PaymentMethodType
    transaction_ref: Optional[str] = Field(None, max_length=120)
    notes: Optional[str] = Field(None, max_length=500)


class PaymentUpdateRequest(BaseModel):
    status: PaymentStatusType
    notes: Optional[str] = Field(None, max_length=500)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    student_id: int
    student_name: Optional[str] = None
    course_id: int
    course_name: Optional[str] = None
    enrollment_id: int
    total_fee: Decimal
    amount_paid: Decimal
    pending_amount: Decimal = Decimal("0.00")
    payment_method: str
    transaction_ref: Optional[str] = None
    status: str
    payment_date: datetime
    notes: Optional[str] = None
    recorded_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
