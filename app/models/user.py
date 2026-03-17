"""User model and related enums."""
from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from app.models.notification import Notification  # noqa
from app.core.base import Base


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

    # Map the current app's user_id field to the legacy DB id column.
    user_id = Column("id", Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=True)
    phone_or_email = Column(String(100), nullable=False, unique=True, index=True)
    role = Column(String(50), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String(10), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @property
    def email(self) -> str | None:
        return self.phone_or_email if "@" in self.phone_or_email else None

    @property
    def phone(self) -> str | None:
        return self.phone_or_email if "@" not in self.phone_or_email else None

    @property
    def status(self) -> UserStatus:
        return UserStatus.ACTIVE if self.is_active else UserStatus.INACTIVE

    @property
    def updated_at(self) -> datetime:
        return self.created_at

    kindergarten_users = relationship("KindergartenUser", back_populates="user", cascade="all, delete-orphan")
    parent_user = relationship("ParentUser", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="creator", foreign_keys="Post.created_by_admin_user_id")
    feedback_handled = relationship("Feedback", back_populates="handled_by_admin", foreign_keys="Feedback.handled_by_admin_user_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    menus_created = relationship("Menu", back_populates="created_by_user", foreign_keys="Menu.created_by_user_id")
