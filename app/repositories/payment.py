"""Payment repository."""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models.payment import Payment, PaymentStatus, PaymentProvider
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    """Repository for Payment model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Payment)
    
    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by payment_id."""
        return self.get_by_id_field('payment_id', payment_id)
    
    def get_by_enrollment(self, enrol_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Payment], int]:
        """Get payments by enrollment."""
        total = self.db.query(func.count(Payment.payment_id)).filter(
            Payment.enrol_id == enrol_id
        ).scalar()
        records = self.db.query(Payment).filter(
            Payment.enrol_id == enrol_id
        ).offset(skip).limit(limit).all()
        return records, total
    
    def get_by_parent(self, parent_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Payment], int]:
        """Get payments by parent."""
        total = self.db.query(func.count(Payment.payment_id)).filter(
            Payment.parent_id == parent_id
        ).scalar()
        records = self.db.query(Payment).filter(
            Payment.parent_id == parent_id
        ).offset(skip).limit(limit).all()
        return records, total
    
    def create_payment(self, payment_id: str, enrol_id: str, parent_id: str,
                      child_id: str, amount: Decimal, payment_date: date,
                      provider: PaymentProvider, transaction_id: Optional[str] = None,
                      recipient_info: Optional[str] = None) -> Payment:
        """Create a new payment."""
        payment = Payment(
            payment_id=payment_id,
            enrol_id=enrol_id,
            parent_id=parent_id,
            child_id=child_id,
            amount=amount,
            payment_date=payment_date,
            provider=provider,
            transaction_id=transaction_id,
            recipient_info=recipient_info
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        return self.db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
