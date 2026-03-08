"""Payment schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.payment import PaymentStatus, PaymentProvider


class PaymentCreateRequest(BaseModel):
    """Create payment request."""
    enrol_id: str
    amount: Decimal = Field(..., decimal_places=2)
    payment_date: date
    provider: PaymentProvider
    transaction_id: Optional[str] = None
    recipient_info: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response schema."""
    payment_id: str
    enrol_id: str
    parent_id: str
    child_id: str
    payment_date: date
    amount: Decimal
    provider: PaymentProvider
    status: PaymentStatus
    transaction_id: Optional[str]
    recipient_info: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
