from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CourseStatus = Literal["draft", "published", "archived"]


class CourseModuleCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    sequence_order: int = Field(1, ge=1)


class CourseModuleUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    sequence_order: Optional[int] = Field(None, ge=1)


class CourseModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    sequence_order: int
    created_at: datetime
    updated_at: datetime


class CourseCreateRequest(BaseModel):
    course_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=5, max_length=5000)
    category: str = Field(..., min_length=2, max_length=100)
    duration_hours: int = Field(..., ge=1, le=5000)
    fee: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    status: CourseStatus = "draft"
    primary_instructor_id: Optional[int] = None
    instructor_ids: List[int] = Field(default_factory=list)


class CourseUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=5, max_length=5000)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    duration_hours: Optional[int] = Field(None, ge=1, le=5000)
    fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    status: Optional[CourseStatus] = None
    primary_instructor_id: Optional[int] = None


class AssignInstructorRequest(BaseModel):
    instructor_id: int


class CourseInstructorBrief(BaseModel):
    instructor_id: int
    user_id: int
    full_name: str
    employee_code: str


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_code: str
    name: str
    description: str
    category: str
    duration_hours: int
    fee: Decimal
    thumbnail_url: Optional[str] = None
    status: str
    primary_instructor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class CourseDetailOut(CourseOut):
    modules: List[CourseModuleOut] = []
    assigned_instructors: List[CourseInstructorBrief] = []
