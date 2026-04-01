"""Parent submission models for one-way Telegram bot intake."""
from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class ParentSubmissionSource(str, Enum):
    """Supported ingestion sources."""

    TELEGRAM_BOT = "telegram_bot"


class ParentSubmissionType(str, Enum):
    """Supported submission categories."""

    PAYMENT_PROOF = "payment_proof"
    MESSAGE = "message"
    OTHER = "other"


class ParentSubmissionAttachmentType(str, Enum):
    """Supported attachment kinds."""

    IMAGE = "image"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"


class ParentSubmissionStatus(str, Enum):
    """Review lifecycle for parent submissions."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class ParentSubmission(Base):
    """One-way parent submission visible to kindergarten staff for review."""

    __tablename__ = "parent_submissions"
    __table_args__ = (
        Index("ix_parent_submissions_kindergarten_id", "kindergarten_id"),
        Index("ix_parent_submissions_parent_id", "parent_id"),
        Index("ix_parent_submissions_child_id", "child_id"),
        Index("ix_parent_submissions_payment_id", "payment_id"),
        Index("ix_parent_submissions_status", "status"),
        Index("ix_parent_submissions_submission_type", "submission_type"),
        Index("ix_parent_submissions_created_at", "created_at"),
        Index(
            "ix_parent_submissions_kindergarten_status_created",
            "kindergarten_id",
            "status",
            "created_at",
        ),
    )

    id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(
        String,
        ForeignKey("kindergartens.kindergarten_id"),
        nullable=False,
    )
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=True)
    payment_id = Column(String, ForeignKey("payments.payment_id"), nullable=True)
    source = Column(
        SQLEnum(ParentSubmissionSource, name="parent_submission_source", native_enum=False),
        nullable=False,
        default=ParentSubmissionSource.TELEGRAM_BOT,
    )
    submission_type = Column(
        SQLEnum(ParentSubmissionType, name="parent_submission_type", native_enum=False),
        nullable=False,
    )
    text = Column(Text, nullable=True)
    attachment_url = Column(Text, nullable=True)
    attachment_type = Column(
        SQLEnum(ParentSubmissionAttachmentType, name="parent_submission_attachment_type", native_enum=False),
        nullable=True,
    )
    status = Column(
        SQLEnum(ParentSubmissionStatus, name="parent_submission_status", native_enum=False),
        nullable=False,
        default=ParentSubmissionStatus.PENDING,
    )
    admin_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    kindergarten = relationship("Kindergarten", back_populates="parent_submissions")
    parent = relationship("Parent", back_populates="parent_submissions")
    child = relationship("Child", back_populates="parent_submissions")
    payment = relationship("Payment", back_populates="parent_submissions")
    reviewer = relationship("User", back_populates="reviewed_parent_submissions", foreign_keys=[reviewed_by])
