"""Teacher schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _split_full_name(full_name: str) -> tuple[Optional[str], Optional[str]]:
    parts = [part for part in full_name.strip().split() if part]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


class TeacherCreateRequest(BaseModel):
    """Create teacher request."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: str = Field(..., min_length=7, max_length=20)
    experience_year: Optional[int] = Field(None, ge=0, le=80)
    group_id: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def normalize_name(self):
        if not self.full_name:
            if not self.first_name or not self.last_name:
                raise ValueError("full_name is required")
            self.full_name = f"{self.first_name.strip()} {self.last_name.strip()}".strip()
        first_name, last_name = _split_full_name(self.full_name)
        if not self.first_name:
            self.first_name = first_name
        if not self.last_name:
            self.last_name = last_name
        return self


class TeacherUpdateRequest(BaseModel):
    """Update teacher request."""

    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    experience_year: Optional[int] = Field(None, ge=0, le=80)
    group_id: Optional[str] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def normalize_name(self):
        if self.full_name:
            first_name, last_name = _split_full_name(self.full_name)
            if not self.first_name:
                self.first_name = first_name
            if not self.last_name:
                self.last_name = last_name
        elif self.first_name and self.last_name:
            self.full_name = f"{self.first_name.strip()} {self.last_name.strip()}".strip()
        return self


class TeacherResponse(BaseModel):
    """Teacher response schema."""

    model_config = ConfigDict(from_attributes=True)

    teacher_id: str
    kindergarten_id: str
    group_id: Optional[str]
    full_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: str
    experience_year: Optional[int]
    created_at: datetime
    updated_at: datetime
