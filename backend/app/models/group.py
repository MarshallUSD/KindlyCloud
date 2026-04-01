"""Group/Class model."""
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class Group(Base):
    """Group/Class model."""
    __tablename__ = "groups"
    
    group_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    group_name = Column(String(100), nullable=False, index=True)
    teacher_id = Column(String, nullable=True, index=True)
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
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationships
    kindergarten = relationship("Kindergarten", back_populates="groups")
    children = relationship("Child", back_populates="group")
    teachers = relationship("Pedagogue", back_populates="group")
    pedagogue_links = relationship("PedagogueGroupLink", back_populates="group", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="group", cascade="all, delete-orphan")
    group_menus = relationship("GroupMenu", back_populates="group", cascade="all, delete-orphan")

    @property
    def id(self) -> str:
        """Compatibility alias for REST responses."""
        return self.group_id

    @property
    def name(self) -> str:
        """Compatibility alias for REST responses."""
        return self.group_name

    @name.setter
    def name(self, value: str) -> None:
        self.group_name = value

    @property
    def capacity(self) -> int | None:
        """Compatibility alias for REST responses."""
        return self.max_capacity

    @capacity.setter
    def capacity(self, value: int | None) -> None:
        self.max_capacity = value

    @property
    def schedule_from(self):
        """Compatibility alias for REST responses."""
        return self.active_time_start

    @schedule_from.setter
    def schedule_from(self, value) -> None:
        self.active_time_start = value

    @property
    def schedule_to(self):
        """Compatibility alias for REST responses."""
        return self.active_time_end

    @schedule_to.setter
    def schedule_to(self, value) -> None:
        self.active_time_end = value


class PedagogueGroupLink(Base):
    """Junction table linking Pedagogue to Group."""
    __tablename__ = "pedagogue_group_links"
    
    link_id = Column(String, primary_key=True, index=True)
    teacher_id = Column(String, ForeignKey("pedagogues.teacher_id"), nullable=False, index=True)
    group_id = Column(String, ForeignKey("groups.group_id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=utcnow, nullable=False)
    role = Column(String(50), nullable=True) # e.g. "Main Teacher", "Assistant"
    
    # Relationships
    pedagogue = relationship("Pedagogue", back_populates="group_links")
    group = relationship("Group", back_populates="pedagogue_links")
