"""Kindergarten models."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class Kindergarten(Base):
    """Kindergarten institution model."""
    __tablename__ = "kindergartens"
    
    kindergarten_id = Column(String, primary_key=True, index=True)
    kinder_name = Column(String(255), nullable=False, index=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    street = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True, unique=True, index=True)
    payment_token = Column(String, nullable=True)
    payment_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten_users = relationship("KindergartenUser", back_populates="kindergarten", cascade="all, delete-orphan")
    pedagogues = relationship("Pedagogue", back_populates="kindergarten", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="kindergarten", cascade="all, delete-orphan")
    menus = relationship("Menu", back_populates="kindergarten", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="target_kindergarten", foreign_keys="Post.target_kindergarten_id")
    feedback_from = relationship("Feedback", back_populates="from_kindergarten", foreign_keys="Feedback.from_kindergarten_id")


class KindergartenUser(Base):
    """Junction table for kindergarten staff/owners."""
    __tablename__ = "kindergarten_users"
    
    kindergarten_user_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    position = Column(String(100), nullable=True)  # e.g., "Director", "Staff"
    is_owner = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="kindergarten_users")
    kindergarten = relationship("Kindergarten", back_populates="kindergarten_users")
