"""Group/Class model."""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Integer, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


from app.core.base import Base
class Group(Base):
    """Group/Class model."""
    __tablename__ = "groups"
    
    group_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    group_name = Column(String(100), nullable=False, index=True)
    teacher_id = Column(String, ForeignKey("pedagogues.teacher_id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    schedule = Column(Text, nullable=True)  # JSON-encoded schedule
    max_capacity = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten = relationship("Kindergarten", back_populates="groups")
    teacher = relationship("Pedagogue", back_populates="groups")
    enrollments = relationship("Enrollment", back_populates="group", cascade="all, delete-orphan")
    group_menus = relationship("GroupMenu", back_populates="group", cascade="all, delete-orphan")
