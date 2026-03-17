"""Group schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, time


class GroupCreateRequest(BaseModel):
    """Create group request."""
    group_name: str = Field(..., min_length=1, max_length=100)
    teacher_ids: List[str] = Field(default_factory=list)
    start_date: date
    end_date: Optional[date] = None
    schedule: Optional[str] = None
    max_capacity: Optional[int] = Field(None, ge=1)
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    room_number: Optional[str] = None
    monthly_fee: Optional[float] = None
    active_time_start: Optional[time] = None
    active_time_end: Optional[time] = None


class GroupUpdateRequest(BaseModel):
    """Update group request."""
    group_name: Optional[str] = None
    teacher_ids: Optional[List[str]] = None
    end_date: Optional[date] = None
    schedule: Optional[str] = None
    max_capacity: Optional[int] = None
    age_from: Optional[int] = None
    age_to: Optional[int] = None
    room_number: Optional[str] = None
    monthly_fee: Optional[float] = None
    active_time_start: Optional[time] = None
    active_time_end: Optional[time] = None


class GroupResponse(BaseModel):
    """Group response schema."""
    group_id: str
    kindergarten_id: str
    group_name: str
    start_date: date
    end_date: Optional[date]
    schedule: Optional[str]
    max_capacity: Optional[int]
    age_from: Optional[int]
    age_to: Optional[int]
    room_number: Optional[str]
    monthly_fee: Optional[float]
    active_time_start: Optional[time]
    active_time_end: Optional[time]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
