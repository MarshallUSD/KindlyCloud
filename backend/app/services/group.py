"""Group service."""
import uuid
from typing import Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.models.child import Child
from app.models.group import Group
from app.models.pedagogue import Pedagogue
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository
from app.schemas.group import GroupCreateRequest, GroupUpdateRequest


class GroupService:
    """Service for tenant-safe group management."""

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
            raise NotFoundException("Group not found")
        return group

    def _get_scoped_teacher(self, kindergarten_id: str, teacher_id: str) -> Pedagogue:
        teacher = (
            self.db.query(Pedagogue)
            .filter(Pedagogue.teacher_id == teacher_id, Pedagogue.kindergarten_id == kindergarten_id)
            .first()
        )
        if not teacher:
            raise ValidationException("Teacher not found in your kindergarten")
        return teacher

    def _sync_primary_teacher(self, group: Group, teacher: Pedagogue | None) -> None:
        group.teacher_id = teacher.teacher_id if teacher else None
        if teacher:
            teacher.group_id = group.group_id

    def create_group(self, current_user: User, payload: GroupCreateRequest) -> Group:
        """Create a group for the current kindergarten tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)

        group = Group(
            group_id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            group_name=payload.name,
            age_from=payload.age_from,
            age_to=payload.age_to,
            max_capacity=int(payload.capacity),
            active_time_start=payload.schedule_from,
            active_time_end=payload.schedule_to,
            monthly_fee=float(payload.monthly_fee),
            start_date=current_user.created_at.date(),
        )

        if payload.teacher_id:
            teacher = self._get_scoped_teacher(kindergarten_id, payload.teacher_id)
            self._sync_primary_teacher(group, teacher)

        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def list_groups(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[list[Group], int]:
        """List groups for the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        query = self.db.query(Group).filter(Group.kindergarten_id == kindergarten_id)
        total = query.with_entities(func.count(Group.group_id)).scalar() or 0
        items = query.order_by(Group.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_group(self, current_user: User, group_id: str) -> Group:
        """Get one group scoped to the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        return self._get_scoped_group(kindergarten_id, group_id)

    def update_group(self, current_user: User, group_id: str, payload: GroupUpdateRequest) -> Group:
        """Update a group inside the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        group = self._get_scoped_group(kindergarten_id, group_id)

        data = payload.model_dump(exclude_unset=True, exclude_none=True)
        if "name" in data:
            group.group_name = data["name"]
        if "age_from" in data:
            group.age_from = data["age_from"]
        if "age_to" in data:
            group.age_to = data["age_to"]
        if "capacity" in data:
            child_count = (
                self.db.query(func.count(Child.child_id))
                .filter(Child.group_id == group.group_id, Child.kindergarten_id == kindergarten_id)
                .scalar()
                or 0
            )
            if data["capacity"] < child_count:
                raise ValidationException("Group capacity cannot be lower than current child count")
            group.max_capacity = int(data["capacity"])
        if "schedule_from" in data:
            group.active_time_start = data["schedule_from"]
        if "schedule_to" in data:
            group.active_time_end = data["schedule_to"]
        if "monthly_fee" in data and data["monthly_fee"] is not None:
            group.monthly_fee = float(data["monthly_fee"])

        if "teacher_id" in data:
            if data["teacher_id"]:
                teacher = self._get_scoped_teacher(kindergarten_id, data["teacher_id"])
                self._sync_primary_teacher(group, teacher)
            else:
                if group.teacher_id:
                    old_teacher = (
                        self.db.query(Pedagogue)
                        .filter(
                            Pedagogue.teacher_id == group.teacher_id,
                            Pedagogue.kindergarten_id == kindergarten_id,
                        )
                        .first()
                    )
                    if old_teacher and old_teacher.group_id == group.group_id:
                        old_teacher.group_id = None
                group.teacher_id = None

        self.db.commit()
        self.db.refresh(group)
        return group

    def delete_group(self, current_user: User, group_id: str) -> None:
        """Delete a group when it is no longer referenced."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        group = self._get_scoped_group(kindergarten_id, group_id)

        children_count = (
            self.db.query(func.count(Child.child_id))
            .filter(Child.group_id == group.group_id, Child.kindergarten_id == kindergarten_id)
            .scalar()
            or 0
        )
        teachers_count = (
            self.db.query(func.count(Pedagogue.teacher_id))
            .filter(Pedagogue.group_id == group.group_id, Pedagogue.kindergarten_id == kindergarten_id)
            .scalar()
            or 0
        )
        if children_count or teachers_count:
            raise ValidationException("Group cannot be deleted while children or teachers are assigned")

        self.db.delete(group)
        self.db.commit()
