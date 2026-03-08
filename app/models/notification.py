"""Notification model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.base import Base
from sqlalchemy.dialects.postgresql import UUID

user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

class Notification(Base):
    """User notification."""
    __tablename__ = "notifications"
    
    notification_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, index=True)
    notif_type = Column(String(50), nullable=False)  # "enrollment", "payment", "attendance", etc.
    payload = Column(JSON, nullable=True)  # Additional data for the notification
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
