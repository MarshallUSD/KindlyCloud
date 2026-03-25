"""Group schemas."""
from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GroupCreateRequest(BaseModel):
    """Create group request."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100)
    age_from: int = Field(..., ge=0, le=18)
    age_to: int = Field(..., ge=0, le=18)
    capacity: int = Field(..., ge=1, le=200)
    schedule_from: time
    schedule_to: time
    monthly_fee: Decimal = Field(..., ge=0)
    teacher_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("name", values.get("group_name"))
        values.setdefault("capacity", values.get("max_capacity"))
        values.setdefault("schedule_from", values.get("active_time_start"))
        values.setdefault("schedule_to", values.get("active_time_end"))
        return values

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.age_from > self.age_to:
            raise ValueError("age_from must be less than or equal to age_to")
        if self.schedule_from >= self.schedule_to:
            raise ValueError("schedule_from must be earlier than schedule_to")
        return self


class GroupUpdateRequest(BaseModel):
    """Update group request."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age_from: Optional[int] = Field(None, ge=0, le=18)
    age_to: Optional[int] = Field(None, ge=0, le=18)
    capacity: Optional[int] = Field(None, ge=1, le=200)
    schedule_from: Optional[time] = None
    schedule_to: Optional[time] = None
    monthly_fee: Optional[Decimal] = Field(None, ge=0)
    teacher_id: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("name", values.get("group_name"))
        values.setdefault("capacity", values.get("max_capacity"))
        values.setdefault("schedule_from", values.get("active_time_start"))
        values.setdefault("schedule_to", values.get("active_time_end"))
        return values

    @model_validator(mode="after")
    def validate_business_rules(self):
        if self.age_from is not None and self.age_to is not None and self.age_from > self.age_to:
            raise ValueError("age_from must be less than or equal to age_to")
        if (
            self.schedule_from is not None
            and self.schedule_to is not None
            and self.schedule_from >= self.schedule_to
        ):
            raise ValueError("schedule_from must be earlier than schedule_to")
        return self


class GroupResponse(BaseModel):
    """Group response schema."""

    model_config = ConfigDict(from_attributes=True)

    group_id: str
    kindergarten_id: str
    name: str
    group_name: str
    age_from: Optional[int]
    age_to: Optional[int]
    capacity: Optional[int]
    max_capacity: Optional[int]
    schedule_from: Optional[time]
    schedule_to: Optional[time]
    monthly_fee: Optional[Decimal]
    teacher_id: Optional[str]
    created_at: datetime
    updated_at: datetime
