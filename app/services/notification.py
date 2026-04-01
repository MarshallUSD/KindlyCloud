"""Notification service hooks for MVP events."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException
from app.models.user import User
from app.repositories.notification import NotificationRepository


class NotificationService:
    """Persist notification-ready events without external delivery."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def create_bulk(self, *, user_ids: Iterable[int], notif_type: str, payload: Optional[dict]) -> None:
        """Create one notification record per user."""
        seen: set[int] = set()
        for user_id in user_ids:
            if user_id in seen:
                continue
            seen.add(user_id)
            self.repo.create_notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                notif_type=notif_type,
                payload=payload,
            )
        self.db.commit()

    def list_for_user(self, current_user: User, *, skip: int = 0, limit: int = 20):
        """List notifications for the authenticated user."""
        return self.repo.list_for_user(user_id=current_user.user_id, skip=skip, limit=limit)

    def count_unread_for_user(self, current_user: User) -> int:
        """Return unread notification count for the authenticated user."""
        return self.repo.count_unread_for_user(user_id=current_user.user_id)

    def mark_as_read(self, current_user: User, notification_id: str):
        """Mark one of the current user's notifications as read."""
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundException("Notification not found")
        if notification.user_id != str(current_user.user_id):
            raise AuthorizationException("You do not have access to this notification")
        if notification.read_at is not None:
            return notification
        return self.repo.mark_as_read(
            notification,
            timestamp=datetime.now(UTC).replace(tzinfo=None),
        )
