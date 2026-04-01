"""Attendance repository for database operations."""
from datetime import date
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for attendance records."""

    def __init__(self, db_session: Session):
        super().__init__(db_session, Attendance)

    def get_by_child_and_date(self, child_id: str, attend_date: date) -> Optional[Attendance]:
        """Get one attendance record for a child on a specific day."""
        return (
            self.db.query(Attendance)
            .filter(
                and_(
                    Attendance.child_id == child_id,
                    Attendance.attend_date == attend_date,
                )
            )
            .first()
        )

    def list_by_group_and_range(
        self,
        *,
        kindergarten_id: str,
        group_id: str,
        date_from: date,
        date_to: date,
    ) -> list[Attendance]:
        """List attendance records for one tenant group in a date range."""
        return (
            self.db.query(Attendance)
            .filter(
                Attendance.kindergarten_id == kindergarten_id,
                Attendance.group_id == group_id,
                Attendance.attend_date >= date_from,
                Attendance.attend_date <= date_to,
            )
            .order_by(Attendance.attend_date.desc(), Attendance.child_id.asc())
            .all()
        )
