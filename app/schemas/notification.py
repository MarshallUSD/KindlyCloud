"""User schemas (in addition to auth schemas)."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole, UserStatus


class NotificationResponse(BaseModel):
    """Notification response schema."""
    notification_id: str
    user_id: str
    notif_type: str
    payload: Optional[dict]
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
