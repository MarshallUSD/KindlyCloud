"""Notification model."""
from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow

class Notification(Base):
    """User notification."""
    __tablename__ = "notifications"
    
    notification_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    notif_type = Column(String(50), nullable=False)  # "enrollment", "payment", "attendance", etc.
    payload = Column(JSON, nullable=True)  # Additional data for the notification
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

    @property
    def is_read(self) -> bool:
        """Expose a boolean read flag for API responses."""
        return self.read_at is not None
