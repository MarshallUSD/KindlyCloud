"""Announcement creation and fan-out workflows."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.core.time import utcnow
from app.models.child import Child, ParentChildLink
from app.models.notification import Announcement, AnnouncementTargetType
from app.models.parent import Parent
from app.models.user import User
from app.repositories.notification import AnnouncementRepository
from app.services.notification import NotificationService
from app.services.tenant_scope import TenantScopedService


@dataclass
class AnnouncementRecipient:
    """Resolved fan-out recipient."""

    parent_id: str
    child_id: str | None


class AnnouncementService(TenantScopedService):
    """Tenant-safe announcement management and fan-out."""

    def __init__(self, db: Session):
        super().__init__(db)
        self.db = db
        self.repo = AnnouncementRepository(db)
        self.notification_service = NotificationService(db)

    def create_announcement(
        self,
        current_user: User,
        *,
        title: str,
        message: str,
        target_type: AnnouncementTargetType,
        target_group_id: str | None,
        target_child_id: str | None,
        scheduled_at: datetime | None,
    ) -> Announcement:
        """Create an announcement and fan it out immediately when due."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        self._validate_target(
            kindergarten_id=kindergarten_id,
            target_type=target_type,
            target_group_id=target_group_id,
            target_child_id=target_child_id,
        )
        announcement = Announcement(
            id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            title=title,
            message=message,
            target_type=target_type,
            target_group_id=target_group_id,
            target_child_id=target_child_id,
            scheduled_at=scheduled_at,
            created_by_user_id=current_user.user_id,
        )
        self.repo.create(announcement)
        self.db.commit()
        self.db.refresh(announcement)
        if scheduled_at is None or scheduled_at <= utcnow():
            announcement = self.fan_out_announcement(announcement.id, current_user=current_user)
        return announcement

    def list_announcements(self, current_user: User, *, skip: int = 0, limit: int = 20) -> tuple[list[Announcement], int]:
        """List announcements for one tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        return self.repo.list_for_kindergarten(kindergarten_id=kindergarten_id, skip=skip, limit=limit)

    def get_announcement(self, current_user: User, announcement_id: str) -> Announcement:
        """Get one tenant-scoped announcement."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        announcement = self.repo.get_by_id(announcement_id)
        if not announcement:
            raise NotFoundException("Announcement not found")
        if announcement.kindergarten_id != kindergarten_id:
            raise AuthorizationException("You do not have access to this announcement")
        return announcement

    def delete_announcement(self, current_user: User, announcement_id: str) -> None:
        """Delete one tenant-scoped announcement."""
        announcement = self.get_announcement(current_user, announcement_id)
        self.repo.delete(announcement)
        self.db.commit()

    def send_due_announcements(self, *, now: datetime | None = None) -> int:
        """Dispatch scheduled announcements that are due."""
        current_time = now or utcnow()
        due_announcements = self.repo.list_due_scheduled(before=current_time)
        for announcement in due_announcements:
            self.fan_out_announcement(announcement.id)
        return len(due_announcements)

    def fan_out_announcement(self, announcement_id: str, current_user: User | None = None) -> Announcement:
        """Expand one announcement into parent-scoped notifications."""
        announcement = self.repo.get_by_id(announcement_id)
        if not announcement:
            raise NotFoundException("Announcement not found")
        if current_user is not None:
            tenant_id = self.get_current_kindergarten_id(current_user)
            if announcement.kindergarten_id != tenant_id:
                raise AuthorizationException("You do not have access to this announcement")
        if announcement.sent_at is not None:
            return announcement

        recipients = self.resolve_target_parents(announcement)
        created_notifications = []
        for recipient in recipients:
            notification = self.notification_service.create_announcement_notification(
                kindergarten_id=announcement.kindergarten_id,
                parent_id=recipient.parent_id,
                child_id=recipient.child_id,
                source_announcement_id=announcement.id,
                title=announcement.title,
                message=announcement.message,
            )
            created_notifications.append(notification)

        stats = self.repo.get_or_create_delivery_stats(announcement_id=announcement.id)
        stats.sent_count = len(created_notifications)
        stats.read_count = 0
        self.repo.save_delivery_stats(stats)
        self.repo.mark_sent(announcement, sent_at=utcnow())
        self.db.commit()

        for notification in created_notifications:
            self.db.refresh(notification)
            self.notification_service.deliver_notification(notification)

        return self.repo.get_by_id(announcement.id) or announcement

    def resolve_target_parents(self, announcement: Announcement) -> list[AnnouncementRecipient]:
        """Resolve tenant-safe recipients for an announcement."""
        query = (
            self.db.query(Parent.parent_id, Child.child_id)
            .join(ParentChildLink, ParentChildLink.parent_id == Parent.parent_id)
            .join(Child, Child.child_id == ParentChildLink.child_id)
            .filter(
                Child.kindergarten_id == announcement.kindergarten_id,
                ParentChildLink.status == "active",
            )
        )

        if announcement.target_type == AnnouncementTargetType.GROUP:
            query = query.filter(Child.group_id == announcement.target_group_id)
        elif announcement.target_type == AnnouncementTargetType.CHILD:
            query = query.filter(Child.child_id == announcement.target_child_id)

        rows = query.order_by(Parent.parent_id.asc(), Child.child_id.asc()).all()
        recipients: list[AnnouncementRecipient] = []
        seen_parent_ids: set[str] = set()
        for parent_id, child_id in rows:
            if announcement.target_type == AnnouncementTargetType.CHILD:
                recipients.append(AnnouncementRecipient(parent_id=parent_id, child_id=child_id))
                continue
            if parent_id in seen_parent_ids:
                continue
            seen_parent_ids.add(parent_id)
            recipients.append(AnnouncementRecipient(parent_id=parent_id, child_id=None))
        return recipients

    def _validate_target(
        self,
        *,
        kindergarten_id: str,
        target_type: AnnouncementTargetType,
        target_group_id: str | None,
        target_child_id: str | None,
    ) -> None:
        if target_type == AnnouncementTargetType.ALL:
            if target_group_id or target_child_id:
                raise ValidationException("all announcements cannot include group or child targets")
            return
        if target_type == AnnouncementTargetType.GROUP:
            if not target_group_id or target_child_id:
                raise ValidationException("group announcements require target_group_id only")
            self.get_group_for_kindergarten(kindergarten_id, target_group_id)
            return
        if not target_child_id or target_group_id:
            raise ValidationException("child announcements require target_child_id only")
        self.get_tenant_record_or_raise(
            model=Child,
            record_field=Child.child_id,
            record_id=target_child_id,
            kindergarten_field=Child.kindergarten_id,
            kindergarten_id=kindergarten_id,
            not_found_message="Child not found",
            forbidden_message="You cannot access another kindergarten's child",
        )
