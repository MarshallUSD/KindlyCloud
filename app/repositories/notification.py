"""Notification repository."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository):
    """Repository for notification records."""

    def __init__(self, db: Session):
        super().__init__(db, Notification)

    def create_notification(
        self,
        *,
        notification_id: str,
        user_id: int,
        notif_type: str,
        payload: Optional[dict],
    ) -> Notification:
        """Create a notification record."""
        notification = Notification(
            notification_id=notification_id,
            user_id=str(user_id),
            notif_type=notif_type,
            payload=payload,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_for_user(self, *, user_id: int, skip: int, limit: int) -> tuple[list[Notification], int]:
        """List notifications for one user ordered newest first."""
        query = self.db.query(Notification).filter(Notification.user_id == str(user_id))
        total = query.count()
        items = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def count_unread_for_user(self, *, user_id: int) -> int:
        """Count unread notifications for one user."""
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == str(user_id), Notification.read_at.is_(None))
            .count()
        )

    def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Get notification by identifier."""
        return self.get_by_id_field("notification_id", notification_id)

    def mark_as_read(self, notification: Notification, *, timestamp: datetime) -> Notification:
        """Persist read timestamp on a notification."""
        notification.read_at = timestamp
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
