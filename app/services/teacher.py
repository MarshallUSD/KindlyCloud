"""Teacher service."""
import uuid
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.models.group import Group
from app.models.pedagogue import Pedagogue
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository
from app.schemas.teacher import TeacherCreateRequest, TeacherUpdateRequest


class TeacherService:
    """Service for tenant-safe teacher management."""

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

    def _get_scoped_teacher(self, kindergarten_id: str, teacher_id: str) -> Pedagogue:
        teacher = (
            self.db.query(Pedagogue)
            .filter(Pedagogue.teacher_id == teacher_id, Pedagogue.kindergarten_id == kindergarten_id)
            .first()
        )
        if not teacher:
            raise NotFoundException("Teacher not found")
        return teacher

    def _sync_group_primary_teacher(self, teacher: Pedagogue, previous_group_id: Optional[str] = None) -> None:
        if previous_group_id and previous_group_id != teacher.group_id:
            previous_group = self.db.query(Group).filter(Group.group_id == previous_group_id).first()
            if previous_group and previous_group.teacher_id == teacher.teacher_id:
                previous_group.teacher_id = None

        if teacher.group_id:
            group = self.db.query(Group).filter(Group.group_id == teacher.group_id).first()
            if group:
                group.teacher_id = teacher.teacher_id

    def create_teacher(self, current_user: User, payload: TeacherCreateRequest) -> Pedagogue:
        """Create a teacher in the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        if payload.group_id:
            self._get_scoped_group(kindergarten_id, payload.group_id)

        teacher = Pedagogue(
            teacher_id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            group_id=payload.group_id,
            full_name=payload.full_name,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            experience_year=payload.experience_year,
        )
        self.db.add(teacher)
        self._sync_group_primary_teacher(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def list_teachers(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        group_id: Optional[str] = None,
    ) -> Tuple[list[Pedagogue], int]:
        """List teachers for the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        query = self.db.query(Pedagogue).filter(Pedagogue.kindergarten_id == kindergarten_id)
        if group_id:
            self._get_scoped_group(kindergarten_id, group_id)
            query = query.filter(Pedagogue.group_id == group_id)
        total = query.with_entities(func.count(Pedagogue.teacher_id)).scalar() or 0
        items = query.order_by(Pedagogue.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_teacher(self, current_user: User, teacher_id: str) -> Pedagogue:
        """Get a teacher scoped to the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        return self._get_scoped_teacher(kindergarten_id, teacher_id)

    def update_teacher(self, current_user: User, teacher_id: str, payload: TeacherUpdateRequest) -> Pedagogue:
        """Update a teacher inside the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        teacher = self._get_scoped_teacher(kindergarten_id, teacher_id)
        previous_group_id = teacher.group_id
        data = payload.model_dump(exclude_unset=True, exclude_none=True)

        if "group_id" in data and data["group_id"]:
            self._get_scoped_group(kindergarten_id, data["group_id"])

        for field in ("full_name", "first_name", "last_name", "phone", "experience_year", "group_id"):
            if field in data:
                setattr(teacher, field, data[field])

        self._sync_group_primary_teacher(teacher, previous_group_id=previous_group_id)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def delete_teacher(self, current_user: User, teacher_id: str) -> None:
        """Delete a teacher scoped to the current tenant."""
        kindergarten_id = self._get_current_kindergarten_id(current_user)
        teacher = self._get_scoped_teacher(kindergarten_id, teacher_id)
        previous_group_id = teacher.group_id
        self.db.delete(teacher)
        if previous_group_id:
            previous_group = self.db.query(Group).filter(Group.group_id == previous_group_id).first()
            if previous_group and previous_group.teacher_id == teacher_id:
                previous_group.teacher_id = None
        self.db.commit()
