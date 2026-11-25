import uuid
from datetime import timedelta
from typing import Optional

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.middleware.exceptions import AppException
from app.models.mixins import utcnow
from app.models.user import Instructor, PasswordResetToken, Role, Student, User
from app.schemas.auth import (
    LoginResponse,
    ProfileUpdateRequest,
    UserCreateRequest,
    UserSummary,
    UserUpdateRequest,
)
from app.utils.email_service import send_email_notification
from app.utils.pagination import apply_sorting, paginate_query
from app.utils.security import (
    create_access_token,
    generate_reset_token,
    hash_password,
    hash_token,
    validate_password_strength,
    verify_password,
)


def serialize_user(user: User) -> UserSummary:
    return UserSummary(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role.name if user.role else "",
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _validate_password_or_raise(password: str) -> None:
    err = validate_password_strength(password)
    if err:
        raise AppException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="WEAK_PASSWORD",
            message=err,
        )


def authenticate_user(db: Session, email: str, password: str) -> LoginResponse:
    """Verify credentials, reject inactive users, and return JWT LoginResponse."""
    normalized_email = email.strip().lower()
    user = db.execute(
        select(User).options(joinedload(User.role)).where(User.email == normalized_email)
    ).scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )

    if not user.is_active:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ACCOUNT_INACTIVE",
            message="Your account is deactivated. Please contact an administrator.",
        )

    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)

    settings = get_settings()
    token, _ = create_access_token(user_id=user.id, role=user.role.name)
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user=serialize_user(user),
    )


def _ensure_role_profile(db: Session, user: User, role_name: str, payload: Optional[UserCreateRequest] = None) -> None:
    """Create Student or Instructor extension profile if missing for that role."""
    if role_name == "student" and user.student_profile is None:
        code = (payload.student_code if payload and payload.student_code else f"STU-{uuid.uuid4().hex[:8].upper()}")
        student = Student(
            user_id=user.id,
            student_code=code,
            date_of_birth=payload.date_of_birth if payload else None,
            address=payload.address if payload else None,
            guardian_name=payload.guardian_name if payload else None,
            guardian_phone=payload.guardian_phone if payload else None,
        )
        db.add(student)
    elif role_name == "instructor" and user.instructor_profile is None:
        code = (payload.employee_code if payload and payload.employee_code else f"INS-{uuid.uuid4().hex[:8].upper()}")
        instructor = Instructor(
            user_id=user.id,
            employee_code=code,
            expertise=payload.expertise if payload else None,
            qualification=payload.qualification if payload else None,
            bio=payload.bio if payload else None,
            experience_years=(payload.experience_years if payload and payload.experience_years is not None else 0),
        )
        db.add(instructor)


def create_user_account(db: Session, payload: UserCreateRequest) -> User:
    """Create a user account (Admin-only operation) and associated role profile."""
    _validate_password_or_raise(payload.password)
    normalized_email = payload.email.strip().lower()

    existing = db.execute(select(User.id).where(User.email == normalized_email)).scalar_one_or_none()
    if existing is not None:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            code="EMAIL_EXISTS",
            message="An account with this email address already exists.",
        )

    role = db.execute(select(Role).where(Role.name == payload.role)).scalar_one_or_none()
    if role is None:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_ROLE",
            message=f"Role '{payload.role}' does not exist.",
        )

    user = User(
        role_id=role.id,
        full_name=payload.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(payload.password),
        phone=payload.phone.strip() if payload.phone else None,
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()

    _ensure_role_profile(db, user, role.name, payload)
    db.commit()

    return db.execute(
        select(User).options(joinedload(User.role)).where(User.id == user.id)
    ).scalar_one()


def list_users(
    db: Session,
    page: int,
    page_size: int,
    search: Optional[str],
    role: Optional[str],
    is_active: Optional[bool],
    sort_by: Optional[str],
    sort_order: str,
) -> dict:
    stmt = select(User).options(joinedload(User.role))
    if role:
        stmt = stmt.join(Role).where(Role.name == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))

    allowed_sorts = {
        "id": User.id,
        "full_name": User.full_name,
        "email": User.email,
        "created_at": User.created_at,
        "is_active": User.is_active,
    }
    stmt = apply_sorting(stmt, User, sort_by, sort_order, allowed_sorts, User.created_at)
    return paginate_query(db, stmt, page, page_size, serializer=serialize_user)


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.execute(
        select(User)
        .options(
            joinedload(User.role),
            joinedload(User.student_profile),
            joinedload(User.instructor_profile),
        )
        .where(User.id == user_id)
    ).scalar_one_or_none()
    if user is None:
        raise AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            code="USER_NOT_FOUND",
            message="User not found.",
        )
    return user


