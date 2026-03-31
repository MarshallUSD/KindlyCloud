"""Payment schemas for MVP billing tracking."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreateRequest(BaseModel):
    """Create a monthly payment record."""

    child_id: str
    amount: Decimal = Field(..., gt=0)
    due_date: date
    billing_period: str = Field(..., min_length=7, max_length=7, pattern=r"^\d{4}-\d{2}$")
    status: PaymentStatus = PaymentStatus.PENDING
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    payment_method: Optional[PaymentMethod] = None

    @field_validator("status")
    @classmethod
    def validate_create_status(cls, value: PaymentStatus) -> PaymentStatus:
        if value not in {PaymentStatus.PENDING, PaymentStatus.PAID}:
            raise ValueError("New payment records can only start as pending or paid")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount_scale(cls, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))


class PaymentUpdateRequest(BaseModel):
    """Update editable fields before a payment is marked paid."""

    amount: Optional[Decimal] = Field(None, gt=0)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentMarkPaidRequest(BaseModel):
    """Mark a payment as paid manually."""

    paid_at: Optional[datetime] = None
    payment_method: Optional[PaymentMethod] = None


class PaymentResponse(BaseModel):
    """Kindergarten payment response."""

    payment_id: str
    kindergarten_id: str
    child_id: str
    parent_id: Optional[str]
    billing_period: str
    amount: Decimal
    due_date: date
    status: PaymentStatus
    notes: Optional[str]
    paid_at: Optional[datetime]
    payment_method: Optional[PaymentMethod]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParentPaymentResponse(BaseModel):
    """Parent-facing payment response."""

    payment_id: str
    child_id: str
    child_name: Optional[str]
    amount: Decimal
    due_date: date
    billing_period: str
    status: PaymentStatus
    paid_at: Optional[datetime]
    notes: Optional[str]
    payment_method: Optional[PaymentMethod]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentReportPeriod(str, Enum):
    """Allowed reporting periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
