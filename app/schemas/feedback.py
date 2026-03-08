"""Feedback schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.feedback import FeedbackStatus


class FeedbackCreateRequest(BaseModel):
    """Create feedback request."""
    message: str = Field(..., min_length=1)
    child_id: Optional[str] = None  # Optional, may be feedback about kindergarten


class FeedbackUpdateRequest(BaseModel):
    """Update feedback status request."""
    status: FeedbackStatus


class FeedbackResponse(BaseModel):
    """Feedback response schema."""
    feedback_id: str
    from_kindergarten_id: Optional[str]
    from_parent_id: Optional[str]
    child_id: Optional[str]
    message: str
    status: FeedbackStatus
    handled_by_admin_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