def update_user_account(db: Session, user_id: int, payload: UserUpdateRequest) -> User:
    user = get_user_by_id(db, user_id)

    if payload.email is not None:
        normalized_email = payload.email.strip().lower()
        if normalized_email != user.email:
            dup = db.execute(
                select(User.id).where(User.email == normalized_email, User.id != user_id)
            ).scalar_one_or_none()
            if dup is not None:
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    code="EMAIL_EXISTS",
                    message="Another user already uses this email address.",
                )
            user.email = normalized_email

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url.strip() or None
    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.role is not None and payload.role != user.role.name:
        new_role = db.execute(select(Role).where(Role.name == payload.role)).scalar_one_or_none()
        if new_role is None:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="INVALID_ROLE",
                message=f"Role '{payload.role}' does not exist.",
            )
        user.role_id = new_role.id
        db.flush()
        _ensure_role_profile(db, user, new_role.name)

    db.commit()
    return get_user_by_id(db, user_id)


def deactivate_user(db: Session, user_id: int, acting_admin_id: int) -> User:
    if user_id == acting_admin_id:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="CANNOT_DEACTIVATE_SELF",
            message="You cannot deactivate your own administrator account.",
        )
    user = get_user_by_id(db, user_id)
    user.is_active = False
    db.commit()
    return get_user_by_id(db, user_id)


def update_own_profile(db: Session, user: User, payload: ProfileUpdateRequest) -> User:
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url.strip() or None
    db.commit()
    return get_user_by_id(db, user.id)


def change_own_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_CURRENT_PASSWORD",
            message="Current password is incorrect.",
        )
    _validate_password_or_raise(new_password)
    user.password_hash = hash_password(new_password)
    db.commit()


def admin_reset_user_password(db: Session, user_id: int, new_password: str) -> None:
    user = get_user_by_id(db, user_id)
    _validate_password_or_raise(new_password)
    user.password_hash = hash_password(new_password)
    db.commit()


def request_password_reset(db: Session, email: str) -> Optional[str]:
    """
    Create a short-lived password reset token if the active account exists.
    Returns None in HTTP handler; email is dispatched via configured SMTP service.
    """
    normalized_email = email.strip().lower()
    user = db.execute(select(User).where(User.email == normalized_email)).scalar_one_or_none()
    if user is None or not user.is_active:
        return None

    raw_token, digest = generate_reset_token()
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=digest,
        expires_at=utcnow() + timedelta(minutes=30),
    )
    db.add(reset_record)
    db.commit()

    settings = get_settings()
    reset_link = f"{settings.FRONTEND_RESET_URL}?token={raw_token}"
    send_email_notification(
        to_email=user.email,
        subject="LMS Password Reset Request",
        body=(
            f"Hello {user.full_name},\n\n"
            f"Use the following link within 30 minutes to reset your password:\n"
            f"{reset_link}\n"
        ),
    )
    return raw_token


def reset_password_with_token(db: Session, raw_token: str, new_password: str) -> None:
    _validate_password_or_raise(new_password)
    digest = hash_token(raw_token)
    record = db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == digest)
    ).scalar_one_or_none()

    now = utcnow()
    if record is None or record.used_at is not None or record.expires_at < now:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_OR_EXPIRED_TOKEN",
            message="Password reset token is invalid or has expired.",
        )

    user = get_user_by_id(db, record.user_id)
    if not user.is_active:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ACCOUNT_INACTIVE",
            message="Account is deactivated.",
        )

    user.password_hash = hash_password(new_password)
    record.used_at = now
    db.commit()
