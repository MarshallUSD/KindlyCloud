"""Repository helpers for parent submissions."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.parent_submission import ParentSubmission, ParentSubmissionStatus, ParentSubmissionType
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class ParentSubmissionRepository(BaseRepository):
    """Persistence operations for tenant-scoped parent submissions."""

    def __init__(self, db: Session):
        super().__init__(db, ParentSubmission)

    def base_query(self):
        """Return the default eager-loaded submission query."""
        return self.db.query(ParentSubmission).options(
            joinedload(ParentSubmission.parent),
            joinedload(ParentSubmission.child),
            joinedload(ParentSubmission.payment).joinedload(Payment.child),
            joinedload(ParentSubmission.reviewer),
        )

    def get_by_id(self, submission_id: str) -> Optional[ParentSubmission]:
        """Get one submission by id."""
        return self.base_query().filter(ParentSubmission.id == submission_id).first()

    def create_submission(self, **data) -> ParentSubmission:
        """Persist a new parent submission."""
        submission = ParentSubmission(**data)
        self.db.add(submission)
        self.db.commit()
        return self.get_by_id(submission.id)

    def update_submission(self, submission: ParentSubmission, **changes) -> ParentSubmission:
        """Persist changes to an existing submission."""
        for key, value in changes.items():
            setattr(submission, key, value)
        self.db.add(submission)
        self.db.commit()
        return self.get_by_id(submission.id)

    def list_for_kindergarten(
        self,
        *,
        kindergarten_id: str,
        page: int,
        size: int,
        status: Optional[ParentSubmissionStatus] = None,
        submission_type: Optional[ParentSubmissionType] = None,
        parent_id: Optional[str] = None,
        child_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[ParentSubmission], int]:
        """List submissions for one tenant with optional filters."""
        query = self._apply_filters(
            kindergarten_id=kindergarten_id,
            status=status,
            submission_type=submission_type,
            parent_id=parent_id,
            child_id=child_id,
            payment_id=payment_id,
            date_from=date_from,
            date_to=date_to,
        )
        total = query.with_entities(func.count(ParentSubmission.id)).scalar() or 0
        offset = (page - 1) * size
        items = (
            query
            .order_by(ParentSubmission.created_at.desc(), ParentSubmission.id.desc())
            .offset(offset)
            .limit(size)
            .all()
        )
        return items, total

    def _apply_filters(
        self,
        *,
        kindergarten_id: str,
        status: Optional[ParentSubmissionStatus] = None,
        submission_type: Optional[ParentSubmissionType] = None,
        parent_id: Optional[str] = None,
        child_id: Optional[str] = None,
        payment_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        query = self.base_query().filter(ParentSubmission.kindergarten_id == kindergarten_id)
        if status:
            query = query.filter(ParentSubmission.status == status)
        if submission_type:
            query = query.filter(ParentSubmission.submission_type == submission_type)
        if parent_id:
            query = query.filter(ParentSubmission.parent_id == parent_id)
        if child_id:
            query = query.filter(ParentSubmission.child_id == child_id)
        if payment_id:
            query = query.filter(ParentSubmission.payment_id == payment_id)
        if date_from:
            query = query.filter(ParentSubmission.created_at >= date_from)
        if date_to:
            query = query.filter(ParentSubmission.created_at <= date_to)
        return query
