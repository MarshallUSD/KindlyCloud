"""Kindergarten schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class KindergartenCreateRequest(BaseModel):
    """Create kindergarten request."""
    kinder_name: str = Field(..., min_length=3, max_length=255)
    region: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    payment_note: Optional[str] = None


class KindergartenUpdateRequest(BaseModel):
    """Update kindergarten request."""
    kinder_name: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    street: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    payment_note: Optional[str] = None


class KindergartenResponse(BaseModel):
    """Kindergarten response schema."""
    kindergarten_id: str
    kinder_name: str
    region: Optional[str]
    city: Optional[str]
    district: Optional[str]
    street: Optional[str]
    address: Optional[str]
    is_verified: bool
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
