"""Payment repository."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.child import Child, ParentChildLink
from app.models.parent import ParentUser
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    """Repository for payment tracking records."""

    def __init__(self, db: Session):
        super().__init__(db, Payment)

    def base_query(self):
        """Return the default eager-loaded payment query."""
        return self.db.query(Payment).options(
            joinedload(Payment.child).joinedload(Child.group),
            joinedload(Payment.parent),
        )

    def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get payment by identifier."""
        return self.base_query().filter(Payment.payment_id == payment_id).first()

    def get_duplicate(
        self,
        *,
        kindergarten_id: str,
        child_id: str,
        billing_period: str,
        exclude_payment_id: Optional[str] = None,
    ) -> Optional[Payment]:
        """Find an existing payment record for the same billing period."""
        query = self.base_query().filter(
            Payment.kindergarten_id == kindergarten_id,
            Payment.child_id == child_id,
            Payment.billing_period == billing_period,
        )
        if exclude_payment_id:
            query = query.filter(Payment.payment_id != exclude_payment_id)
        return query.first()

    def create_payment(
        self,
        *,
        payment_id: str,
        kindergarten_id: str,
        child_id: str,
        parent_id: Optional[str],
        billing_period: str,
        amount: Decimal,
        due_date: date,
        status: PaymentStatus,
        notes: Optional[str],
        paid_at: Optional[datetime],
        payment_method: Optional[PaymentMethod],
    ) -> Payment:
        """Create a new payment record."""
        payment = Payment(
            payment_id=payment_id,
            kindergarten_id=kindergarten_id,
            child_id=child_id,
            parent_id=parent_id,
            billing_period=billing_period,
            amount=amount,
            due_date=due_date,
            status=status,
            notes=notes,
            paid_at=paid_at,
            payment_method=payment_method,
        )
        self.db.add(payment)
        self.db.commit()
        return self.get_by_id(payment_id)

    def update_payment(self, payment: Payment, **changes) -> Payment:
        """Persist updates on a payment record."""
        for key, value in changes.items():
            setattr(payment, key, value)
        self.db.add(payment)
        self.db.commit()
        return self.get_by_id(payment.payment_id)

    def list_for_kindergarten(
        self,
        *,
        kindergarten_id: str,
        skip: int,
        limit: int,
        child_id: Optional[str] = None,
        group_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        billing_period: Optional[str] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
    ) -> tuple[list[Payment], int]:
        """List tenant-scoped payments with filters."""
        query = self._apply_kindergarten_filters(
            kindergarten_id=kindergarten_id,
            child_id=child_id,
            group_id=group_id,
            status=status,
            billing_period=billing_period,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
        )
        total = query.with_entities(func.count(Payment.payment_id)).scalar() or 0
        items = query.order_by(Payment.due_date.desc(), Payment.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def list_for_parent(
        self,
        *,
        parent_id: str,
        skip: int,
        limit: int,
    ) -> tuple[list[Payment], int]:
        """List payments visible to one parent through linked children."""
        query = (
            self.base_query()
            .join(ParentChildLink, ParentChildLink.child_id == Payment.child_id)
            .filter(
                ParentChildLink.parent_id == parent_id,
                ParentChildLink.status == "active",
            )
        )
        total = query.with_entities(func.count(func.distinct(Payment.payment_id))).scalar() or 0
        items = (
            query
            .order_by(Payment.due_date.desc(), Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def payment_visible_to_parent(self, payment_id: str, parent_id: str) -> Optional[Payment]:
        """Get one payment if the parent has an active child link."""
        return (
            self.base_query()
            .join(ParentChildLink, ParentChildLink.child_id == Payment.child_id)
            .filter(
                Payment.payment_id == payment_id,
                ParentChildLink.parent_id == parent_id,
                ParentChildLink.status == "active",
            )
            .first()
        )

    def report_records(
        self,
        *,
        kindergarten_id: str,
        from_date: date,
        to_date: date,
        group_id: Optional[str] = None,
    ) -> list[Payment]:
        """Return records for reporting over a due-date range."""
        query = self._apply_kindergarten_filters(
            kindergarten_id=kindergarten_id,
            group_id=group_id,
            due_date_from=from_date,
            due_date_to=to_date,
        )
        return query.order_by(Payment.due_date.asc(), Payment.created_at.asc()).all()

    def get_parent_user_ids_for_child(self, child_id: str) -> list[int]:
        """Resolve user ids for parents linked to a child."""
        rows = (
            self.db.query(ParentUser.user_id)
            .join(ParentChildLink, ParentChildLink.parent_id == ParentUser.parent_id)
            .filter(
                ParentChildLink.child_id == child_id,
                ParentChildLink.status == "active",
            )
            .all()
        )
        return [row[0] for row in rows]

    def get_latest_for_overdue_scan(self, kindergarten_id: str) -> list[Payment]:
        """Return unpaid records for a tenant to evaluate overdue transitions."""
        return (
            self.base_query()
            .filter(
                Payment.kindergarten_id == kindergarten_id,
                Payment.status != PaymentStatus.PAID,
            )
            .all()
        )

    def _apply_kindergarten_filters(
        self,
        *,
        kindergarten_id: str,
        child_id: Optional[str] = None,
        group_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        billing_period: Optional[str] = None,
        due_date_from: Optional[date] = None,
        due_date_to: Optional[date] = None,
    ):
        query = self.base_query().filter(Payment.kindergarten_id == kindergarten_id)
        if child_id:
            query = query.filter(Payment.child_id == child_id)
        if group_id:
            query = query.join(Child, Child.child_id == Payment.child_id).filter(Child.group_id == group_id)
        if status:
            query = query.filter(Payment.status == status)
        if billing_period:
            query = query.filter(Payment.billing_period == billing_period)
        if due_date_from:
            query = query.filter(Payment.due_date >= due_date_from)
        if due_date_to:
            query = query.filter(Payment.due_date <= due_date_to)
        return query
