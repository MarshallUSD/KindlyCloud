"""Feedback model."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


from app.core.base import Base


class FeedbackStatus(str, Enum):
    """Feedback status enumeration."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Feedback(Base):
    """Feedback from kindergarten or parent."""
    __tablename__ = "feedback"
    
    feedback_id = Column(String, primary_key=True, index=True)
    from_kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=True, index=True)
    from_parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=True, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.OPEN, nullable=False)
    handled_by_admin_user_id = Column(String, ForeignKey("users.user_id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    from_kindergarten = relationship("Kindergarten", back_populates="feedback_from", foreign_keys=[from_kindergarten_id])
    from_parent = relationship("Parent", back_populates="feedback_from", foreign_keys=[from_parent_id])
    for_child = relationship("Child", back_populates="feedback_for", foreign_keys=[child_id])
    handled_by_admin = relationship("User", back_populates="feedback_handled", foreign_keys=[handled_by_admin_user_id])
