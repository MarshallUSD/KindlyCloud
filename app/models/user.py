"""User model and related enums."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.notification import Notification  # noqa
from app.core.base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    KINDERGARTEN = "kindergarten"
    PARENT = "parent"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    phone = Column(String(20), nullable=True, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    kindergarten_users = relationship("KindergartenUser", back_populates="user", cascade="all, delete-orphan")
    parent_user = relationship("ParentUser", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="creator", foreign_keys="Post.created_by_admin_user_id")
    feedback_handled = relationship("Feedback", back_populates="handled_by_admin", foreign_keys="Feedback.handled_by_admin_user_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    menus_created = relationship("Menu", back_populates="created_by_user", foreign_keys="Menu.created_by_user_id")
