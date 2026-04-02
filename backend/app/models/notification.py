"""Notification, announcement, and delivery preference models."""
from __future__ import annotations

from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class NotificationType(str, Enum):
    """Supported notification families."""

    SYSTEM = "system"
    ANNOUNCEMENT = "announcement"


class NotificationEventType(str, Enum):
    """Supported automatic backend notification events."""

    ATTENDANCE_LATE = "attendance_late"
    ATTENDANCE_ABSENT = "attendance_absent"
    PAYMENT_CREATED = "payment_created"
    PAYMENT_OVERDUE = "payment_overdue"
    PAYMENT_PAID = "payment_paid"


class AnnouncementTargetType(str, Enum):
    """Announcement audience selectors."""

    ALL = "all"
    GROUP = "group"
    CHILD = "child"


class TelegramDeliveryStatus(str, Enum):
    """Best-effort Telegram delivery state."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class Notification(Base):
    """Parent-scoped delivery and read record."""

    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=True, index=True)
    type = Column(SQLEnum(NotificationType, name="notification_type", native_enum=False), nullable=False)
    event_type = Column(
        SQLEnum(NotificationEventType, name="notification_event_type", native_enum=False),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    source_announcement_id = Column(String, ForeignKey("announcements.id"), nullable=True, index=True)
    telegram_delivery_status = Column(
        SQLEnum(TelegramDeliveryStatus, name="telegram_delivery_status", native_enum=False),
        nullable=True,
    )
    telegram_delivered_at = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    dedup_key = Column(String(255), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    kindergarten = relationship("Kindergarten", back_populates="notifications")
    parent = relationship("Parent", back_populates="notifications")
    child = relationship("Child", back_populates="notifications")
    source_announcement = relationship("Announcement", back_populates="notifications")


class Announcement(Base):
    """Manual outbound announcement source record."""

    __tablename__ = "announcements"

    id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(String, ForeignKey("kindergartens.kindergarten_id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    target_type = Column(
        SQLEnum(AnnouncementTargetType, name="announcement_target_type", native_enum=False),
        nullable=False,
    )
    target_group_id = Column(String, ForeignKey("groups.group_id"), nullable=True, index=True)
    target_child_id = Column(String, ForeignKey("children.child_id"), nullable=True, index=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    kindergarten = relationship("Kindergarten", back_populates="announcements")
    creator = relationship("User", back_populates="announcements_created", foreign_keys=[created_by_user_id])
    notifications = relationship("Notification", back_populates="source_announcement")
    delivery_stats = relationship(
        "NotificationDeliveryStats",
        back_populates="announcement",
        uselist=False,
        cascade="all, delete-orphan",
    )


class NotificationDeliveryStats(Base):
    """Aggregated delivery counters for one announcement fan-out."""

    __tablename__ = "notification_delivery_stats"

    id = Column(String, primary_key=True, index=True)
    announcement_id = Column(String, ForeignKey("announcements.id"), nullable=True, unique=True, index=True)
    sent_count = Column(Integer, nullable=False, default=0)
    delivered_count = Column(Integer, nullable=False, default=0)
    read_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    announcement = relationship("Announcement", back_populates="delivery_stats")


class ParentNotificationSettings(Base):
    """Notification delivery preferences for one parent."""

    __tablename__ = "parent_notification_settings"

    id = Column(String, primary_key=True, index=True)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False, unique=True, index=True)
    attendance_enabled = Column(Boolean, nullable=False, default=True)
    payments_enabled = Column(Boolean, nullable=False, default=True)
    announcements_enabled = Column(Boolean, nullable=False, default=True)
    telegram_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    parent = relationship("Parent", back_populates="notification_settings")
