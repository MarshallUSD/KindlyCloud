"""Child and related models."""
from enum import Enum

from sqlalchemy import Column, Date, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class ChildGender(str, Enum):
    """Supported child genders."""

    MALE = "male"
    FEMALE = "female"


class ChildStatus(str, Enum):
    """Child status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"


class Child(Base):
    """Child/Student model."""
    __tablename__ = "children"
    
    child_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    parent_phone = Column(String(20), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    birth_date = Column(Date, nullable=False)
    gender = Column(SQLEnum(ChildGender), nullable=True)
    notes = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    status = Column(SQLEnum(ChildStatus), default=ChildStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    parent_links = relationship("ParentChildLink", back_populates="child", cascade="all, delete-orphan")
    kindergarten = relationship("Kindergarten", back_populates="children")
    group = relationship("Group", back_populates="children")
    enrollments = relationship("Enrollment", back_populates="child", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="child", cascade="all, delete-orphan")
    feedback_for = relationship("Feedback", back_populates="for_child", foreign_keys="Feedback.child_id")
    payments = relationship("Payment", back_populates="child", foreign_keys="Payment.child_id")
    parent_submissions = relationship("ParentSubmission", back_populates="child", foreign_keys="ParentSubmission.child_id")
    notifications = relationship("Notification", back_populates="child")

    @property
    def id(self) -> str:
        """Compatibility alias used by Milestone 3 responses."""
        return self.child_id


class ParentChildLink(Base):
    """Junction table linking Parent to Child."""
    __tablename__ = "parent_child_links"
    
    link_id = Column(String, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False, index=True)
    status = Column(String(50), default="active", nullable=False)  # "active", "inactive", "removed"
    linked_at = Column(DateTime, default=utcnow, nullable=False)
    note = Column(Text, nullable=True)
    
    # Relationships
    parent = relationship("Parent", back_populates="child_links")
    child = relationship("Child", back_populates="parent_links")
