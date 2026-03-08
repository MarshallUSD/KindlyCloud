"""Attendance model."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class AttendanceStatus(str, Enum):
    """Attendance status enumeration."""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class Attendance(Base):
    """Daily attendance record."""
    __tablename__ = "attendance"
    
    attendance_id = Column(String, primary_key=True, index=True)
    enrol_id = Column(String, ForeignKey("enrollments.enrol_id"), nullable=False, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False, index=True)  # Denormalized for convenience
    attend_date = Column(Date, nullable=False)
    status = Column(SQLEnum(AttendanceStatus), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="attendance_records")
    child = relationship("Child", back_populates="attendance_records")
