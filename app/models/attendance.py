"""Attendance model."""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.base import Base


class AttendanceStatus(str, Enum):
    """Supported daily attendance statuses."""

    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"


class Attendance(Base):
    """Daily attendance record for one child."""

    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("child_id", "attend_date", name="uq_attendance_child_date"),
    )

    attendance_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    attend_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    marked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Legacy fields kept nullable for compatibility with older installations.
    enrol_id = Column(String, ForeignKey("enrollments.enrol_id"), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    enrollment = relationship("Enrollment", back_populates="attendance_records")
    child = relationship("Child", back_populates="attendance_records")

    @property
    def id(self) -> str:
        """Compatibility alias used by newer API responses."""
        return self.attendance_id

    @property
    def date(self):
        """Compatibility alias for the attendance day."""
        return self.attend_date

    @date.setter
    def date(self, value) -> None:
        self.attend_date = value
