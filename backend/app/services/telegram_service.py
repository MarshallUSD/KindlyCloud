"""Best-effort Telegram delivery service."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

from config import settings
from app.core.time import utcnow
from app.models.notification import Notification, NotificationEventType, NotificationType, TelegramDeliveryStatus
from app.models.parent import Parent

logger = logging.getLogger(__name__)


@dataclass
class TelegramDeliveryResult:
    """Best-effort Telegram send result."""

    status: TelegramDeliveryStatus
    delivered_at: datetime | None = None


class TelegramService:
    """Best-effort outbound Telegram sender."""

    def __init__(self) -> None:
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        self.api_base = getattr(settings, "TELEGRAM_API_BASE_URL", "https://api.telegram.org").rstrip("/")

    def send_parent_notification(self, *, parent: Parent | None, notification: Notification) -> TelegramDeliveryResult:
        """Send one notification to a parent when integration settings allow it."""
        if parent is None or not parent.telegram_id:
            return TelegramDeliveryResult(status=TelegramDeliveryStatus.SKIPPED)
        if not self.bot_token:
            logger.info("Skipping Telegram delivery because TELEGRAM_BOT_TOKEN is not configured")
            return TelegramDeliveryResult(status=TelegramDeliveryStatus.SKIPPED)

        text = self.format_message(notification)
        try:
            response = httpx.post(
                f"{self.api_base}/bot{self.bot_token}/sendMessage",
                json={"chat_id": parent.telegram_id, "text": text},
                timeout=10.0,
            )
            response.raise_for_status()
            return TelegramDeliveryResult(
                status=TelegramDeliveryStatus.SENT,
                delivered_at=utcnow(),
            )
        except Exception as exc:  # pragma: no cover - defensive around external API
            self.handle_send_failure(parent=parent, notification=notification, exc=exc)
            return TelegramDeliveryResult(status=TelegramDeliveryStatus.FAILED)

    def format_message(self, notification: Notification) -> str:
        """Render the Telegram message body."""
        if notification.type == NotificationType.ANNOUNCEMENT:
            return f"Yangi e'lon: {notification.title}\n{notification.message}"

        mapping = {
            NotificationEventType.ATTENDANCE_LATE: "Farzandingiz bugun kech qoldi.",
            NotificationEventType.ATTENDANCE_ABSENT: "Farzandingiz bugun bog'chaga kelmadi.",
            NotificationEventType.PAYMENT_CREATED: "Siz uchun yangi to'lov yaratildi.",
            NotificationEventType.PAYMENT_OVERDUE: "Sizda muddati o'tgan to'lov mavjud.",
            NotificationEventType.PAYMENT_PAID: "To'lovingiz muvaffaqiyatli tasdiqlandi.",
        }
        return mapping.get(notification.event_type, f"{notification.title}\n{notification.message}")

    def handle_send_failure(self, *, parent: Parent, notification: Notification, exc: Exception) -> None:
        """Log a delivery failure without interrupting the caller."""
        logger.exception(
            "Telegram delivery failed for parent_id=%s notification_id=%s",
            parent.parent_id,
            notification.id,
            exc_info=exc,
        )
