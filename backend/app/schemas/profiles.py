from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=30)
    student_code: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    guardian_name: Optional[str] = Field(None, max_length=120)
    guardian_phone: Optional[str] = Field(None, max_length=30)
    is_active: bool = True


class StudentUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    guardian_name: Optional[str] = Field(None, max_length=120)
    guardian_phone: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    student_profile_id: int
    student_code: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    is_active: bool
    created_at: datetime


class StudentDetailOut(StudentOut):
    enrollments: List[dict] = []
    batches: List[dict] = []
    attendance_percentage: float = 0.0


class InstructorCreateRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(None, max_length=30)
    employee_code: Optional[str] = Field(None, max_length=50)
    expertise: Optional[str] = Field(None, max_length=255)
    qualification: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    experience_years: int = Field(0, ge=0, le=70)
    is_active: bool = True


class InstructorUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    phone: Optional[str] = Field(None, max_length=30)
    expertise: Optional[str] = Field(None, max_length=255)
    qualification: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=2000)
    experience_years: Optional[int] = Field(None, ge=0, le=70)
    is_active: Optional[bool] = None


class InstructorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    instructor_profile_id: int
    employee_code: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    expertise: Optional[str] = None
    qualification: Optional[str] = None
    bio: Optional[str] = None
    experience_years: int
    is_active: bool
    created_at: datetime


class InstructorDetailOut(InstructorOut):
    assigned_courses: List[dict] = []
    assigned_batches: List[dict] = []
