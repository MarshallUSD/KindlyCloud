"""Schemas for parent submission intake and review."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.parent_submission import (
    ParentSubmissionAttachmentType,
    ParentSubmissionSource,
    ParentSubmissionStatus,
    ParentSubmissionType,
)
from app.models.payment import PaymentStatus


class ParentSubmissionParentSummary(BaseModel):
    """Compact parent payload for dashboard use."""

    parent_id: str
    first_name: str
    last_name: str
    phone: str

    model_config = ConfigDict(from_attributes=True)


class ParentSubmissionChildSummary(BaseModel):
    """Compact child payload for dashboard use."""

    child_id: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class ParentSubmissionPaymentSummary(BaseModel):
    """Compact payment payload for dashboard use."""

    payment_id: str
    billing_period: str
    amount: Decimal
    status: PaymentStatus
    child_id: str

    model_config = ConfigDict(from_attributes=True)


class ParentSubmissionReviewerSummary(BaseModel):
    """Compact reviewer payload."""

    user_id: int
    full_name: Optional[str]
    email: Optional[str]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ParentSubmissionCreateInternal(BaseModel):
    """Protected ingestion payload accepted from the Telegram bot integration."""

    kindergarten_id: str
    parent_id: Optional[str] = None
    parent_telegram_id: Optional[str] = None
    child_id: Optional[str] = None
    payment_id: Optional[str] = None
    source: ParentSubmissionSource = ParentSubmissionSource.TELEGRAM_BOT
    submission_type: ParentSubmissionType
    text: Optional[str] = None
    attachment_url: Optional[str] = None
    attachment_type: Optional[ParentSubmissionAttachmentType] = None

    @model_validator(mode="after")
    def validate_content_and_parent_reference(self):
        """Require content and a usable parent reference."""
        if not self.parent_id and not self.parent_telegram_id:
            raise ValueError("Either parent_id or parent_telegram_id is required")
        if not self.text and not self.attachment_url:
            raise ValueError("Either text or attachment_url is required")
        if self.attachment_type and not self.attachment_url:
            raise ValueError("attachment_type requires attachment_url")
        return self


class ParentSubmissionReviewRequest(BaseModel):
    """Review action payload for kindergarten staff."""

    action: ParentSubmissionStatus
    admin_note: Optional[str] = None

    @model_validator(mode="after")
    def validate_action(self):
        """Restrict review API to explicit review actions."""
        if self.action not in {
            ParentSubmissionStatus.REVIEWED,
            ParentSubmissionStatus.APPROVED,
            ParentSubmissionStatus.REJECTED,
        }:
            raise ValueError("Action must be reviewed, approved, or rejected")
        return self


class ParentSubmissionFilterParams(BaseModel):
    """List filter payload resolved from query parameters."""

    status: Optional[ParentSubmissionStatus] = None
    submission_type: Optional[ParentSubmissionType] = None
    parent_id: Optional[str] = None
    child_id: Optional[str] = None
    payment_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

    def datetime_from(self) -> Optional[datetime]:
        """Normalize date_from to the start of day."""
        if self.date_from is None:
            return None
        return datetime.combine(self.date_from, time.min)

    def datetime_to(self) -> Optional[datetime]:
        """Normalize date_to to the end of day."""
        if self.date_to is None:
            return None
        return datetime.combine(self.date_to, time.max)


class ParentSubmissionListItem(BaseModel):
    """Submission row for inbox listing."""

    id: str
    submission_type: ParentSubmissionType
    text: Optional[str]
    attachment_url: Optional[str]
    attachment_type: Optional[ParentSubmissionAttachmentType]
    status: ParentSubmissionStatus
    created_at: datetime
    parent: ParentSubmissionParentSummary
    child: Optional[ParentSubmissionChildSummary]
    payment: Optional[ParentSubmissionPaymentSummary]

    model_config = ConfigDict(from_attributes=True)


class ParentSubmissionDetail(BaseModel):
    """Detailed submission payload."""

    id: str
    kindergarten_id: str
    parent_id: str
    child_id: Optional[str]
    payment_id: Optional[str]
    source: ParentSubmissionSource
    submission_type: ParentSubmissionType
    text: Optional[str]
    attachment_url: Optional[str]
    attachment_type: Optional[ParentSubmissionAttachmentType]
    status: ParentSubmissionStatus
    admin_note: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    parent: ParentSubmissionParentSummary
    child: Optional[ParentSubmissionChildSummary]
    payment: Optional[ParentSubmissionPaymentSummary]
    reviewer: Optional[ParentSubmissionReviewerSummary]

    model_config = ConfigDict(from_attributes=True)
