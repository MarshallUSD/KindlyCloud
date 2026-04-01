"""Staff service."""
import uuid
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.pedagogue import Pedagogue
from app.models.user import User
from app.schemas.staff import StaffCreate, StaffUpdate
from app.services.tenant_scope import TenantScopedService


class StaffService(TenantScopedService):
    """Service for tenant-safe staff management."""

    def __init__(self, db: Session):
        super().__init__(db)

    def _get_scoped_staff(self, kindergarten_id: str, staff_id: str) -> Pedagogue:
        return self.get_tenant_record_or_raise(
            model=Pedagogue,
            record_field=Pedagogue.teacher_id,
            record_id=staff_id,
            kindergarten_field=Pedagogue.kindergarten_id,
            kindergarten_id=kindergarten_id,
            not_found_message="Staff member not found",
            forbidden_message="You cannot access another kindergarten's staff member",
        )

    def _sync_group_assignment(self, staff: Pedagogue, previous_group_id: Optional[str] = None) -> None:
        if previous_group_id and previous_group_id != staff.group_id:
            previous_group = self.db.query(Group).filter(Group.group_id == previous_group_id).first()
            if previous_group and previous_group.teacher_id == staff.teacher_id:
                previous_group.teacher_id = None

        if staff.group_id:
            group = self.db.query(Group).filter(Group.group_id == staff.group_id).first()
            if group:
                group.teacher_id = staff.teacher_id

    def create_staff(self, current_user: User, payload: StaffCreate) -> Pedagogue:
        """Create a staff member in the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        if payload.group_id:
            self.get_group_for_kindergarten(kindergarten_id, payload.group_id)

        staff = Pedagogue(
            teacher_id=str(uuid.uuid4()),
            kindergarten_id=kindergarten_id,
            group_id=payload.group_id,
            full_name=payload.full_name,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            role=payload.role,
            salary=payload.salary,
            hired_at=payload.hired_at,
        )
        self.db.add(staff)
        self._sync_group_assignment(staff)
        self.db.commit()
        self.db.refresh(staff)
        return staff

    def get_staff(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 20,
        group_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[list[Pedagogue], int]:
        """List staff for the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        query = self.db.query(Pedagogue).filter(Pedagogue.kindergarten_id == kindergarten_id)
        if group_id:
            self.get_group_for_kindergarten(kindergarten_id, group_id)
            query = query.filter(Pedagogue.group_id == group_id)
        if search:
            query = query.filter(Pedagogue.full_name.ilike(f"%{search.strip()}%"))

        total = query.with_entities(func.count(Pedagogue.teacher_id)).scalar() or 0
        items = query.order_by(Pedagogue.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_staff_member(self, current_user: User, staff_id: str) -> Pedagogue:
        """Get one staff member scoped to the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        return self._get_scoped_staff(kindergarten_id, staff_id)

    def update_staff(self, current_user: User, staff_id: str, payload: StaffUpdate) -> Pedagogue:
        """Update a staff member inside the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        staff = self._get_scoped_staff(kindergarten_id, staff_id)
        previous_group_id = staff.group_id
        data = payload.model_dump(exclude_unset=True)

        if "group_id" in data and data["group_id"]:
            self.get_group_for_kindergarten(kindergarten_id, data["group_id"])

        for field in ("full_name", "first_name", "last_name", "phone", "role", "salary", "hired_at", "group_id"):
            if field in data:
                setattr(staff, field, data[field])

        self._sync_group_assignment(staff, previous_group_id=previous_group_id)
        self.db.commit()
        self.db.refresh(staff)
        return staff

    def delete_staff(self, current_user: User, staff_id: str) -> None:
        """Delete a staff member scoped to the current tenant."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        staff = self._get_scoped_staff(kindergarten_id, staff_id)
        previous_group_id = staff.group_id
        self.db.delete(staff)
        if previous_group_id:
            previous_group = self.db.query(Group).filter(Group.group_id == previous_group_id).first()
            if previous_group and previous_group.teacher_id == staff_id:
                previous_group.teacher_id = None
        self.db.commit()
