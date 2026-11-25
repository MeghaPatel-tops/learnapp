"""Notifications router – user's own in-app notification inbox."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationOut
from app.services import notification_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", summary="List my notifications")
def list_notifications(
    is_read: Optional[bool] = None,
    paging: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notification_service.list_my_notifications(
        db,
        user_id=current_user.id,
        page=paging.page,
        page_size=paging.page_size,
        is_read=is_read,
        sort_by=paging.sort_by,
        sort_order=paging.sort_order,
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut, summary="Mark notification as read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notification_service.mark_notification_read(db, notification_id, current_user.id)


@router.post("/read-all", response_model=MessageResponse, summary="Mark all notifications as read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = notification_service.mark_all_notifications_read(db, current_user.id)
    return MessageResponse(message=f"{count} notification(s) marked as read.")
