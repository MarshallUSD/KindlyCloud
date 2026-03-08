"""Pedagogue/Teacher model."""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class Pedagogue(Base):
    """Teacher/Pedagogue model."""
    __tablename__ = "pedagogues"
    
    teacher_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, unique=True, index=True)
    hire_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten = relationship("Kindergarten", back_populates="pedagogues")
    groups = relationship("Group", back_populates="teacher")
