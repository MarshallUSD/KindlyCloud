"""Backward-compatible teacher schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.staff import StaffCreate, StaffUpdate


class TeacherCreateRequest(StaffCreate):
    """Legacy teacher create schema."""

    experience_year: Optional[int] = Field(None, ge=0, le=80)

    @model_validator(mode="before")
    @classmethod
    def map_legacy_role(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        values.setdefault("role", "teacher")
        return values


class TeacherUpdateRequest(StaffUpdate):
    """Legacy teacher update schema."""

    experience_year: Optional[int] = Field(None, ge=0, le=80)

    @model_validator(mode="before")
    @classmethod
    def map_legacy_role(cls, values):
        if not isinstance(values, dict):
            return values
        values = dict(values)
        if values.get("role") is None and "experience_year" in values:
            values["role"] = "teacher"
        return values


class TeacherResponse(BaseModel):
    """Legacy teacher response schema."""

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
    experience_year: Optional[int]
    created_at: datetime
    updated_at: datetime
