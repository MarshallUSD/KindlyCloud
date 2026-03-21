"""Child and related models."""
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.base import Base


class ChildStatus(str, Enum):
    """Child status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"


class Child(Base):
    """Child/Student model."""
    __tablename__ = "children"
    
    child_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(String(10), nullable=True)  # "male", "female", "other"
    address = Column(Text, nullable=True)
    status = Column(SQLEnum(ChildStatus), default=ChildStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent_links = relationship("ParentChildLink", back_populates="child", cascade="all, delete-orphan")
    kindergarten = relationship("Kindergarten")
    enrollments = relationship("Enrollment", back_populates="child", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="child", cascade="all, delete-orphan")
    feedback_for = relationship("Feedback", back_populates="for_child", foreign_keys="Feedback.child_id")
    payments = relationship("Payment", back_populates="child", foreign_keys="Payment.child_id")


class ParentChildLink(Base):
    """Junction table linking Parent to Child."""
    __tablename__ = "parent_child_links"
    
    link_id = Column(String, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False)  # "active", "inactive", "removed"
    linked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    note = Column(Text, nullable=True)
    
    # Relationships
    parent = relationship("Parent", back_populates="child_links")
    child = relationship("Child", back_populates="parent_links")
