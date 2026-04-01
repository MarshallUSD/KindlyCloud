"""Parent read services."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.models.attendance import Attendance, AttendanceStatus
from app.models.child import Child, ParentChildLink
from app.models.group import Group
from app.models.menu import Menu
from app.models.parent import Parent
from app.models.payment import Payment
from app.models.pedagogue import Pedagogue
from app.models.user import User
from app.repositories.child import ChildRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.menu import MenuRepository
from app.repositories.parent import ParentRepository
from app.repositories.payment import PaymentRepository
from app.schemas.parent import (
    ParentAttendanceItemResponse,
    ParentDashboardAttendanceStatus,
    ParentDashboardChildItem,
    ParentDashboardResponse,
    ParentGroupSummary,
    ParentLatestPaymentSummary,
    ParentMenuItemResponse,
    ParentMenuResponse,
    ParentPedagogueSummary,
)
from app.services.notification import NotificationService


class ParentService:
    """Service for parent management and parent read layer."""

    def __init__(self, db: Session):
        self.db = db
        self.parent_repo = ParentRepository(db)
        self.child_repo = ChildRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.menu_repo = MenuRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.notification_service = NotificationService(db)

    def create_parent(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
        birth_date=None,
    ) -> Parent:
        """Create a new parent profile."""
        parent_id = str(uuid.uuid4())
        return self.parent_repo.create_parent(
            parent_id=parent_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            birth_date=birth_date,
        )

    def get_parent(self, parent_id: str) -> Parent:
        """Get parent by ID."""
        parent = self.parent_repo.get_by_id(parent_id)
        if not parent:
            raise NotFoundException("Parent not found")
        return parent

    def get_my_parent_profile(self, current_user: User) -> Parent:
        """Get current user's parent profile."""
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise NotFoundException("Parent profile not found")
        return parent

    def link_child(self, current_user: User, child_id: str, note: Optional[str] = None):
        """Link a child to the parent."""
        parent = self.get_my_parent_profile(current_user)
        child = self.child_repo.get_by_id(child_id)

        if not child:
            raise NotFoundException("Child not found")

        link_id = str(uuid.uuid4())
        return self.child_repo.link_parent_to_child(
            link_id=link_id,
            parent_id=parent.parent_id,
            child_id=child_id,
            note=note,
        )

    def get_my_children(self, current_user: User) -> List[Child]:
        """Get all children linked to the parent."""
        parent = self.get_my_parent_profile(current_user)
        return self._get_linked_children(parent.parent_id)

    def get_dashboard(self, current_user: User, *, today: Optional[date] = None) -> ParentDashboardResponse:
        """Return a parent dashboard covering all linked children."""
        parent = self.get_my_parent_profile(current_user)
        today_value = today or datetime.now().date()
        children = self._get_linked_children(parent.parent_id)
        child_ids = [child.child_id for child in children]
        group_ids = sorted({child.group_id for child in children if child.group_id})

        attendance_map = self._get_attendance_map(child_ids=child_ids, target_date=today_value)
        menu_map = self._get_group_menu_map(group_ids=group_ids, target_date=today_value)
        latest_payment_map = self._get_latest_payment_map(child_ids=child_ids)
        pedagogue_map = self._get_pedagogue_map(group_ids=group_ids)

        items = []
        for child in children:
            group = child.group or self.db.query(Group).filter(Group.group_id == child.group_id).first()
            if not group:
                raise NotFoundException("Group not found for child")

            attendance = attendance_map.get(child.child_id)
            items.append(
                ParentDashboardChildItem(
                    child_id=child.child_id,
                    full_name=child.full_name,
                    birth_date=child.birth_date,
                    gender=child.gender.value if getattr(child.gender, "value", None) else child.gender,
                    group=ParentGroupSummary(group_id=group.group_id, group_name=group.group_name),
                    pedagogue=pedagogue_map.get(group.group_id),
                    today_attendance_status=self._dashboard_attendance_status(attendance),
                    today_menu=self._serialize_menu(menu_map.get(group.group_id), group),
                    latest_payment=self._serialize_payment_summary(latest_payment_map.get(child.child_id)),
                )
            )

        return ParentDashboardResponse(
            children=items,
            unread_notifications_count=self.notification_service.count_unread_for_user(current_user),
        )

    def get_attendance(
        self,
        current_user: User,
        *,
        child_id: Optional[str] = None,
        exact_date: Optional[date] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[ParentAttendanceItemResponse]:
        """Return attendance history for the current parent's linked children."""
        parent = self.get_my_parent_profile(current_user)
        if child_id:
            selected_child_ids = [self._get_linked_child_or_raise(parent.parent_id, child_id).child_id]
        else:
            linked_children = self._get_linked_children(parent.parent_id)
            if not linked_children:
                return []
            selected_child_ids = [child.child_id for child in linked_children]

        start_date, end_date = self._resolve_attendance_range(
            exact_date=exact_date,
            date_from=date_from,
            date_to=date_to,
        )
        rows = (
            self.db.query(Attendance, Child.full_name.label("child_name"), Group.group_name.label("group_name"))
            .join(Child, Child.child_id == Attendance.child_id)
            .join(Group, Group.group_id == Attendance.group_id)
            .filter(
                Attendance.child_id.in_(selected_child_ids),
                Attendance.attend_date >= start_date,
                Attendance.attend_date <= end_date,
            )
            .order_by(Attendance.attend_date.desc(), Child.full_name.asc(), Attendance.child_id.asc())
            .all()
        )

        return [
            ParentAttendanceItemResponse(
                child_id=attendance.child_id,
                child_name=child_name,
                group_id=attendance.group_id,
                group_name=group_name,
                date=attendance.attend_date,
                status=AttendanceStatus(attendance.status),
            )
            for attendance, child_name, group_name in rows
        ]

    def get_menu(self, current_user: User, *, child_id: Optional[str] = None, target_date: Optional[date] = None) -> ParentMenuResponse:
        """Return the visible menu for a selected linked child."""
        child = self._resolve_selected_child(current_user, child_id=child_id)
        group = child.group or self.db.query(Group).filter(Group.group_id == child.group_id).first()
        if not group:
            raise NotFoundException("Group not found for child")

        menu = self.get_menu_model(current_user, child_id=child.child_id, target_date=target_date)
        response = self._serialize_menu(menu, group)
        if response is None:
            raise NotFoundException("Published menu not found")
        return response

    def get_menu_model(self, current_user: User, *, child_id: str, target_date: Optional[date] = None) -> Menu:
        """Return the published menu ORM record for one linked child and date."""
        parent = self.get_my_parent_profile(current_user)
        child = self._get_linked_child_or_raise(parent.parent_id, child_id)
        selected_date = target_date or datetime.now().date()
        menu = self.menu_repo.get_menu_for_group(child.group_id, selected_date, published_only=True)
        if not menu:
            raise NotFoundException("Published menu not found")
        return menu

    def list_notifications(self, current_user: User, *, skip: int = 0, limit: int = 20):
        """List notifications visible to the current parent user."""
        return self.notification_service.list_for_user(current_user, skip=skip, limit=limit)

    def mark_notification_read(self, current_user: User, notification_id: str):
        """Mark a notification as read for the current parent user."""
        return self.notification_service.mark_as_read(current_user, notification_id)

    def list_parents(self, skip: int = 0, limit: int = 20) -> Tuple[List[Parent], int]:
        """List all parents."""
        return self.parent_repo.list(skip=skip, limit=limit)

    def _get_linked_children(self, parent_id: str) -> List[Child]:
        """Load active linked children with their groups."""
        return (
            self.db.query(Child)
            .options(joinedload(Child.group))
            .join(ParentChildLink, ParentChildLink.child_id == Child.child_id)
            .filter(
                ParentChildLink.parent_id == parent_id,
                ParentChildLink.status == "active",
            )
            .order_by(Child.full_name.asc(), Child.child_id.asc())
            .all()
        )

    def _get_linked_child_or_raise(self, parent_id: str, child_id: str) -> Child:
        """Resolve one linked child and distinguish missing from forbidden."""
        child = (
            self.db.query(Child)
            .options(joinedload(Child.group))
            .join(ParentChildLink, ParentChildLink.child_id == Child.child_id)
            .filter(
                ParentChildLink.parent_id == parent_id,
                ParentChildLink.status == "active",
                Child.child_id == child_id,
            )
            .first()
        )
        if child:
            return child

        existing = self.child_repo.get_by_id(child_id)
        if existing:
            raise AuthorizationException("Child is not linked to this parent")
        raise NotFoundException("Child not found")

    def _resolve_selected_child(self, current_user: User, *, child_id: Optional[str]) -> Child:
        """Resolve which child a parent is targeting for child-scoped reads."""
        parent = self.get_my_parent_profile(current_user)
        children = self._get_linked_children(parent.parent_id)
        if not children:
            raise NotFoundException("No linked children found")
        if child_id:
            return self._get_linked_child_or_raise(parent.parent_id, child_id)
        if len(children) == 1:
            return children[0]
        raise ValidationException("child_id is required when parent has multiple linked children")

    def _resolve_attendance_range(
        self,
        *,
        exact_date: Optional[date],
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> tuple[date, date]:
        """Validate and normalize parent attendance filters."""
        if exact_date and (date_from or date_to):
            raise ValidationException("date cannot be combined with date_from or date_to")

        if exact_date:
            return exact_date, exact_date

        today = datetime.now().date()
        start_date = date_from
        end_date = date_to
        if start_date is None and end_date is None:
            end_date = today
            start_date = today - timedelta(days=29)
        elif start_date is not None and end_date is None:
            end_date = today
        elif start_date is None and end_date is not None:
            start_date = end_date

        if start_date > end_date:
            raise ValidationException("date_from cannot be after date_to")
        return start_date, end_date

    def _get_attendance_map(self, *, child_ids: list[str], target_date: date) -> dict[str, Attendance]:
        """Load today's attendance keyed by child."""
        if not child_ids:
            return {}
        records = (
            self.db.query(Attendance)
            .filter(Attendance.child_id.in_(child_ids), Attendance.attend_date == target_date)
            .all()
        )
        return {record.child_id: record for record in records}

    def _get_group_menu_map(self, *, group_ids: list[str], target_date: date) -> dict[str, Menu]:
        """Load the first published menu per group for one date."""
        menu_map: dict[str, Menu] = {}
        for group_id, menu in self.menu_repo.list_group_menus_by_date(
            group_ids=group_ids,
            menu_date=target_date,
            published_only=True,
        ):
            menu_map.setdefault(group_id, menu)
        return menu_map

    def _get_latest_payment_map(self, *, child_ids: list[str]) -> dict[str, Payment]:
        """Load the latest payment per linked child."""
        if not child_ids:
            return {}

        payments = (
            self.db.query(Payment)
            .filter(Payment.child_id.in_(child_ids))
            .order_by(Payment.child_id.asc(), Payment.due_date.desc(), Payment.created_at.desc())
            .all()
        )
        latest_by_child: dict[str, Payment] = {}
        for payment in payments:
            latest_by_child.setdefault(payment.child_id, payment)
        return latest_by_child

    def _get_pedagogue_map(self, *, group_ids: list[str]) -> dict[str, ParentPedagogueSummary]:
        """Resolve one pedagogue per group for dashboard use."""
        if not group_ids:
            return {}

        groups = (
            self.db.query(Group)
            .filter(Group.group_id.in_(group_ids))
            .order_by(Group.group_id.asc())
            .all()
        )
        result: dict[str, ParentPedagogueSummary] = {}
        for group in groups:
            pedagogue = None
            if group.teacher_id:
                pedagogue = (
                    self.db.query(Pedagogue)
                    .filter(
                        Pedagogue.teacher_id == group.teacher_id,
                        Pedagogue.kindergarten_id == group.kindergarten_id,
                    )
                    .first()
                )
            if pedagogue is None:
                pedagogue = (
                    self.db.query(Pedagogue)
                    .filter(
                        Pedagogue.group_id == group.group_id,
                        Pedagogue.kindergarten_id == group.kindergarten_id,
                    )
                    .order_by(Pedagogue.created_at.asc(), Pedagogue.teacher_id.asc())
                    .first()
                )
            if pedagogue is not None:
                result[group.group_id] = ParentPedagogueSummary(
                    pedagogue_id=pedagogue.teacher_id,
                    full_name=pedagogue.full_name,
                    role=pedagogue.role,
                )
        return result

    def _dashboard_attendance_status(self, attendance: Optional[Attendance]) -> ParentDashboardAttendanceStatus:
        """Return dashboard status with an explicit unmarked value."""
        if attendance is None:
            return ParentDashboardAttendanceStatus.UNMARKED
        return ParentDashboardAttendanceStatus(attendance.status)

    def _serialize_menu(self, menu: Optional[Menu], group: Group) -> Optional[ParentMenuResponse]:
        """Convert a menu ORM object into the parent-facing response shape."""
        if menu is None:
            return None
        return ParentMenuResponse(
            menu_id=menu.menu_id,
            group_id=group.group_id,
            group_name=group.group_name,
            menu_date=menu.menu_date,
            status=menu.status,
            published_at=menu.published_at,
            notes=menu.notes,
            items=[
                ParentMenuItemResponse(
                    meal=item.meal,
                    title=item.title,
                    description=item.description,
                    calories=item.calories,
                )
                for item in sorted(menu.items, key=lambda value: value.meal.value)
            ],
        )

    def _serialize_payment_summary(self, payment: Optional[Payment]) -> Optional[ParentLatestPaymentSummary]:
        """Convert a payment into a compact dashboard summary."""
        if payment is None:
            return None
        return ParentLatestPaymentSummary(
            payment_id=payment.payment_id,
            billing_period=payment.billing_period,
            amount=payment.amount,
            status=payment.effective_status,
            due_date=payment.due_date,
        )
