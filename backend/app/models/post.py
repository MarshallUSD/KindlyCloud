"""Post/Announcement model."""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class Post(Base):
    """Admin post/announcement."""
    __tablename__ = "posts"
    
    post_id = Column(String, primary_key=True, index=True)
    admin_id_type = BigInteger().with_variant(Integer, "sqlite")

    created_by_admin_id = Column(admin_id_type, ForeignKey("admins.admin_id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    body = Column(Text, nullable=False)
    target_kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=True)  # NULL means broadcast to all
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    
    # Relationships
    creator = relationship("Admin", back_populates="posts", foreign_keys=[created_by_admin_id])
    target_kindergarten = relationship("Kindergarten", back_populates="posts", foreign_keys=[target_kindergarten_id])
