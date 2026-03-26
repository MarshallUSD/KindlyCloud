"""Shared tenant-aware service helpers."""
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.models.group import Group
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository


class TenantScopedService:
    """Base service with kindergarten tenant helpers."""

    def __init__(self, db: Session):
        self.db = db
        self.kindergarten_repo = KindergartenRepository(db)

    def get_current_kindergarten_id(self, current_user: User) -> str:
        """Resolve tenant id for the current kindergarten user."""
        kindergarten = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kindergarten:
            raise AuthorizationException("User does not belong to a kindergarten")
        return kindergarten.kindergarten_id

    def get_group_for_kindergarten(self, kindergarten_id: str, group_id: str) -> Group:
        """Resolve a group that belongs to the current tenant."""
        group = (
            self.db.query(Group)
            .filter(Group.group_id == group_id, Group.kindergarten_id == kindergarten_id)
            .first()
        )
        if group:
            return group

        foreign_group = self.db.query(Group).filter(Group.group_id == group_id).first()
        if foreign_group:
            raise AuthorizationException("You cannot use a group from another kindergarten")
        raise ValidationException("Group not found in your kindergarten")

    def get_tenant_record_or_raise(
        self,
        model: Any,
        record_field: Any,
        record_id: str,
        kindergarten_field: Any,
        kindergarten_id: str,
        not_found_message: str,
        forbidden_message: str,
    ):
        """Fetch a tenant-scoped record while distinguishing 404 and cross-tenant 403."""
        record = (
            self.db.query(model)
            .filter(record_field == record_id, kindergarten_field == kindergarten_id)
            .first()
        )
        if record:
            return record

        foreign_record = self.db.query(model).filter(record_field == record_id).first()
        if foreign_record:
            raise AuthorizationException(forbidden_message)
        raise NotFoundException(not_found_message)
