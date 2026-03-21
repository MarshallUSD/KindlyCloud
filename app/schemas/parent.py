"""Parent schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime


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
    parent_id: str
    first_name: str
    last_name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    birth_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
