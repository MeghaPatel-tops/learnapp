import csv
import io
from datetime import datetime
from typing import Any, Iterable, List, Sequence

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import get_settings


def generate_certificate_pdf(
    student_name: str,
    course_name: str,
    completion_date: datetime,
    certificate_number: str,
    verification_code: str,
) -> bytes:
    """Generate a branded landscape PDF certificate and return raw PDF bytes."""
    settings = get_settings()
    buf = io.BytesIO()
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))

    # Border
    c.setStrokeColor(colors.HexColor("#1E3A8A"))
    c.setLineWidth(4)
    c.rect(28, 28, page_w - 56, page_h - 56)
    c.setStrokeColor(colors.HexColor("#0D9488"))
    c.setLineWidth(1.5)
    c.rect(38, 38, page_w - 76, page_h - 76)

    # Header branding
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(page_w / 2, page_h - 95, settings.INSTITUTE_NAME.upper())

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 11)
    c.drawCentredString(page_w / 2, page_h - 118, settings.INSTITUTE_TAGLINE)

    # Title
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(page_w / 2, page_h - 175, "CERTIFICATE OF COMPLETION")

    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawCentredString(page_w / 2, page_h - 220, "This is to proudly certify that")

    # Student Name
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor("#0D9488"))
    c.drawCentredString(page_w / 2, page_h - 265, student_name)

    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawCentredString(page_w / 2, page_h - 305, "has successfully completed all academic requirements for the course")

    # Course Name
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.drawCentredString(page_w / 2, page_h - 345, course_name)

    # Completion Date
    date_str = completion_date.strftime("%B %d, %Y")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawCentredString(page_w / 2, page_h - 388, f"Completed on {date_str}")

    # Footer metadata
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawString(64, 72, f"Certificate No: {certificate_number}")
    c.drawRightString(page_w - 64, 72, f"Verification Code: {verification_code}")

    c.showPage()
    c.save()
    return buf.getvalue()


def generate_receipt_pdf(
    receipt_number: str,
    student_name: str,
    student_email: str,
    course_name: str,
    total_fee: str,
    amount_paid: str,
    pending_amount: str,
    payment_method: str,
    status_label: str,
    payment_date: datetime,
    transaction_ref: str | None = None,
) -> bytes:
    """Generate a downloadable PDF fee payment receipt."""
    settings = get_settings()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"<b>{settings.INSTITUTE_NAME}</b>", styles["Title"]),
        Paragraph("Official Fee Payment Receipt", styles["Heading2"]),
        Spacer(1, 14),
    ]

    rows = [
        ["Receipt Number", receipt_number],
        ["Payment Date", payment_date.strftime("%Y-%m-%d %H:%M UTC")],
        ["Student Name", student_name],
        ["Student Email", student_email],
        ["Course", course_name],
        ["Payment Method", payment_method.replace("_", " ").title()],
        ["Transaction Reference", transaction_ref or "N/A"],
        ["Status", status_label.replace("_", " ").title()],
        ["Course Total Fee", f"${total_fee}"],
        ["Amount Paid (This Receipt)", f"${amount_paid}"],
        ["Remaining Pending Balance", f"${pending_amount}"],
    ]
    table = Table(rows, colWidths=[2.4 * inch, 4.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return buf.getvalue()


def export_csv_bytes(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> bytes:
    """Serialize tabular data as UTF-8 CSV bytes."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if val is None else str(val) for val in row])
    return buf.getvalue().encode("utf-8")


def export_xlsx_bytes(sheet_title: str, headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> bytes:
    """Serialize tabular data as an Excel (.xlsx) workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]
    ws.append(list(headers))
    for row in rows:
        ws.append([val if isinstance(val, (int, float)) else ("" if val is None else str(val)) for val in row])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_table_pdf_bytes(title: str, headers: Sequence[str], rows: List[Sequence[Any]]) -> bytes:
    """Render a printable landscape PDF table report."""
    settings = get_settings()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"<b>{settings.INSTITUTE_NAME} — {title}</b>", styles["Heading2"]),
        Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]),
        Spacer(1, 12),
    ]
    data = [list(headers)] + [["" if v is None else str(v) for v in r] for r in rows]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    return buf.getvalue()
