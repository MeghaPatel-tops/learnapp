from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

BatchStatus = Literal["upcoming", "active", "closed", "archived"]
EnrollmentStatus = Literal["active", "completed", "dropped"]


class BatchCreateRequest(BaseModel):
    batch_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    course_id: int
    instructor_id: int
    start_date: date
    end_date: date
    class_days: str = Field(..., min_length=2, max_length=100)
    class_timing: str = Field(..., min_length=2, max_length=100)
    capacity: int = Field(..., ge=1, le=1000)
    status: BatchStatus = "upcoming"

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be greater than or equal to start_date.")
        return self


class BatchUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    instructor_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    class_days: Optional[str] = Field(None, min_length=2, max_length=100)
    class_timing: Optional[str] = Field(None, min_length=2, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=1000)
    status: Optional[BatchStatus] = None


class BatchStudentAddRequest(BaseModel):
    student_id: int


class BatchRosterItem(BaseModel):
    student_id: int
    full_name: str
    email: str
    student_code: str
    status: str
    joined_at: datetime


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_code: str
    name: str
    course_id: int
    course_name: Optional[str] = None
    instructor_id: int
    instructor_name: Optional[str] = None
    start_date: date
    end_date: date
    class_days: str
    class_timing: str
    capacity: int
    enrolled_count: int = 0
    status: str
    created_at: datetime
    updated_at: datetime


class BatchDetailOut(BatchOut):
    roster: List[BatchRosterItem] = []


class EnrollmentCreateRequest(BaseModel):
    student_id: int
    course_id: int


class EnrollmentUpdateRequest(BaseModel):
    status: EnrollmentStatus


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: Optional[str] = None
    course_id: int
    course_name: Optional[str] = None
    status: str
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime
