"""Pedagogue/Teacher model."""
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.base import Base


class Pedagogue(Base):
    """Teacher/Pedagogue model."""
    __tablename__ = "pedagogues"
    
    teacher_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=True, index=True)
    full_name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    experience_year = Column(Integer, nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, unique=True, index=True)
    hire_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten = relationship("Kindergarten", back_populates="pedagogues")
    group = relationship("Group", back_populates="teachers")
    group_links = relationship("PedagogueGroupLink", back_populates="pedagogue", cascade="all, delete-orphan")
