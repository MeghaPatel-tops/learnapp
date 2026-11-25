from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LectureCreateRequest(BaseModel):
    course_id: int
    module_id: int
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    sequence_order: int = Field(1, ge=1)
    video_url: Optional[str] = Field(None, max_length=500)
    duration_minutes: int = Field(0, ge=0, le=1000)
    is_published: bool = True


class LectureUpdateRequest(BaseModel):
    module_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    sequence_order: Optional[int] = Field(None, ge=1)
    video_url: Optional[str] = Field(None, max_length=500)
    duration_minutes: Optional[int] = Field(None, ge=0, le=1000)
    is_published: Optional[bool] = None


class LectureReorderRequest(BaseModel):
    course_id: int
    module_id: int
    lecture_ids: List[int] = Field(..., min_length=1)


class LectureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    module_id: int
    title: str
    description: Optional[str] = None
    sequence_order: int
    video_url: Optional[str] = None
    has_uploaded_video: bool = False
    video_file_name: Optional[str] = None
    video_file_size: Optional[int] = None
    duration_minutes: int
    is_published: bool
    is_completed: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class StudyMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    module_id: Optional[int] = None
    lecture_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    file_name: str
    mime_type: str
    file_size: int
    uploaded_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class LectureCompletionOut(BaseModel):
    lecture_id: int
    student_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    course_completed: bool = False
