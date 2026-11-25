from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User
from app.schemas.attendance import (
    AttendanceAuditOut,
    AttendanceBulkMarkRequest,
    AttendanceOut,
    AttendanceStatus,
    AttendanceSummaryOut,
    AttendanceUpdateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services import attendance_service
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.get("", response_model=PaginatedResponse[AttendanceOut])
def list_attendance(
    batch_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status_filter: Optional[AttendanceStatus] = Query(None, alias="status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List attendance records scoped by role."""
    return attendance_service.list_attendance(
        db=db,
        current_user=current_user,
        batch_id=batch_id,
        student_id=student_id,
        date_from=date_from,
        date_to=date_to,
        status_filter=status_filter,
        page=pagination.page,
        page_size=pagination.page_size,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )


@router.get("/summary", response_model=AttendanceSummaryOut)
def get_attendance_summary(
    student_id: Optional[int] = Query(None),
    batch_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get monthly attendance summary and percentage (excluding cancelled, holiday, approved_leave)."""
    return attendance_service.get_attendance_summary(db, current_user, student_id, batch_id)


@router.post("", response_model=List[AttendanceOut], status_code=status.HTTP_201_CREATED)
def mark_attendance(
    payload: AttendanceBulkMarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Record attendance for a batch and session date (Admin or assigned Instructor)."""
    return attendance_service.mark_attendance(db, payload, current_user)


@router.put("/{attendance_id}", response_model=AttendanceOut)
def update_attendance(
    attendance_id: int,
    payload: AttendanceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """Update an attendance record and write an audit trail entry."""
    return attendance_service.update_attendance(db, attendance_id, payload, current_user)


@router.get("/{attendance_id}/audit", response_model=List[AttendanceAuditOut])
def get_attendance_audit(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "instructor")),
):
    """View the audit trail for an attendance record."""
    return attendance_service.get_attendance_audit(db, attendance_id, current_user)
