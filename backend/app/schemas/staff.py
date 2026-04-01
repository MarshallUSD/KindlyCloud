"""Staff schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas._person import split_full_name


class StaffCreate(BaseModel):
    """Create staff request."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: str = Field(..., min_length=7, max_length=20)
    role: str = Field(..., min_length=2, max_length=50)
    salary: Optional[Decimal] = Field(None, ge=0)
    hired_at: Optional[date] = None
    group_id: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("hired_at", values.get("hire_date"))
        values.setdefault("role", values.get("position") or "teacher")
        return values

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


class StaffUpdate(BaseModel):
    """Update staff request."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    role: Optional[str] = Field(None, min_length=2, max_length=50)
    salary: Optional[Decimal] = Field(None, ge=0)
    hired_at: Optional[date] = None
    group_id: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("hired_at", values.get("hire_date"))
        values.setdefault("role", values.get("position"))
        return values

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


class StaffResponse(BaseModel):
    """Staff response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    teacher_id: str
    kindergarten_id: str
    group_id: Optional[str]
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: str
    role: str
    salary: Optional[Decimal]
    hired_at: Optional[date]
    created_at: datetime
    updated_at: datetime
