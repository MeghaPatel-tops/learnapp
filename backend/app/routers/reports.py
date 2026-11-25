"""Reports router – tabular data export (CSV / XLSX / PDF)."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User
from app.services import report_service
from app.utils.pdf_export import export_csv_bytes, export_table_pdf_bytes, export_xlsx_bytes

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get(
    "/{report_type}",
    summary="Export report (students, enrollments, payments, attendance, course-progress)",
)
def export_report(
    report_type: str,
    format: Literal["csv", "xlsx", "pdf"] = "csv",
    course_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    current_user: User = Depends(require_role("admin", "instructor")),
    db: Session = Depends(get_db),
):
    title, headers, rows = report_service.get_report_data(db, report_type, course_id, batch_id)

    if format == "csv":
        content = export_csv_bytes(headers, rows)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.csv"'},
        )
    elif format == "xlsx":
        content = export_xlsx_bytes(title, headers, rows)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.xlsx"'},
        )
    else:
        content = export_table_pdf_bytes(title, headers, rows)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{report_type}.pdf"'},
        )
