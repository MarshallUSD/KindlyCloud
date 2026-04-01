from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enrollment import EnrollmentStatus


class EnrollmentCreateRequest(BaseModel):
    """Create enrollment request."""
    child_id: str
    group_id: str
    enrol_date: date
    total_fees: Optional[Decimal] = None


class EnrollmentUpdateRequest(BaseModel):
    """Update enrollment request."""
    status: Optional[EnrollmentStatus] = None
    total_fees: Optional[Decimal] = None


class EnrollmentResponse(BaseModel):
    """Enrollment response schema."""
    enrol_id: str
    child_id: str
    group_id: str
    enrol_date: date
    status: EnrollmentStatus
    total_fees: Optional[Decimal]
    amount_paid: Decimal
    balance: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
