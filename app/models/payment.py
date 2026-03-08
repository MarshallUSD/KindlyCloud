"""Payment model."""
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Numeric, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.base import Base


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProvider(str, Enum):
    """Payment provider enumeration."""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"


class Payment(Base):
    """Payment record for enrollment fees."""
    __tablename__ = "payments"
    
    payment_id = Column(String, primary_key=True, index=True)
    enrol_id = Column(String, ForeignKey("enrollments.enrol_id"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("parents.parent_id"), nullable=False, index=True)
    child_id = Column(String, ForeignKey("children.child_id"), nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    provider = Column(SQLEnum(PaymentProvider), nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    transaction_id = Column(String, nullable=True, unique=True, index=True)
    recipient_info = Column(Text, nullable=True)  # Account info, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="payments")
    parent = relationship("Parent", back_populates="payments", foreign_keys=[parent_id])
    child = relationship("Child", back_populates="payments", foreign_keys=[child_id])
