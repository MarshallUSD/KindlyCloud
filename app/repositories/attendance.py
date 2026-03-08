"""Attendance repository for database operations."""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.attendance import Attendance
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    """Repository for Attendance model operations."""

    def __init__(self, db_session: Session):
        """Initialize attendance repository.
        
        Args:
            db_session: SQLAlchemy database session
        """
        super().__init__(Attendance, db_session)

    def get_by_enrollment_and_date(
        self, enrol_id: str, attend_date: date
    ) -> Optional[Attendance]:
        """Get attendance record by enrollment and date.
        
        Args:
            enrol_id: Enrollment ID
            attend_date: Attendance date
            
        Returns:
            Attendance record or None
        """
        return self.db_session.query(Attendance).filter(
            and_(
                Attendance.enrol_id == enrol_id,
                Attendance.attend_date == attend_date
            )
        ).first()

    def get_by_enrollment(
        self, enrol_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[List[Attendance], int]:
        """Get attendance records by enrollment.
        
        Args:
            enrol_id: Enrollment ID
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (attendance records, total count)
        """
        query = self.db_session.query(Attendance).filter(
            Attendance.enrol_id == enrol_id
        )
        total = query.count()
        records = query.offset(skip).limit(limit).all()
        return records, total

    def get_by_child(
        self, child_id: str, skip: int = 0, limit: int = 100
    ) -> tuple[List[Attendance], int]:
        """Get attendance records by child.
        
        Args:
            child_id: Child ID
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (attendance records, total count)
        """
        query = self.db_session.query(Attendance).filter(
            Attendance.child_id == child_id
        )
        total = query.count()
        records = query.offset(skip).limit(limit).all()
        return records, total
