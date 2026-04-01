"""Parent schemas."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.attendance import AttendanceStatus
from app.models.menu import Meal, MenuStatus
from app.models.payment import PaymentStatus


class ParentCreateRequest(BaseModel):
    """Create parent request."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=7, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    birth_date: Optional[date] = None
    password: str = Field(..., min_length=8)
    child_ids: list[str] = Field(default_factory=list)


class ParentUpdateRequest(BaseModel):
    """Update parent request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    birth_date: Optional[date] = None


class ParentResponse(BaseModel):
    """Parent response schema."""
    model_config = ConfigDict(from_attributes=True)

    parent_id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str]
    telegram_id: Optional[str]
    address: Optional[str]
    birth_date: Optional[date]
    created_at: datetime
    updated_at: datetime


class ParentDashboardAttendanceStatus(str, Enum):
    """Attendance status exposed on the parent dashboard."""

    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    UNMARKED = "unmarked"


class ParentPedagogueSummary(BaseModel):
    """Primary pedagogue details for a group."""

    pedagogue_id: str
    full_name: str
    role: str


class ParentGroupSummary(BaseModel):
    """Compact child group details."""

    group_id: str
    group_name: str


class ParentMenuItemResponse(BaseModel):
    """Parent-facing menu item."""

    meal: Meal
    title: str
    description: Optional[str]
    calories: Optional[int]


class ParentMenuResponse(BaseModel):
    """Menu visible to a parent for one child/group/date."""

    menu_id: str
    group_id: str
    group_name: str
    menu_date: date
    status: MenuStatus
    published_at: Optional[datetime]
    notes: Optional[str]
    items: list[ParentMenuItemResponse]


class ParentLatestPaymentSummary(BaseModel):
    """Latest payment snapshot for one child."""

    payment_id: str
    billing_period: str
    amount: Decimal
    status: PaymentStatus
    due_date: date


class ParentDashboardChildItem(BaseModel):
    """Dashboard payload for one linked child."""

    child_id: str
    full_name: str
    birth_date: Optional[date]
    gender: Optional[str]
    group: ParentGroupSummary
    pedagogue: Optional[ParentPedagogueSummary]
    today_attendance_status: ParentDashboardAttendanceStatus
    today_menu: Optional[ParentMenuResponse]
    latest_payment: Optional[ParentLatestPaymentSummary]


class ParentDashboardResponse(BaseModel):
    """Dashboard summary for the current parent."""

    children: list[ParentDashboardChildItem]
    unread_notifications_count: int


class ParentAttendanceItemResponse(BaseModel):
    """Parent-facing attendance history row."""

    child_id: str
    child_name: str
    group_id: str
    group_name: str
    date: date
    status: AttendanceStatus
