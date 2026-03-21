"""Post schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PostCreateRequest(BaseModel):
    """Create post request."""
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    target_kindergarten_id: Optional[str] = None  # NULL means broadcast to all


class PostResponse(BaseModel):
    """Post response schema."""
    post_id: str
    created_by_admin_id: int
    title: str
    body: str
    target_kindergarten_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
