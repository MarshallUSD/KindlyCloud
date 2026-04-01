"""Payment reporting service."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.models.payment import PaymentStatus
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.payment import PaymentRepository
from app.schemas.payment import PaymentReportPeriod
from app.services.payment import PaymentService


class PaymentReportService:
    """Build tenant-scoped payment report exports."""

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.payment_service = PaymentService(db)

    def export_pdf(
        self,
        current_user: User,
        *,
        period: PaymentReportPeriod,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        group_id: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """Generate a PDF export for the current kindergarten tenant."""
        kindergarten = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kindergarten:
            raise ValidationException("Kindergarten not found for current user")

        self.payment_service._sync_overdue_for_kindergarten(kindergarten.kindergarten_id)
        range_start, range_end = self._resolve_period(period=period, from_date=from_date, to_date=to_date)
        records = self.payment_repo.report_records(
            kindergarten_id=kindergarten.kindergarten_id,
            from_date=range_start,
            to_date=range_end,
            group_id=group_id,
        )
        records = [self.payment_service._sync_status(record) for record in records]

        total_records = len(records)
        paid_records = [record for record in records if record.status == PaymentStatus.PAID]
        pending_records = [record for record in records if record.status == PaymentStatus.PENDING]
        overdue_records = [record for record in records if record.status == PaymentStatus.OVERDUE]

        lines = [
            "KindlyCloud Payment Report",
            f"Kindergarten: {kindergarten.kinder_name}",
            f"Report title: Payments {period.value.title()} Export",
            f"Selected range: {range_start.isoformat()} to {range_end.isoformat()}",
            f"Generated at: {datetime.now(UTC).isoformat(timespec='seconds')}",
            "",
            f"Total records: {total_records}",
            f"Total paid count: {len(paid_records)}",
            f"Total pending count: {len(pending_records)}",
            f"Total overdue count: {len(overdue_records)}",
            f"Total paid amount: {self._sum_amount(paid_records)}",
            f"Total pending amount: {self._sum_amount(pending_records)}",
            f"Total overdue amount: {self._sum_amount(overdue_records)}",
            "",
        ]

        if not records:
            lines.append("No payment data found for the selected range.")
        else:
            lines.append("Detailed records:")
            for record in records:
                lines.append(
                    " | ".join(
                        [
                            f"Child: {record.child_name or '-'}",
                            f"Group: {record.group_name or '-'}",
                            f"Billing: {record.billing_period}",
                            f"Amount: {record.amount}",
                            f"Due: {record.due_date.isoformat()}",
                            f"Status: {record.status.value}",
                            f"Paid at: {record.paid_at.isoformat(timespec='seconds') if record.paid_at else '-'}",
                        ]
                    )
                )

        pdf_bytes = self._build_simple_pdf(lines)
        filename = f"payments_{period.value}_{range_start.isoformat()}_{range_end.isoformat()}.pdf"
        return pdf_bytes, filename

    def _resolve_period(
        self,
        *,
        period: PaymentReportPeriod,
        from_date: Optional[date],
        to_date: Optional[date],
    ) -> tuple[date, date]:
        today = date.today()
        if period == PaymentReportPeriod.DAILY:
            return today, today
        if period == PaymentReportPeriod.WEEKLY:
            start = today - timedelta(days=today.weekday())
            return start, start + timedelta(days=6)
        if period == PaymentReportPeriod.MONTHLY:
            start = today.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1) - timedelta(days=1)
            else:
                end = start.replace(month=start.month + 1) - timedelta(days=1)
            return start, end
        if period == PaymentReportPeriod.CUSTOM:
            if not from_date or not to_date:
                raise ValidationException("from_date and to_date are required for custom reports")
            if from_date > to_date:
                raise ValidationException("from_date cannot be after to_date")
            return from_date, to_date
        raise ValidationException("Unsupported report period")

    def _sum_amount(self, records) -> str:
        total = sum((Decimal(str(record.amount)) for record in records), Decimal("0.00"))
        return f"{total:.2f}"

    def _build_simple_pdf(self, lines: list[str]) -> bytes:
        safe_lines = [self._pdf_escape(line)[:110] for line in lines]
        content_lines = ["BT", "/F1 10 Tf", "40 800 Td", "14 TL"]
        for index, line in enumerate(safe_lines):
            if index == 0:
                content_lines.append(f"({line}) Tj")
            else:
                content_lines.append("T*")
                content_lines.append(f"({line}) Tj")
        content_lines.append("ET")
        stream = "\n".join(content_lines).encode("latin-1", errors="replace")

        objects = [
            b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
            b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
            b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
            f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n",
        ]

        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for obj in objects:
            offsets.append(len(pdf))
            pdf.extend(obj)

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(offsets)}\n".encode("latin-1"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        pdf.extend(
            (
                f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF"
            ).encode("latin-1")
        )
        return bytes(pdf)

    def _pdf_escape(self, value: str) -> str:
        return (
            value.encode("latin-1", errors="replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        )
