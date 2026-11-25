from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreateRequest(BaseModel):
    course_id: int
    batch_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=200)
    instructions: str = Field(..., min_length=3, max_length=10000)
    max_marks: Decimal = Field(..., gt=Decimal("0.00"), le=Decimal("1000.00"))
    passing_marks: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), le=Decimal("1000.00"))
    due_date: datetime
    allow_late: bool = True


class AssignmentUpdateRequest(BaseModel):
    batch_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    instructions: Optional[str] = Field(None, min_length=3, max_length=10000)
    max_marks: Optional[Decimal] = Field(None, gt=Decimal("0.00"), le=Decimal("1000.00"))
    passing_marks: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("1000.00"))
    due_date: Optional[datetime] = None
    allow_late: Optional[bool] = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    batch_id: Optional[int] = None
    title: str
    instructions: str
    attachment_name: Optional[str] = None
    attachment_mime: Optional[str] = None
    attachment_size: Optional[int] = None
    max_marks: Decimal
    passing_marks: Decimal
    due_date: datetime
    allow_late: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    evaluator_id: Optional[int] = None
    marks_obtained: Decimal
    feedback_text: Optional[str] = None
    evaluated_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    student_id: int
    student_name: Optional[str] = None
    version: int
    submission_text: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    is_late: bool
    submitted_at: datetime
    feedback: Optional[FeedbackOut] = None


class EvaluateSubmissionRequest(BaseModel):
    marks_obtained: Decimal = Field(..., ge=Decimal("0.00"))
    feedback_text: Optional[str] = Field(None, max_length=5000)


class SubmissionStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(under_review)$")
