"""User schemas (in addition to auth schemas)."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NotificationResponse(BaseModel):
    """Notification response schema."""
    model_config = ConfigDict(from_attributes=True)

    notification_id: str
    user_id: str
    notif_type: str
    payload: Optional[dict]
    read_at: Optional[datetime]
    created_at: datetime
    is_read: bool
