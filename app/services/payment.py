"""Payment service."""
import uuid
from typing import Optional, List, Tuple
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.models.user import User
from app.repositories.payment import PaymentRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.parent import ParentRepository
from app.repositories.child import ChildRepository
from app.core.exceptions import NotFoundException


class PaymentService:
    """Service for payment management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)
        self.parent_repo = ParentRepository(db)
        self.child_repo = ChildRepository(db)
    
    def create_payment(self, current_user: User, enrol_id: str, amount: Decimal,
                      payment_date: date, provider: PaymentProvider,
                      transaction_id: Optional[str] = None) -> Payment:
        """Create a payment."""
        enrollment = self.enrollment_repo.get_by_id(enrol_id)
        if not enrollment:
            raise NotFoundException("Enrollment not found")
        
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise NotFoundException("Parent profile not found")
        
        child = self.child_repo.get_by_id(enrollment.child_id)
        if not child:
            raise NotFoundException("Child not found")
        linked_child_ids = {linked_child.child_id for linked_child in self.child_repo.get_children_by_parent(parent.parent_id, active_only=True)}
        if child.child_id not in linked_child_ids:
            raise NotFoundException("Child is not linked to this parent")

        payment_id = str(uuid.uuid4())
        payment = self.payment_repo.create_payment(
            payment_id=payment_id,
            enrol_id=enrol_id,
            parent_id=parent.parent_id,
            child_id=child.child_id,
            amount=amount,
            payment_date=payment_date,
            provider=provider,
            transaction_id=transaction_id
        )
        
        # Update enrollment amount paid
        new_amount_paid = enrollment.amount_paid + amount
        self.enrollment_repo.update_balance(enrol_id, new_amount_paid)
        
        return payment
    
    def get_payment(self, payment_id: str) -> Payment:
        """Get payment by ID."""
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")
        return payment
    
    def list_payments_for_parent(self, current_user: User, skip: int = 0,
                                 limit: int = 20) -> Tuple[List[Payment], int]:
        """List payments for parent."""
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise NotFoundException("Parent profile not found")
        
        return self.payment_repo.get_by_parent(parent.parent_id, skip=skip, limit=limit)
    
    def list_payments_for_enrollment(self, enrol_id: str, skip: int = 0,
                                     limit: int = 20) -> Tuple[List[Payment], int]:
        """List payments for an enrollment."""
        return self.payment_repo.get_by_enrollment(enrol_id, skip=skip, limit=limit)
