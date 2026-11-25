from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Return current UTC time as a naive datetime compatible with MySQL DATETIME."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    """Standard created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )
