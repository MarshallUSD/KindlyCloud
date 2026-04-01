"""Payment service."""
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, ConflictException, NotFoundException, ValidationException
from app.models.child import ParentChildLink
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User
from app.repositories.child import ChildRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.parent import ParentRepository
from app.repositories.payment import PaymentRepository
from app.services.notification import NotificationService


class PaymentService:
    """Service for payment tracking and parent visibility."""

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.child_repo = ChildRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.parent_repo = ParentRepository(db)
        self.notification_service = NotificationService(db)

    def create_payment(
        self,
        current_user: User,
        *,
        child_id: str,
        amount: Decimal,
        due_date: date,
        billing_period: str,
        status: PaymentStatus,
        notes: Optional[str] = None,
        paid_at: Optional[datetime] = None,
        payment_method: Optional[PaymentMethod] = None,
    ) -> Payment:
        """Create a tenant-scoped payment record."""
        kindergarten = self._get_kindergarten_for_user(current_user)
        child = self._get_child_for_kindergarten(child_id, kindergarten.kindergarten_id)
        if self.payment_repo.get_duplicate(
            kindergarten_id=kindergarten.kindergarten_id,
            child_id=child.child_id,
            billing_period=billing_period,
        ):
            raise ConflictException("Payment record for this child and billing period already exists")

        effective_status = self._validate_create_status(status=status, paid_at=paid_at)
        parent_id = self._resolve_primary_parent_id(child.child_id)
        effective_paid_at = paid_at or datetime.now(UTC).replace(tzinfo=None) if effective_status == PaymentStatus.PAID else None
        payment = self.payment_repo.create_payment(
            payment_id=str(uuid.uuid4()),
            kindergarten_id=kindergarten.kindergarten_id,
            child_id=child.child_id,
            parent_id=parent_id,
            billing_period=billing_period,
            amount=amount,
            due_date=due_date,
            status=effective_status,
            notes=notes,
            paid_at=effective_paid_at,
            payment_method=payment_method if effective_status == PaymentStatus.PAID else None,
        )
        self._sync_status(payment)
        self._emit_child_notifications(
            child_id=child.child_id,
            notif_type="payment_created",
            payload={
                "payment_id": payment.payment_id,
                "child_id": child.child_id,
                "billing_period": payment.billing_period,
                "amount": str(payment.amount),
                "due_date": payment.due_date.isoformat(),
                "status": payment.status.value,
            },
        )
        return payment

    def list_payments_for_kindergarten(
        self,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
        child_id: Optional[str] = None,
        group_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        billing_period: Optional[str] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
    ) -> tuple[list[Payment], int]:
        """List payments for the current tenant."""
        kindergarten = self._get_kindergarten_for_user(current_user)
        self._sync_overdue_for_kindergarten(kindergarten.kindergarten_id)
        return self.payment_repo.list_for_kindergarten(
            kindergarten_id=kindergarten.kindergarten_id,
            skip=skip,
            limit=limit,
            child_id=child_id,
            group_id=group_id,
            status=status,
            billing_period=billing_period,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
        )

    def get_payment_for_kindergarten(self, current_user: User, payment_id: str) -> Payment:
        """Get one payment while enforcing tenant isolation."""
        kindergarten = self._get_kindergarten_for_user(current_user)
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")
        if payment.kindergarten_id != kindergarten.kindergarten_id:
            raise AuthorizationException("You do not have access to this payment")
        return self._sync_status(payment)

    def update_payment(
        self,
        current_user: User,
        payment_id: str,
        *,
        amount: Optional[Decimal] = None,
        due_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Payment:
        """Update an unpaid payment record."""
        payment = self.get_payment_for_kindergarten(current_user, payment_id)
        if payment.status == PaymentStatus.PAID:
            raise ValidationException("Paid records cannot be modified")
        changes = {}
        if amount is not None:
            changes["amount"] = amount
        if due_date is not None:
            changes["due_date"] = due_date
        if notes is not None:
            changes["notes"] = notes
        payment = self.payment_repo.update_payment(payment, **changes)
        return self._sync_status(payment)

    def mark_paid(
        self,
        current_user: User,
        payment_id: str,
        *,
        paid_at: Optional[datetime] = None,
        payment_method: Optional[PaymentMethod] = None,
    ) -> Payment:
        """Mark a payment record as paid."""
        payment = self.get_payment_for_kindergarten(current_user, payment_id)
        if payment.status == PaymentStatus.PAID:
            return payment

        timestamp = paid_at or datetime.now(UTC).replace(tzinfo=None)
        payment = self.payment_repo.update_payment(
            payment,
            status=PaymentStatus.PAID,
            paid_at=timestamp,
            payment_method=payment_method,
        )
        self._emit_child_notifications(
            child_id=payment.child_id,
            notif_type="payment_paid",
            payload={
                "payment_id": payment.payment_id,
                "child_id": payment.child_id,
                "billing_period": payment.billing_period,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                "payment_method": payment.payment_method.value if payment.payment_method else None,
            },
        )
        return payment

    def confirm_payment_submission(
        self,
        current_user: User,
        *,
        payment_id: str,
        approved_at: Optional[datetime] = None,
    ) -> Payment:
        """Confirm a payment after staff approves a parent submission."""
        payment = self.get_payment_for_kindergarten(current_user, payment_id)
        if payment.status == PaymentStatus.PAID:
            return payment
        return self.mark_paid(
            current_user,
            payment_id,
            paid_at=approved_at,
            payment_method=payment.payment_method,
        )

    def list_payments_for_parent(
        self,
        current_user: User,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Payment], int]:
        """List payments for the current parent."""
        parent = self._get_parent_for_user(current_user)
        items, total = self.payment_repo.list_for_parent(parent_id=parent.parent_id, skip=skip, limit=limit)
        synced = [self._sync_status(payment) for payment in items]
        return synced, total

    def get_payment_for_parent(self, current_user: User, payment_id: str) -> Payment:
        """Get one payment for the current parent."""
        parent = self._get_parent_for_user(current_user)
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")
        visible = self.payment_repo.payment_visible_to_parent(payment_id, parent.parent_id)
        if not visible:
            raise AuthorizationException("You do not have access to this payment")
        return self._sync_status(visible)

    def _get_kindergarten_for_user(self, current_user: User):
        kindergarten = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kindergarten:
            raise NotFoundException("Kindergarten not found for current user")
        return kindergarten

    def _get_parent_for_user(self, current_user: User):
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise NotFoundException("Parent profile not found")
        return parent

    def _get_child_for_kindergarten(self, child_id: str, kindergarten_id: str):
        child = self.child_repo.get_by_id(child_id)
        if not child:
            raise NotFoundException("Child not found")
        if child.kindergarten_id != kindergarten_id:
            raise AuthorizationException("You do not have access to this child")
        return child

    def _validate_create_status(self, *, status: PaymentStatus, paid_at: Optional[datetime]) -> PaymentStatus:
        if status == PaymentStatus.OVERDUE:
            raise ValidationException("Payments cannot be created directly as overdue")
        if status == PaymentStatus.PAID and paid_at is None:
            return PaymentStatus.PAID
        if status == PaymentStatus.PENDING:
            return PaymentStatus.PENDING
        return status

    def _resolve_primary_parent_id(self, child_id: str) -> Optional[str]:
        row = (
            self.db.query(ParentChildLink.parent_id)
            .filter(
                ParentChildLink.child_id == child_id,
                ParentChildLink.status == "active",
            )
            .first()
        )
        return row[0] if row else None

    def _sync_overdue_for_kindergarten(self, kindergarten_id: str) -> None:
        for payment in self.payment_repo.get_latest_for_overdue_scan(kindergarten_id):
            self._sync_status(payment)

    def _sync_status(self, payment: Payment) -> Payment:
        computed_status = payment.effective_status
        if payment.status == computed_status:
            return payment
        previous_status = payment.status
        payment = self.payment_repo.update_payment(payment, status=computed_status)
        if previous_status != PaymentStatus.OVERDUE and computed_status == PaymentStatus.OVERDUE:
            self._emit_child_notifications(
                child_id=payment.child_id,
                notif_type="payment_overdue",
                payload={
                    "payment_id": payment.payment_id,
                    "child_id": payment.child_id,
                    "billing_period": payment.billing_period,
                    "due_date": payment.due_date.isoformat(),
                    "status": payment.status.value,
                },
            )
        return payment

    def _emit_child_notifications(self, *, child_id: str, notif_type: str, payload: dict) -> None:
        user_ids = self.payment_repo.get_parent_user_ids_for_child(child_id)
        if not user_ids:
            return
        self.notification_service.create_bulk(user_ids=user_ids, notif_type=notif_type, payload=payload)
