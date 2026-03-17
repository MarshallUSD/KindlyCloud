"""Post/Announcement model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class Post(Base):
    """Admin post/announcement."""
    __tablename__ = "posts"
    
    post_id = Column(String, primary_key=True, index=True)
    created_by_admin_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    body = Column(Text, nullable=False)
    target_kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=True)  # NULL means broadcast to all
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    creator = relationship("User", back_populates="posts", foreign_keys=[created_by_admin_user_id])
    target_kindergarten = relationship("Kindergarten", back_populates="posts", foreign_keys=[target_kindergarten_id])
