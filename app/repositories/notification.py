"""Notification repository."""
from __future__ import annotations

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
