"""Parent models."""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class Parent(Base):
    """Parent/Guardian model."""
    __tablename__ = "parents"
    
    parent_id = Column(String, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True, unique=True, index=True)
    address = Column(Text, nullable=True)
    birth_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent_user = relationship("ParentUser", back_populates="parent", cascade="all, delete-orphan")
    child_links = relationship("ParentChildLink", back_populates="parent", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="parent", foreign_keys="Payment.parent_id")
    feedback_from = relationship("Feedback", back_populates="from_parent", foreign_keys="Feedback.from_parent_id")


class ParentUser(Base):
    """Junction table linking Parent to User."""
    __tablename__ = "parent_users"
    
    parent_user_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, unique=True, index=True)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="parent_user")
    parent = relationship("Parent", back_populates="parent_user")
