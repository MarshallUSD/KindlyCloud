"""Parent-scoped notification workflows."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException
from app.models.child import Child, ParentChildLink
from app.models.notification import (
    Notification,
    NotificationEventType,
    NotificationType,
    TelegramDeliveryStatus,
)
from app.models.parent import Parent
from app.models.user import User
from app.repositories.notification import AnnouncementRepository, NotificationRepository
from app.repositories.parent import ParentRepository
from app.services.telegram_service import TelegramDeliveryResult, TelegramService
from app.services.tenant_scope import TenantScopedService


@dataclass
class NotificationPreferenceDecision:
    """Resolved delivery preferences for one parent and category."""

    category_enabled: bool
    telegram_enabled: bool


class NotificationService(TenantScopedService):
    """Tenant-safe notification storage, reads, and delivery behavior."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db
        self.repo = NotificationRepository(db)
        self.parent_repo = ParentRepository(db)
        self.announcement_repo = AnnouncementRepository(db)
        self.telegram_service = TelegramService()

    def create_system_notification(
        self,
        *,
        kindergarten_id: str,
        parent_id: str,
        child_id: str | None,
        event_type: NotificationEventType,
        title: str,
        message: str,
        dedup_key: str | None = None,
        commit: bool = True,
    ) -> Notification:
        """Create one automatic system notification."""
        existing = self.apply_deduplication_rules(dedup_key=dedup_key)
        if existing is not None:
            return existing

        decision = self.evaluate_parent_preferences(
            parent_id=parent_id,
            notification_type=NotificationType.SYSTEM,
            event_type=event_type,
        )
        notification = Notification(
            id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            parent_id=parent_id,
            child_id=child_id,
            type=NotificationType.SYSTEM,
            event_type=event_type,
            title=title,
            message=message,
            dedup_key=dedup_key,
            telegram_delivery_status=TelegramDeliveryStatus.PENDING if decision.telegram_enabled else TelegramDeliveryStatus.SKIPPED,
        )
        self.repo.create(notification)
        if commit:
            self.db.commit()
            self.db.refresh(notification)
            self._deliver_best_effort(notification, decision=decision)
        return notification

    def create_system_notifications_for_child(
        self,
        *,
        kindergarten_id: str,
        child_id: str,
        event_type: NotificationEventType,
        title: str,
        message: str,
        event_date: date | None = None,
        business_event_id: str | None = None,
    ) -> list[Notification]:
        """Create one system notification per active linked parent."""
        parent_ids = self._get_parent_ids_for_child(child_id)
        created: list[tuple[Notification, NotificationPreferenceDecision]] = []
        for parent_id in parent_ids:
            dedup_key = self._build_dedup_key(
                parent_id=parent_id,
                child_id=child_id,
                event_type=event_type,
                event_date=event_date,
                business_event_id=business_event_id,
            )
            existing = self.apply_deduplication_rules(dedup_key=dedup_key)
            if existing is not None:
                continue

            decision = self.evaluate_parent_preferences(
                parent_id=parent_id,
                notification_type=NotificationType.SYSTEM,
                event_type=event_type,
            )
            notification = Notification(
                id=str(uuid.uuid4()),
                kindergarten_id=kindergarten_id,
                parent_id=parent_id,
                child_id=child_id,
                type=NotificationType.SYSTEM,
                event_type=event_type,
                title=title,
                message=message,
                dedup_key=dedup_key,
                telegram_delivery_status=TelegramDeliveryStatus.PENDING if decision.telegram_enabled else TelegramDeliveryStatus.SKIPPED,
            )
            self.repo.create(notification)
            created.append((notification, decision))

        if created:
            self.db.commit()
            for notification, decision in created:
                self.db.refresh(notification)
                self._deliver_best_effort(notification, decision=decision)
        return [notification for notification, _ in created]

    def create_announcement_notification(
        self,
        *,
        kindergarten_id: str,
        parent_id: str,
        child_id: str | None,
        source_announcement_id: str,
        title: str,
        message: str,
        commit: bool = False,
    ) -> Notification:
        """Create one parent-scoped announcement notification."""
        decision = self.evaluate_parent_preferences(
            parent_id=parent_id,
            notification_type=NotificationType.ANNOUNCEMENT,
            event_type=None,
        )
        notification = Notification(
            id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            parent_id=parent_id,
            child_id=child_id,
            type=NotificationType.ANNOUNCEMENT,
            event_type=None,
            title=title,
            message=message,
            source_announcement_id=source_announcement_id,
            dedup_key=f"announcement:{source_announcement_id}:{parent_id}:{child_id or 'all'}",
            telegram_delivery_status=TelegramDeliveryStatus.PENDING if decision.telegram_enabled else TelegramDeliveryStatus.SKIPPED,
        )
        self.repo.create(notification)
        if commit:
            self.db.commit()
            self.db.refresh(notification)
        return notification

    def list_parent_notifications(
        self,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
        type_: NotificationType | None = None,
        event_type: NotificationEventType | None = None,
        is_read: bool | None = None,
    ) -> tuple[list[Notification], int]:
        """List notifications for the authenticated parent."""
        parent = self._get_parent_for_user(current_user)
        return self.repo.list_for_parent(
            parent_id=parent.parent_id,
            skip=skip,
            limit=limit,
            type_=type_,
            event_type=event_type,
            is_read=is_read,
        )

    def count_unread_for_parent(self, current_user: User) -> int:
        """Return unread notification count for the current parent."""
        parent = self._get_parent_for_user(current_user)
        return self.repo.count_unread_for_parent(parent_id=parent.parent_id)

    def mark_as_read(self, current_user: User, notification_id: str) -> Notification:
        """Mark a notification as read for the current parent."""
        parent = self._get_parent_for_user(current_user)
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            raise NotFoundException("Notification not found")
        if notification.parent_id != parent.parent_id:
            raise AuthorizationException("You do not have access to this notification")
        if notification.is_read:
            return notification

        self.repo.mark_as_read(notification, timestamp=datetime.now(UTC).replace(tzinfo=None))
        if notification.source_announcement_id:
            self._refresh_announcement_read_count(notification.source_announcement_id)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_settings(self, current_user: User):
        """Return settings for the current parent."""
        parent = self._get_parent_for_user(current_user)
        settings_row = self.repo.get_or_create_settings(parent_id=parent.parent_id)
        self.db.commit()
        self.db.refresh(settings_row)
        return settings_row

    def update_settings(self, current_user: User, **changes):
        """Persist notification settings for the current parent."""
        parent = self._get_parent_for_user(current_user)
        settings_row = self.repo.get_or_create_settings(parent_id=parent.parent_id)
        filtered_changes = {key: value for key, value in changes.items() if value is not None}
        self.repo.update_settings(settings_row, **filtered_changes)
        self.db.commit()
        self.db.refresh(settings_row)
        return settings_row

    def apply_deduplication_rules(self, *, dedup_key: str | None) -> Notification | None:
        """Resolve an existing notification when a dedup key is supplied."""
        if not dedup_key:
            return None
        return self.repo.get_by_dedup_key(dedup_key=dedup_key)

    def evaluate_parent_preferences(
        self,
        *,
        parent_id: str,
        notification_type: NotificationType,
        event_type: NotificationEventType | None,
    ) -> NotificationPreferenceDecision:
        """Resolve delivery preferences for one parent and category."""
        settings_row = self.repo.get_or_create_settings(parent_id=parent_id)
        category_enabled = True
        if notification_type == NotificationType.ANNOUNCEMENT:
            category_enabled = settings_row.announcements_enabled
        elif event_type in {NotificationEventType.ATTENDANCE_LATE, NotificationEventType.ATTENDANCE_ABSENT}:
            category_enabled = settings_row.attendance_enabled
        elif event_type is not None:
            category_enabled = settings_row.payments_enabled
        return NotificationPreferenceDecision(
            category_enabled=category_enabled,
            telegram_enabled=category_enabled and settings_row.telegram_enabled,
        )

    def deliver_notification(self, notification: Notification) -> Notification:
        """Attempt Telegram delivery for an existing notification."""
        decision = self.evaluate_parent_preferences(
            parent_id=notification.parent_id,
            notification_type=notification.type,
            event_type=notification.event_type,
        )
        self._deliver_best_effort(notification, decision=decision)
        return notification

    def _deliver_best_effort(
        self,
        notification: Notification,
        *,
        decision: NotificationPreferenceDecision,
    ) -> None:
        """Attempt Telegram delivery without affecting the caller's transaction."""
        if not decision.telegram_enabled:
            notification.telegram_delivery_status = TelegramDeliveryStatus.SKIPPED
            self._persist_delivery_state(notification)
            return

        parent = self.parent_repo.get_by_id(notification.parent_id)
        result = self.telegram_service.send_parent_notification(parent=parent, notification=notification)
        self._apply_delivery_result(notification, result=result)

    def _apply_delivery_result(self, notification: Notification, *, result: TelegramDeliveryResult) -> None:
        """Persist the best-effort delivery outcome."""
        notification.telegram_delivery_status = result.status
        notification.telegram_delivered_at = result.delivered_at
        self._persist_delivery_state(notification)
        if result.status == TelegramDeliveryStatus.SENT and notification.source_announcement_id:
            self._increment_announcement_delivered_count(notification.source_announcement_id)

    def _persist_delivery_state(self, notification: Notification) -> None:
        """Save a notification status update without surfacing failures upstream."""
        try:
            self.db.add(notification)
            self.db.commit()
        except Exception:  # pragma: no cover - defensive isolation around best-effort delivery
            self.db.rollback()

    def _increment_announcement_delivered_count(self, announcement_id: str) -> None:
        """Increment the delivered counter for one announcement."""
        try:
            stats = self.announcement_repo.get_or_create_delivery_stats(announcement_id=announcement_id)
            stats.delivered_count += 1
            self.announcement_repo.save_delivery_stats(stats)
            self.db.commit()
        except Exception:  # pragma: no cover - defensive isolation around best-effort delivery
            self.db.rollback()

    def _refresh_announcement_read_count(self, announcement_id: str) -> None:
        """Refresh read_count from actual notification rows."""
        stats = self.announcement_repo.get_or_create_delivery_stats(announcement_id=announcement_id)
        stats.read_count = self.repo.count_read_for_announcement(announcement_id=announcement_id)
        self.announcement_repo.save_delivery_stats(stats)

    def _build_dedup_key(
        self,
        *,
        parent_id: str,
        child_id: str | None,
        event_type: NotificationEventType,
        event_date: date | None,
        business_event_id: str | None,
    ) -> str | None:
        """Build a deterministic deduplication key for business events."""
        if event_type in {NotificationEventType.ATTENDANCE_LATE, NotificationEventType.ATTENDANCE_ABSENT} and event_date:
            return f"{event_type.value}:{parent_id}:{child_id}:{event_date.isoformat()}"
        if business_event_id:
            return f"{event_type.value}:{business_event_id}:{parent_id}"
        return None

    def _get_parent_for_user(self, current_user: User) -> Parent:
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise NotFoundException("Parent profile not found")
        return parent

    def _get_parent_ids_for_child(self, child_id: str) -> list[str]:
        rows = (
            self.db.query(ParentChildLink.parent_id)
            .join(Child, Child.child_id == ParentChildLink.child_id)
            .filter(ParentChildLink.child_id == child_id, ParentChildLink.status == "active")
            .order_by(ParentChildLink.parent_id.asc())
            .all()
        )
        return [row[0] for row in rows]
