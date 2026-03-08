"""Attendance schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models.attendance import AttendanceStatus


class AttendanceCreateRequest(BaseModel):
    """Create attendance record request."""
    enrol_id: str
    attend_date: date
    status: AttendanceStatus
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    """Attendance response schema."""
    attendance_id: str
    enrol_id: str
    child_id: str
    attend_date: date
    status: AttendanceStatus
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
