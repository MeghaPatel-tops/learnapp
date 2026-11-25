from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.schemas.auth import (
    AdminResetPasswordRequest,
    RoleName,
    UserCreateRequest,
    UserSummary,
    UserUpdateRequest,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services import auth_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/users", tags=["Users (Admin)"])


@router.get("", response_model=PaginatedResponse[UserSummary])
def list_users(
    pagination: PaginationParams = Depends(),
    role: Optional[RoleName] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """List, search, and filter all user accounts (Admin only)."""
    return auth_service.list_users(
        db=db,
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        role=role,
        is_active=is_active,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.post("", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Create a new user account (Admin only)."""
    user = auth_service.create_user_account(db, payload)
    return auth_service.serialize_user(user)


@router.get("/{user_id}", response_model=UserSummary)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Get a user account by ID (Admin only)."""
    return auth_service.serialize_user(auth_service.get_user_by_id(db, user_id))


@router.put("/{user_id}", response_model=UserSummary)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Update a user's details, role, or activation status (Admin only)."""
    updated = auth_service.update_user_account(db, user_id, payload)
    return auth_service.serialize_user(updated)


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
def admin_reset_password(
    user_id: int,
    payload: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Reset a user's password (Admin only)."""
    auth_service.admin_reset_user_password(db, user_id, payload.new_password)
    return MessageResponse(message="User password reset successfully.")


@router.delete("/{user_id}", response_model=UserSummary)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Deactivate a user account (Admin only)."""
    user = auth_service.deactivate_user(db, user_id, admin.id)
    return auth_service.serialize_user(user)
