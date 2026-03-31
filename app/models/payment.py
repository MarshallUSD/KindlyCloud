"""Payment tracking model for MVP billing."""
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.base import Base


class PaymentStatus(str, Enum):
    """Supported MVP payment statuses."""

    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class PaymentMethod(str, Enum):
    """Supported manual payment methods."""

    CASH = "cash"
    CLICK = "click"
    PAYME = "payme"
    BANK_TRANSFER = "bank_transfer"


class Payment(Base):
    """Monthly billing record created by a kindergarten tenant."""

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint(
            "kindergarten_id",
            "child_id",
            "billing_period",
            name="uq_payments_kindergarten_child_billing_period",
        ),
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        Index("ix_payments_kindergarten_id", "kindergarten_id"),
        Index("ix_payments_child_id", "child_id"),
        Index("ix_payments_due_date", "due_date"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_billing_period", "billing_period"),
    )

    payment_id = Column(String, primary_key=True, index=True)
    kindergarten_id = Column(
        String,
        ForeignKey("kindergartens.kindergarten_id"),
        nullable=False,
    )
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=True)
    billing_period = Column(String(7), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(
        SQLEnum(PaymentStatus, name="payment_status", native_enum=False),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(
        SQLEnum(PaymentMethod, name="payment_method", native_enum=False),
        nullable=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    kindergarten = relationship("Kindergarten", back_populates="payments")
    child = relationship("Child", back_populates="payments", foreign_keys=[child_id])
    parent = relationship("Parent", back_populates="payments", foreign_keys=[parent_id])

    @property
    def effective_status(self) -> PaymentStatus:
        """Return the computed status without mutating the record."""
        if self.status == PaymentStatus.PAID:
            return PaymentStatus.PAID
        if self.due_date < date.today():
            return PaymentStatus.OVERDUE
        return PaymentStatus.PENDING

    @property
    def child_name(self) -> str | None:
        """Expose child name in parent/report responses."""
        return self.child.full_name if self.child else None

    @property
    def group_name(self) -> str | None:
        """Expose group name in report responses."""
        if self.child and self.child.group:
            return self.child.group.group_name
        return None
