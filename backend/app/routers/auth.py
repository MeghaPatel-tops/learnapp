from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.middleware.logging_mw import limiter
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    ProfileUpdateRequest,
    ResetPasswordRequest,
    UserCreateRequest,
    UserSummary,
)
from app.schemas.common import MessageResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password and receive a JWT access token."""
    return auth_service.authenticate_user(db, payload.email, payload.password)


@router.post("/register", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
):
    """Admin-only account registration endpoint."""
    user = auth_service.create_user_account(db, payload)
    return auth_service.serialize_user(user)


@router.post("/logout", response_model=MessageResponse)
def logout(_current_user: User = Depends(get_current_user)):
    """Acknowledge client-side JWT token disposal."""
    return MessageResponse(message="Logged out successfully.")


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_RESET)
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Initiate a password reset without revealing whether the email exists."""
    auth_service.request_password_reset(db, payload.email)
    return MessageResponse(
        message="If an active account exists for that email, reset instructions have been sent."
    )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_RESET)
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Complete a password reset using a valid, non-expired token."""
    auth_service.reset_password_with_token(db, payload.token, payload.new_password)
    return MessageResponse(message="Password has been reset successfully.")


@router.get("/me", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return auth_service.serialize_user(current_user)


@router.put("/me", response_model=UserSummary)
def update_me(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated user's own basic profile details."""
    updated = auth_service.update_own_profile(db, current_user, payload)
    return auth_service.serialize_user(updated)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the authenticated user's password after verifying current password."""
    auth_service.change_own_password(db, current_user, payload.current_password, payload.new_password)
    return MessageResponse(message="Password changed successfully.")
