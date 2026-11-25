from typing import Callable, Tuple

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.exceptions import AppException
from app.models.user import User
from app.utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer JWT token, load user + role, and enforce active status."""
    if credentials is None or not credentials.credentials:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authentication credentials were not provided.",
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_TOKEN",
                message="Invalid authentication token.",
            )
        user_id = int(payload["sub"])
    except (jwt.ExpiredSignatureError):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="TOKEN_EXPIRED",
            message="Authentication token has expired.",
        )
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message="Invalid or malformed authentication token.",
        )

    user = db.execute(
        select(User)
        .options(
            joinedload(User.role),
            joinedload(User.instructor_profile),
            joinedload(User.student_profile),
        )
        .where(User.id == user_id)
    ).scalar_one_or_none()

    if user is None:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message="Authenticated user no longer exists.",
        )

    if not user.is_active:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ACCOUNT_INACTIVE",
            message="Your account is deactivated. Please contact an administrator.",
        )

    return user


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    """FastAPI dependency enforcing that current_user holds one of allowed_roles."""
    allowed_set: Tuple[str, ...] = allowed_roles

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name if current_user.role else ""
        if role_name not in allowed_set:
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="FORBIDDEN",
                message="You do not have permission to perform this action.",
            )
        return current_user

    return _checker
