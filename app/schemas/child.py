"""Child schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from app.models.child import ChildStatus


class ChildCreateRequest(BaseModel):
    """Create child request."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    birth_date: date
    gender: Optional[str] = Field(None, description="male, female, or other")
    address: Optional[str] = None


class ChildUpdateRequest(BaseModel):
    """Update child request."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None


class ChildResponse(BaseModel):
    """Child response schema."""
    child_id: str
    first_name: str
    last_name: str
    birth_date: date
    gender: Optional[str]
    address: Optional[str]
    status: ChildStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ParentChildLinkRequest(BaseModel):
    """Link child to parent request."""
    child_id: str
    note: Optional[str] = None


class ParentChildLinkResponse(BaseModel):
    """Parent-child link response."""
    link_id: str
    parent_id: str
    child_id: str
    status: str
    linked_at: datetime
    note: Optional[str]
    
    class Config:
        from_attributes = True
