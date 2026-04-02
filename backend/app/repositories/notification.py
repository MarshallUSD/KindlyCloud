"""Repositories for notifications, announcements, and preferences."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.notification import (
    Announcement,
    Notification,
    NotificationDeliveryStats,
    NotificationEventType,
    NotificationType,
    ParentNotificationSettings,
)
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    """Repository for parent-scoped notifications."""

    def __init__(self, db: Session):
        super().__init__(db, Notification)

    def create(self, notification: Notification) -> Notification:
        """Persist a notification record."""
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Get one notification."""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def get_by_dedup_key(self, *, dedup_key: str) -> Optional[Notification]:
        """Resolve one notification by deduplication key."""
        return self.db.query(Notification).filter(Notification.dedup_key == dedup_key).first()

    def list_for_parent(
        self,
        *,
        parent_id: str,
        skip: int,
        limit: int,
        type_: NotificationType | None = None,
        event_type: NotificationEventType | None = None,
        is_read: bool | None = None,
    ) -> tuple[list[Notification], int]:
        """List notifications for one parent ordered newest first."""
        query = self.db.query(Notification).filter(Notification.parent_id == parent_id)
        if type_ is not None:
            query = query.filter(Notification.type == type_)
        if event_type is not None:
            query = query.filter(Notification.event_type == event_type)
        if is_read is not None:
            query = query.filter(Notification.is_read.is_(is_read))

        total = query.with_entities(func.count(Notification.id)).scalar() or 0
        items = query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def count_unread_for_parent(self, *, parent_id: str) -> int:
        """Count unread notifications for one parent."""
        return (
            self.db.query(Notification)
            .filter(Notification.parent_id == parent_id, Notification.is_read.is_(False))
            .count()
        )

    def count_read_for_announcement(self, *, announcement_id: str) -> int:
        """Count read fan-out notifications for one announcement."""
        return (
            self.db.query(Notification)
            .filter(
                Notification.source_announcement_id == announcement_id,
                Notification.is_read.is_(True),
            )
            .count()
        )

    def mark_as_read(self, notification: Notification, *, timestamp: datetime) -> Notification:
        """Persist read state on a notification."""
        notification.is_read = True
        notification.read_at = timestamp
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_or_create_settings(self, *, parent_id: str) -> ParentNotificationSettings:
        """Return settings row for a parent, creating defaults on first access."""
        settings = (
            self.db.query(ParentNotificationSettings)
            .filter(ParentNotificationSettings.parent_id == parent_id)
            .first()
        )
        if settings:
            return settings
        settings = ParentNotificationSettings(id=str(uuid.uuid4()), parent_id=parent_id)
        self.db.add(settings)
        self.db.flush()
        return settings

    def update_settings(self, settings: ParentNotificationSettings, **changes) -> ParentNotificationSettings:
        """Persist notification preference changes."""
        for key, value in changes.items():
            setattr(settings, key, value)
        self.db.add(settings)
        self.db.flush()
        return settings


class AnnouncementRepository(BaseRepository):
    """Repository for announcements and their stats."""

    def __init__(self, db: Session):
        super().__init__(db, Announcement)

    def create(self, announcement: Announcement) -> Announcement:
        """Persist an announcement record."""
        self.db.add(announcement)
        self.db.flush()
        return announcement

    def get_by_id(self, announcement_id: str) -> Optional[Announcement]:
        """Get announcement by identifier."""
        return (
            self.db.query(Announcement)
            .options(joinedload(Announcement.delivery_stats))
            .filter(Announcement.id == announcement_id)
            .first()
        )

    def list_for_kindergarten(self, *, kindergarten_id: str, skip: int, limit: int) -> tuple[list[Announcement], int]:
        """List announcements for one tenant."""
        query = (
            self.db.query(Announcement)
            .options(joinedload(Announcement.delivery_stats))
            .filter(Announcement.kindergarten_id == kindergarten_id)
        )
        total = query.with_entities(func.count(Announcement.id)).scalar() or 0
        items = query.order_by(Announcement.created_at.desc(), Announcement.id.desc()).offset(skip).limit(limit).all()
        return items, total

    def list_due_scheduled(self, *, before: datetime) -> list[Announcement]:
        """Return unsent announcements due for dispatch."""
        return (
            self.db.query(Announcement)
            .options(joinedload(Announcement.delivery_stats))
            .filter(
                Announcement.sent_at.is_(None),
                Announcement.scheduled_at.is_not(None),
                Announcement.scheduled_at <= before,
            )
            .order_by(Announcement.scheduled_at.asc(), Announcement.created_at.asc())
            .all()
        )

    def mark_sent(self, announcement: Announcement, *, sent_at: datetime) -> Announcement:
        """Persist send timestamp."""
        announcement.sent_at = sent_at
        self.db.add(announcement)
        self.db.flush()
        return announcement

    def get_or_create_delivery_stats(self, *, announcement_id: str) -> NotificationDeliveryStats:
        """Return the stats row for an announcement."""
        stats = (
            self.db.query(NotificationDeliveryStats)
            .filter(NotificationDeliveryStats.announcement_id == announcement_id)
            .first()
        )
        if stats:
            return stats
        stats = NotificationDeliveryStats(id=str(uuid.uuid4()), announcement_id=announcement_id)
        self.db.add(stats)
        self.db.flush()
        return stats

    def save_delivery_stats(self, stats: NotificationDeliveryStats) -> NotificationDeliveryStats:
        """Persist stats changes."""
        self.db.add(stats)
        self.db.flush()
        return stats

    def delete(self, announcement: Announcement) -> None:
        """Delete an announcement record."""
        self.db.delete(announcement)
        self.db.flush()
