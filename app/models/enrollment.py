"""Enrollment model."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Numeric
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class EnrollmentStatus(str, Enum):
    """Enrollment status enumeration."""
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"


class Enrollment(Base):
    """Enrollment model linking child to group."""
    __tablename__ = "enrollments"
    
    enrol_id = Column(String, primary_key=True, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    enrol_date = Column(Date, nullable=False)
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False)
    total_fees = Column(Numeric(10, 2), nullable=True)
    amount_paid = Column(Numeric(10, 2), default=0, nullable=False)
    balance = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    child = relationship("Child", back_populates="enrollments")
    group = relationship("Group", back_populates="enrollments")
    attendance_records = relationship("Attendance", back_populates="enrollment", cascade="all, delete-orphan")
