from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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
    
    model_config = ConfigDict(from_attributes=True)
