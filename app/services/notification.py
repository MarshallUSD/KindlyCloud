"""Notification service hooks for MVP events."""
from __future__ import annotations

import uuid
from typing import Iterable, Optional

from sqlalchemy.orm import Session

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
