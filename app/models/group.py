"""Group/Class model."""
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Integer, Text, Float, Time
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


from app.core.base import Base
class Group(Base):
    """Group/Class model."""
    __tablename__ = "groups"
    
    group_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    group_name = Column(String(100), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    schedule = Column(Text, nullable=True)  # JSON-encoded schedule
    max_capacity = Column(Integer, nullable=True)
    age_from = Column(Integer, nullable=True)
    age_to = Column(Integer, nullable=True)
    room_number = Column(String(50), nullable=True)
    monthly_fee = Column(Float, nullable=True)
    active_time_start = Column(Time, nullable=True)
    active_time_end = Column(Time, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten = relationship("Kindergarten", back_populates="groups")
    pedagogue_links = relationship("PedagogueGroupLink", back_populates="group", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="group", cascade="all, delete-orphan")
    group_menus = relationship("GroupMenu", back_populates="group", cascade="all, delete-orphan")


class PedagogueGroupLink(Base):
    """Junction table linking Pedagogue to Group."""
    __tablename__ = "pedagogue_group_links"
    
    link_id = Column(String, primary_key=True, index=True)
    teacher_id = Column(String, ForeignKey("pedagogues.teacher_id"), nullable=False, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    role = Column(String(50), nullable=True) # e.g. "Main Teacher", "Assistant"
    
    # Relationships
    pedagogue = relationship("Pedagogue", back_populates="group_links")
    group = relationship("Group", back_populates="pedagogue_links")
