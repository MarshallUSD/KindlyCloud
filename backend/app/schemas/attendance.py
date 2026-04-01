"""Attendance schemas."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.attendance import AttendanceStatus


class AttendanceRecordInput(BaseModel):
    """One child attendance entry inside a bulk save request."""

    child_id: str
    status: AttendanceStatus


class AttendanceBulkSaveRequest(BaseModel):
    """Bulk attendance upsert request."""

    group_id: str
    date: date
    records: list[AttendanceRecordInput] = Field(..., min_length=1)

    @model_validator(mode="after")
    def ensure_unique_children(self):
        child_ids = [record.child_id for record in self.records]
        if len(child_ids) != len(set(child_ids)):
            raise ValueError("Duplicate child_id values are not allowed")
        return self


class AttendanceResponse(BaseModel):
    """Attendance record response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    attendance_id: str
    kindergarten_id: str
    child_id: str
    group_id: str
    date: date
    status: AttendanceStatus
    marked_at: datetime
    created_at: datetime
    updated_at: datetime


class AttendanceBulkSaveResponse(BaseModel):
    """Bulk attendance save response."""

    group_id: str
    date: date
    records: list[AttendanceResponse]


class DailyAttendanceItemResponse(BaseModel):
    """Attendance status for one child in a daily group view."""

    child_id: str
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    status: Optional[AttendanceStatus]
    marked_at: Optional[datetime]


class DailyAttendanceResponse(BaseModel):
    """Children in a group for a selected date."""

    group_id: str
    date: date
    items: list[DailyAttendanceItemResponse]


class AttendanceHistoryItemResponse(BaseModel):
    """Attendance history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    attendance_id: str
    kindergarten_id: str
    child_id: str
    group_id: str
    date: date
    status: AttendanceStatus
    marked_at: datetime
    created_at: datetime
    updated_at: datetime
    child_name: str


class AttendanceSummaryResponse(BaseModel):
    """Attendance summary for one group and date."""

    group_id: str
    date: date
    total_children: int
    present_count: int
    late_count: int
    absent_count: int
    unmarked_count: int


class AttendanceCreateRequest(BaseModel):
    """Legacy single-record request used by the old kindergarten route."""

    enrol_id: str
    attend_date: date
    status: AttendanceStatus
    notes: Optional[str] = None
