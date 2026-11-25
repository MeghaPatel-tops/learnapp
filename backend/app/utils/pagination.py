import math
from typing import Any, Callable, List, Optional, Tuple, Type

from fastapi import Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session


class PaginationParams:
    """Reusable pagination and sorting query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        search: Optional[str] = Query(None, max_length=200, description="Search term"),
        sort_by: Optional[str] = Query(None, max_length=50, description="Sort column"),
        sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.search = search.strip() if search and search.strip() else None
        self.sort_by = sort_by
        self.sort_order = sort_order


def paginate_query(
    db: Session,
    stmt,
    page: int,
    page_size: int,
    serializer: Optional[Callable[[Any], Any]] = None,
) -> dict:
    """Execute a SQLAlchemy select statement with pagination and return envelope dict."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.execute(count_stmt).scalar_one()
    offset = (page - 1) * page_size
    rows = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()
    items = [serializer(row) for row in rows] if serializer else list(rows)
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def apply_sorting(
    stmt,
    model: Type[Any],
    sort_by: Optional[str],
    sort_order: str,
    allowed_fields: dict,
    default_col: Any,
):
    """Apply safe column sorting from an allowlisted field mapping."""
    col = allowed_fields.get(sort_by) if sort_by else default_col
    if col is None:
        col = default_col
    return stmt.order_by(asc(col) if sort_order == "asc" else desc(col))
