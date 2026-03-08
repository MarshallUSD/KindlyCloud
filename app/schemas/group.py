"""Group schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class GroupCreateRequest(BaseModel):
    """Create group request."""
    group_name: str = Field(..., min_length=1, max_length=100)
    teacher_id: str
    start_date: date
    end_date: Optional[date] = None
    schedule: Optional[str] = None
    max_capacity: Optional[int] = Field(None, ge=1)


class GroupUpdateRequest(BaseModel):
    """Update group request."""
    group_name: Optional[str] = None
    teacher_id: Optional[str] = None
    end_date: Optional[date] = None
    schedule: Optional[str] = None
    max_capacity: Optional[int] = None


class GroupResponse(BaseModel):
    """Group response schema."""
    group_id: str
    kindergarten_id: str
    group_name: str
    teacher_id: str
    start_date: date
    end_date: Optional[date]
    schedule: Optional[str]
    max_capacity: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
