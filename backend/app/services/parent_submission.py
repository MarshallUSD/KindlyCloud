"""Service layer for parent submissions and Telegram bot intake."""
from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from config import settings
from app.core.exceptions import AuthenticationException, AuthorizationException, NotFoundException, ValidationException
from app.models.child import Child, ParentChildLink
from app.models.parent import Parent
from app.models.parent_submission import ParentSubmission, ParentSubmissionStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.parent import ParentRepository
from app.repositories.parent_submission import ParentSubmissionRepository
from app.repositories.payment import PaymentRepository
from app.services.payment import PaymentService


class ParentSubmissionService:
    """Manage one-way parent submissions for kindergarten review."""

    def __init__(self, db: Session):
        self.db = db
        self.kindergarten_repo = KindergartenRepository(db)
        self.parent_repo = ParentRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.submission_repo = ParentSubmissionRepository(db)
        self.payment_service = PaymentService(db)

    def authenticate_integration_request(self, provided_secret: str | None) -> None:
        """Validate the Telegram integration secret."""
        configured_secret = settings.TELEGRAM_PARENT_SUBMISSIONS_SECRET
        if not configured_secret:
            raise AuthenticationException("Telegram parent submissions secret is not configured")
        if not provided_secret or not secrets.compare_digest(provided_secret, configured_secret):
            raise AuthenticationException("Invalid integration secret")

    def ingest_submission(self, payload) -> ParentSubmission:
        """Create a new parent submission from the Telegram bot integration."""
        kindergarten = self.kindergarten_repo.get_by_id(payload.kindergarten_id)
        if not kindergarten:
            raise NotFoundException("Kindergarten not found")

        parent = self._resolve_parent(payload.parent_id, payload.parent_telegram_id)
        active_child_ids = self._get_active_child_ids_for_parent_in_kindergarten(
            parent_id=parent.parent_id,
            kindergarten_id=kindergarten.kindergarten_id,
        )
        if not active_child_ids:
            raise ValidationException("Parent is not linked to the specified kindergarten")

        payment = None
        child = None
        if payload.payment_id:
            payment = self._get_payment_for_kindergarten(payload.payment_id, kindergarten.kindergarten_id)
            if payment.child_id not in active_child_ids and payment.parent_id != parent.parent_id:
                raise ValidationException("Payment does not belong to the provided parent context")
            child = payment.child

        if payload.child_id:
            child = self._get_child_for_kindergarten(payload.child_id, kindergarten.kindergarten_id)
            if child.child_id not in active_child_ids:
                raise ValidationException("Child is not linked to the provided parent")
            if payment and payment.child_id != child.child_id:
                raise ValidationException("Payment and child reference do not match")

        if not child and payment:
            child = payment.child

        submission = self.submission_repo.create_submission(
            id=str(uuid.uuid4()),
            kindergarten_id=kindergarten.kindergarten_id,
            parent_id=parent.parent_id,
            child_id=child.child_id if child else None,
            payment_id=payment.payment_id if payment else None,
            source=payload.source,
            submission_type=payload.submission_type,
            text=payload.text,
            attachment_url=payload.attachment_url,
            attachment_type=payload.attachment_type,
            status=ParentSubmissionStatus.PENDING,
        )
        return submission

    def list_for_kindergarten(self, current_user: User, filters) -> tuple[list[ParentSubmission], int]:
        """List submissions for the current tenant."""
        kindergarten = self._get_kindergarten_for_user(current_user)
        return self.submission_repo.list_for_kindergarten(
            kindergarten_id=kindergarten.kindergarten_id,
            page=filters.page,
            size=filters.size,
            status=filters.status,
            submission_type=filters.submission_type,
            parent_id=filters.parent_id,
            child_id=filters.child_id,
            payment_id=filters.payment_id,
            date_from=filters.datetime_from(),
            date_to=filters.datetime_to(),
        )

    def get_for_kindergarten(self, current_user: User, submission_id: str) -> ParentSubmission:
        """Resolve one tenant-scoped submission."""
        kindergarten = self._get_kindergarten_for_user(current_user)
        submission = self.submission_repo.get_by_id(submission_id)
        if not submission:
            raise NotFoundException("Parent submission not found")
        if submission.kindergarten_id != kindergarten.kindergarten_id:
            raise AuthorizationException("You do not have access to this parent submission")
        return submission

    def review_submission(self, current_user: User, submission_id: str, *, action, admin_note: str | None) -> ParentSubmission:
        """Review, approve, or reject a parent submission."""
        submission = self.get_for_kindergarten(current_user, submission_id)
        self._validate_review_transition(submission.status, action)

        if submission.status == action:
            if admin_note != submission.admin_note:
                return self.submission_repo.update_submission(
                    submission,
                    admin_note=admin_note,
                    reviewed_by=current_user.user_id,
                    reviewed_at=submission.reviewed_at or datetime.now(UTC).replace(tzinfo=None),
                )
            return submission

        reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        submission = self.submission_repo.update_submission(
            submission,
            status=action,
            admin_note=admin_note,
            reviewed_by=current_user.user_id,
            reviewed_at=reviewed_at,
        )

        if action == ParentSubmissionStatus.APPROVED and submission.payment_id:
            self.payment_service.confirm_payment_submission(
                current_user,
                payment_id=submission.payment_id,
                approved_at=reviewed_at,
            )
            submission = self.submission_repo.get_by_id(submission.id)

        return submission

    def _resolve_parent(self, parent_id: str | None, parent_telegram_id: str | None) -> Parent:
        if parent_id:
            parent = self.parent_repo.get_by_id(parent_id)
            if not parent:
                raise NotFoundException("Parent not found")
            return parent
        parent = self.parent_repo.get_by_telegram_id(parent_telegram_id)
        if not parent:
            raise NotFoundException("Parent not found for telegram identifier")
        return parent

    def _get_kindergarten_for_user(self, current_user: User):
        kindergarten = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kindergarten:
            raise NotFoundException("Kindergarten not found for current user")
        return kindergarten

    def _get_active_child_ids_for_parent_in_kindergarten(self, *, parent_id: str, kindergarten_id: str) -> set[str]:
        rows = (
            self.db.query(Child.child_id)
            .join(ParentChildLink, ParentChildLink.child_id == Child.child_id)
            .filter(
                ParentChildLink.parent_id == parent_id,
                ParentChildLink.status == "active",
                Child.kindergarten_id == kindergarten_id,
            )
            .all()
        )
        return {row[0] for row in rows}

    def _get_child_for_kindergarten(self, child_id: str, kindergarten_id: str) -> Child:
        child = self.db.query(Child).filter(Child.child_id == child_id).first()
        if not child:
            raise NotFoundException("Child not found")
        if child.kindergarten_id != kindergarten_id:
            raise ValidationException("Child does not belong to the specified kindergarten")
        return child

    def _get_payment_for_kindergarten(self, payment_id: str, kindergarten_id: str) -> Payment:
        payment = self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")
        if payment.kindergarten_id != kindergarten_id:
            raise ValidationException("Payment does not belong to the specified kindergarten")
        return payment

    def _validate_review_transition(self, current_status, next_status) -> None:
        allowed_transitions = {
            ParentSubmissionStatus.PENDING: {
                ParentSubmissionStatus.REVIEWED,
                ParentSubmissionStatus.APPROVED,
                ParentSubmissionStatus.REJECTED,
            },
            ParentSubmissionStatus.REVIEWED: {
                ParentSubmissionStatus.REVIEWED,
                ParentSubmissionStatus.APPROVED,
                ParentSubmissionStatus.REJECTED,
            },
            ParentSubmissionStatus.APPROVED: {ParentSubmissionStatus.APPROVED},
            ParentSubmissionStatus.REJECTED: {ParentSubmissionStatus.REJECTED},
        }
        if next_status not in allowed_transitions[current_status]:
            raise ValidationException(
                f"Cannot change submission status from {current_status.value} to {next_status.value}"
            )
