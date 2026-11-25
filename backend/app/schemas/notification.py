from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AnnouncementRole = Literal["all", "admin", "instructor", "student"]


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    event_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=3, max_length=5000)
    target_role: Optional[AnnouncementRole] = "all"
    course_id: Optional[int] = None
    batch_id: Optional[int] = None


class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    target_role: Optional[str] = None
    course_id: Optional[int] = None
    batch_id: Optional[int] = None
    created_by: Optional[int] = None
    published_at: datetime
    created_at: datetime
