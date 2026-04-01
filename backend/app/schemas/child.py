"""Child schemas."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.child import ChildGender
from app.schemas._person import split_full_name


class ChildCreate(BaseModel):
    """Create child request."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    birth_date: date
    gender: Optional[ChildGender] = None
    group_id: str
    parent_phone: str = Field(..., min_length=7, max_length=20)
    notes: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None

    @model_validator(mode="after")
    def normalize_name(self):
        if not self.full_name:
            if not self.first_name or not self.last_name:
                raise ValueError("full_name is required")
            self.full_name = f"{self.first_name.strip()} {self.last_name.strip()}".strip()
        first_name, last_name = split_full_name(self.full_name)
        if not self.first_name:
            self.first_name = first_name
        if not self.last_name:
            self.last_name = last_name
        return self


class ChildUpdate(BaseModel):
    """Update child request."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    birth_date: Optional[date] = None
    gender: Optional[ChildGender] = None
    group_id: Optional[str] = None
    parent_phone: Optional[str] = Field(None, min_length=7, max_length=20)
    notes: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None

    @model_validator(mode="after")
    def normalize_name(self):
        if self.full_name:
            first_name, last_name = split_full_name(self.full_name)
            if not self.first_name:
                self.first_name = first_name
            if not self.last_name:
                self.last_name = last_name
        elif self.first_name and self.last_name:
            self.full_name = f"{self.first_name.strip()} {self.last_name.strip()}".strip()
        return self


class ChildResponse(BaseModel):
    """Child response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    child_id: str
    kindergarten_id: str
    group_id: str
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    birth_date: date
    gender: Optional[ChildGender]
    parent_phone: str
    notes: Optional[str]
    address: Optional[str]
    created_at: datetime
    updated_at: datetime


class ParentChildLinkRequest(BaseModel):
    """Link child to parent request."""

    child_id: str
    note: Optional[str] = None


class ParentChildLinkResponse(BaseModel):
    """Parent-child link response."""

    model_config = ConfigDict(from_attributes=True)

    link_id: str
    parent_id: str
    child_id: str
    status: str
    linked_at: datetime
    note: Optional[str]


ChildCreateRequest = ChildCreate
ChildUpdateRequest = ChildUpdate
