"""Announcements router – admin/instructor publish, all roles browse."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.notification import AnnouncementCreateRequest, AnnouncementOut
from app.services import notification_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/announcements", tags=["Announcements"])


@router.post("", response_model=AnnouncementOut, status_code=201, summary="Create announcement")
def create_announcement(
    payload: AnnouncementCreateRequest,
    current_user: User = Depends(require_role("admin", "instructor")),
    db: Session = Depends(get_db),
):
    return notification_service.create_announcement(db, payload, current_user)


@router.get("", summary="List announcements")
def list_announcements(
    course_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    paging: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notification_service.list_announcements(
        db,
        current_user=current_user,
        page=paging.page,
        page_size=paging.page_size,
        course_id=course_id,
        batch_id=batch_id,
        sort_by=paging.sort_by,
        sort_order=paging.sort_order,
    )
