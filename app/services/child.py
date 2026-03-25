"""Child service."""
import uuid
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.models.child import Child
from app.models.group import Group
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository
from app.schemas.child import ChildCreateRequest, ChildUpdateRequest


class ChildService:
    """Service for tenant-safe child management."""

    def __init__(self, db: Session):
        self.db = db
        self.kindergarten_repo = KindergartenRepository(db)

    def _get_current_kindergarten_id(self, current_user: User) -> str:
        kindergarten = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kindergarten:
            raise AuthorizationException("User does not belong to a kindergarten")
        return kindergarten.kindergarten_id

    def _get_scoped_group(self, kindergarten_id: str, group_id: str) -> Group:
        group = (
            self.db.query(Group)
            .filter(Group.group_id == group_id, Group.kindergarten_id == kindergarten_id)
            .first()
        )
        if not group:
            raise ValidationException("Group not found in your kindergarten")
        return group

    def _get_scoped_child(self, kindergarten_id: str, child_id: str) -> Child:
        child = (
            self.db.query(Child)
            .filter(Child.child_id == child_id, Child.kindergarten_id == kindergarten_id)
            .first()
        )
        if not child:
            raise NotFoundException("Child not found")
        return child

    def _validate_group_capacity(self, kindergarten_id: str, group_id: str, child_id: Optional[str] = None) -> None:
        group = self._get_scoped_group(kindergarten_id, group_id)
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

    def create_child(self, current_user: User, payload: ChildCreateRequest) -> Child:
        """Create a child in the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        self._validate_group_capacity(kindergarten_id, payload.group_id)

        child = Child(
            child_id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            group_id=payload.group_id,
            full_name=payload.full_name,
            first_name=payload.first_name,
            last_name=payload.last_name,
            birth_date=payload.birth_date,
            parent_phone=payload.parent_phone,
            gender=payload.gender,
            address=payload.address,
        )
        self.db.add(child)
        self.db.commit()
        self.db.refresh(child)
        return child

    def list_children(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        group_id: Optional[str] = None,
    ) -> Tuple[list[Child], int]:
        """List children for the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        query = self.db.query(Child).filter(Child.kindergarten_id == kindergarten_id)
        if group_id:
            self._get_scoped_group(kindergarten_id, group_id)
            query = query.filter(Child.group_id == group_id)
        total = query.with_entities(func.count(Child.child_id)).scalar() or 0
        items = query.order_by(Child.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_child(self, current_user: User, child_id: str) -> Child:
        """Get a child scoped to the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        return self._get_scoped_child(kindergarten_id, child_id)

    def update_child(self, current_user: User, child_id: str, payload: ChildUpdateRequest) -> Child:
        """Update a child inside the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        child = self._get_scoped_child(kindergarten_id, child_id)
        data = payload.model_dump(exclude_unset=True, exclude_none=True)

        target_group_id = data.get("group_id", child.group_id)
        if target_group_id != child.group_id:
            self._validate_group_capacity(kindergarten_id, target_group_id, child_id=child.child_id)
            self._get_scoped_group(kindergarten_id, target_group_id)
            child.group_id = target_group_id

        for field in ("full_name", "first_name", "last_name", "birth_date", "parent_phone", "gender", "address"):
            if field in data:
                setattr(child, field, data[field])

        self.db.commit()
        self.db.refresh(child)
        return child

    def delete_child(self, current_user: User, child_id: str) -> None:
        """Delete a child scoped to the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        child = self._get_scoped_child(kindergarten_id, child_id)
        self.db.delete(child)
        self.db.commit()
