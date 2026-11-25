from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AttendanceStatus = Literal["present", "absent", "cancelled", "holiday", "approved_leave"]


class AttendanceEntryInput(BaseModel):
    student_id: int
    status: AttendanceStatus
    remarks: Optional[str] = Field(None, max_length=255)


class AttendanceBulkMarkRequest(BaseModel):
    batch_id: int
    session_date: date
    records: List[AttendanceEntryInput] = Field(..., min_length=1)


class AttendanceUpdateRequest(BaseModel):
    status: AttendanceStatus
    remarks: Optional[str] = Field(None, max_length=255)
    reason: str = Field(..., min_length=2, max_length=255)


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    student_id: int
    student_name: Optional[str] = None
    session_date: date
    status: str
    remarks: Optional[str] = None
    marked_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class AttendanceAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attendance_id: int
    old_status: str
    new_status: str
    changed_by: Optional[int] = None
    reason: Optional[str] = None
    changed_at: datetime


class MonthlyAttendanceSummary(BaseModel):
    month: str
    present: int
    absent: int
    cancelled: int
    holiday: int
    approved_leave: int
    eligible_classes: int
    attendance_percentage: float


class AttendanceSummaryOut(BaseModel):
    student_id: int
    batch_id: Optional[int] = None
    present: int
    absent: int
    cancelled: int
    holiday: int
    approved_leave: int
    eligible_classes: int
    attendance_percentage: float
    monthly_breakdown: List[MonthlyAttendanceSummary] = []
