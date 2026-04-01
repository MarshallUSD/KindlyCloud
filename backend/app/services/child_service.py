"""Child service."""
import uuid
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.models.child import Child
from app.models.user import User
from app.schemas.child import ChildCreate, ChildUpdate
from app.services.tenant_scope import TenantScopedService


class ChildService(TenantScopedService):
    """Service for tenant-safe child management."""

    def __init__(self, db: Session):
        super().__init__(db)

    def _get_scoped_child(self, kindergarten_id: str, child_id: str) -> Child:
        return self.get_tenant_record_or_raise(
            model=Child,
            record_field=Child.child_id,
            record_id=child_id,
            kindergarten_field=Child.kindergarten_id,
            kindergarten_id=kindergarten_id,
            not_found_message="Child not found",
            forbidden_message="You cannot access another kindergarten's child",
        )

    def _validate_group_capacity(self, kindergarten_id: str, group_id: str, child_id: Optional[str] = None) -> None:
        group = self.get_group_for_kindergarten(kindergarten_id, group_id)
        if group.max_capacity is None:
            return

        query = self.db.query(func.count(Child.child_id)).filter(
            Child.kindergarten_id == kindergarten_id,
            Child.group_id == group_id,
        )
        if child_id:
            query = query.filter(Child.child_id != child_id)

        current_count = query.scalar() or 0
        if current_count >= group.max_capacity:
            raise ValidationException("Group capacity has been reached")

    def create_child(self, current_user: User, payload: ChildCreate) -> Child:
        """Create a child in the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        self._validate_group_capacity(kindergarten_id, payload.group_id)

        child = Child(
            child_id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            group_id=payload.group_id,
            full_name=payload.full_name,
            first_name=payload.first_name,
            last_name=payload.last_name,
            birth_date=payload.birth_date,
            gender=payload.gender,
            parent_phone=payload.parent_phone,
            notes=payload.notes,
            address=payload.address,
        )
        self.db.add(child)
        self.db.commit()
        self.db.refresh(child)
        return child

    def get_children(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        group_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[list[Child], int]:
        """List children for the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        query = self.db.query(Child).filter(Child.kindergarten_id == kindergarten_id)
        if group_id:
            self.get_group_for_kindergarten(kindergarten_id, group_id)
            query = query.filter(Child.group_id == group_id)
        if search:
            query = query.filter(Child.full_name.ilike(f"%{search.strip()}%"))

        total = query.with_entities(func.count(Child.child_id)).scalar() or 0
        items = query.order_by(Child.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_child(self, current_user: User, child_id: str) -> Child:
        """Get a child scoped to the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        return self._get_scoped_child(kindergarten_id, child_id)

    def update_child(self, current_user: User, child_id: str, payload: ChildUpdate) -> Child:
        """Update a child inside the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        child = self._get_scoped_child(kindergarten_id, child_id)
        data = payload.model_dump(exclude_unset=True)

        if "group_id" in data and data["group_id"] is not None and data["group_id"] != child.group_id:
            self._validate_group_capacity(kindergarten_id, data["group_id"], child_id=child.child_id)
            self.get_group_for_kindergarten(kindergarten_id, data["group_id"])
            child.group_id = data["group_id"]

        for field in ("full_name", "first_name", "last_name", "birth_date", "gender", "parent_phone", "notes", "address"):
            if field in data:
                setattr(child, field, data[field])

        self.db.commit()
        self.db.refresh(child)
        return child

    def delete_child(self, current_user: User, child_id: str) -> None:
        """Delete a child scoped to the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        child = self._get_scoped_child(kindergarten_id, child_id)
        self.db.delete(child)
        self.db.commit()
