"""Notification and announcement schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.notification import (
    AnnouncementTargetType,
    NotificationEventType,
    NotificationType,
    TelegramDeliveryStatus,
)


class NotificationResponse(BaseModel):
    """Parent-facing notification payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    kindergarten_id: str
    parent_id: str
    child_id: Optional[str]
    type: NotificationType
    event_type: Optional[NotificationEventType]
    title: str
    message: str
    source_announcement_id: Optional[str]
    telegram_delivery_status: Optional[TelegramDeliveryStatus]
    telegram_delivered_at: Optional[datetime]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ParentNotificationSettingsResponse(BaseModel):
    """Notification preference payload."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: str
    attendance_enabled: bool
    payments_enabled: bool
    announcements_enabled: bool
    telegram_enabled: bool
    created_at: datetime
    updated_at: datetime


class ParentNotificationSettingsUpdateRequest(BaseModel):
    """Partial update request for parent notification preferences."""

    attendance_enabled: Optional[bool] = None
    payments_enabled: Optional[bool] = None
    announcements_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None


class NotificationDeliveryStatsResponse(BaseModel):
    """Announcement fan-out delivery counters."""

    model_config = ConfigDict(from_attributes=True)

    sent_count: int
    delivered_count: int
    read_count: int
    created_at: datetime
    updated_at: datetime


class AnnouncementCreateRequest(BaseModel):
    """Create a new announcement."""

    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    target_type: AnnouncementTargetType
    target_group_id: Optional[str] = None
    target_child_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_target(self) -> "AnnouncementCreateRequest":
        if self.target_type == AnnouncementTargetType.ALL:
            if self.target_group_id is not None or self.target_child_id is not None:
                raise ValueError("all announcements cannot include target_group_id or target_child_id")
        elif self.target_type == AnnouncementTargetType.GROUP:
            if not self.target_group_id or self.target_child_id is not None:
                raise ValueError("group announcements require target_group_id only")
        elif not self.target_child_id or self.target_group_id is not None:
            raise ValueError("child announcements require target_child_id only")
        return self


class AnnouncementResponse(BaseModel):
    """Announcement payload for kindergarten users."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    kindergarten_id: str
    title: str
    message: str
    target_type: AnnouncementTargetType
    target_group_id: Optional[str]
    target_child_id: Optional[str]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime
    delivery_stats: Optional[NotificationDeliveryStatsResponse] = None
