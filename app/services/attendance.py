"""Attendance service."""
from __future__ import annotations

import uuid
from collections import Counter
from datetime import UTC, datetime, date

from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.models.attendance import Attendance, AttendanceStatus
from app.models.child import Child
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.attendance import (
    AttendanceBulkSaveRequest,
    AttendanceHistoryItemResponse,
    AttendanceSummaryResponse,
    DailyAttendanceItemResponse,
)
from app.services.tenant_scope import TenantScopedService


class AttendanceService(TenantScopedService):
    """Tenant-safe attendance workflows."""

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

    def _list_group_children(self, kindergarten_id: str, group_id: str) -> list[Child]:
        return (
            self.db.query(Child)
            .filter(Child.kindergarten_id == kindergarten_id, Child.group_id == group_id)
            .order_by(Child.full_name.asc(), Child.child_id.asc())
            .all()
        )

    def bulk_save(self, current_user: User, payload: AttendanceBulkSaveRequest) -> list[Attendance]:
        """Create or update attendance records for one group and date."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        self.get_group_for_kindergarten(kindergarten_id, payload.group_id)

        target_child_ids: list[str] = []
        for record in payload.records:
            child = self._get_scoped_child(kindergarten_id, record.child_id)
            if child.group_id != payload.group_id:
                raise ValidationException("Child does not belong to the selected group")
            target_child_ids.append(child.child_id)

        existing_records = (
            self.db.query(Attendance)
            .filter(
                Attendance.kindergarten_id == kindergarten_id,
                Attendance.attend_date == payload.date,
                Attendance.child_id.in_(target_child_ids),
            )
            .all()
        )
        existing_by_child = {record.child_id: record for record in existing_records}
        timestamp = datetime.now(UTC)
        for item in payload.records:
            attendance = existing_by_child.get(item.child_id)
            if attendance:
                attendance.group_id = payload.group_id
                attendance.status = item.status.value
                attendance.marked_at = timestamp
                attendance.updated_at = timestamp
            else:
                attendance = Attendance(
                    attendance_id=str(uuid.uuid4()),
                    kindergarten_id=kindergarten_id,
                    child_id=item.child_id,
                    group_id=payload.group_id,
                    attend_date=payload.date,
                    status=item.status.value,
                    marked_at=timestamp,
                )
                self.db.add(attendance)

        self.db.commit()

        return (
            self.db.query(Attendance)
            .filter(
                Attendance.kindergarten_id == kindergarten_id,
                Attendance.attend_date == payload.date,
                Attendance.child_id.in_(target_child_ids),
            )
            .order_by(Attendance.child_id.asc())
            .all()
        )

    def get_daily(self, current_user: User, group_id: str, target_date: date) -> list[DailyAttendanceItemResponse]:
        """Return all children in a group with attendance status for one day."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        self.get_group_for_kindergarten(kindergarten_id, group_id)

        children = self._list_group_children(kindergarten_id, group_id)
        attendance_records = (
            self.db.query(Attendance)
            .filter(
                Attendance.kindergarten_id == kindergarten_id,
                Attendance.group_id == group_id,
                Attendance.attend_date == target_date,
            )
            .all()
        )
        attendance_by_child = {record.child_id: record for record in attendance_records}

        return [
            DailyAttendanceItemResponse(
                child_id=child.child_id,
                full_name=child.full_name,
                first_name=child.first_name,
                last_name=child.last_name,
                status=AttendanceStatus(attendance_by_child[child.child_id].status)
                if child.child_id in attendance_by_child
                else None,
                marked_at=attendance_by_child[child.child_id].marked_at
                if child.child_id in attendance_by_child
                else None,
            )
            for child in children
        ]

    def get_history(
        self,
        current_user: User,
        *,
        date_from: date,
        date_to: date,
        group_id: str | None = None,
    ) -> list[AttendanceHistoryItemResponse]:
        """Return tenant-scoped attendance history."""
        if date_from > date_to:
            raise ValidationException("date_from cannot be after date_to")

        kindergarten_id = self.get_current_kindergarten_id(current_user)
        query = (
            self.db.query(Attendance, Child.full_name.label("child_name"))
            .join(Child, Child.child_id == Attendance.child_id)
            .filter(
                Attendance.kindergarten_id == kindergarten_id,
                Attendance.attend_date >= date_from,
                Attendance.attend_date <= date_to,
            )
        )
        if group_id:
            self.get_group_for_kindergarten(kindergarten_id, group_id)
            query = query.filter(Attendance.group_id == group_id)

        rows = query.order_by(Attendance.attend_date.desc(), Child.full_name.asc()).all()
        return [
            AttendanceHistoryItemResponse.model_validate(
                {
                    "id": attendance.id,
                    "attendance_id": attendance.attendance_id,
                    "kindergarten_id": attendance.kindergarten_id,
                    "child_id": attendance.child_id,
                    "group_id": attendance.group_id,
                    "date": attendance.date,
                    "status": attendance.status,
                    "marked_at": attendance.marked_at,
                    "created_at": attendance.created_at,
                    "updated_at": attendance.updated_at,
                    "child_name": child_name,
                }
            )
            for attendance, child_name in rows
        ]

    def get_summary(
        self,
        current_user: User,
        *,
        group_id: str,
        target_date: date,
    ) -> AttendanceSummaryResponse:
        """Return daily attendance counts for one group."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        self.get_group_for_kindergarten(kindergarten_id, group_id)

        children = self._list_group_children(kindergarten_id, group_id)
        attendance_records = (
            self.db.query(Attendance)
            .filter(
                Attendance.kindergarten_id == kindergarten_id,
                Attendance.group_id == group_id,
                Attendance.attend_date == target_date,
            )
            .all()
        )
        counts = Counter(record.status for record in attendance_records)
        total_children = len(children)
        marked_count = len(attendance_records)

        return AttendanceSummaryResponse(
            group_id=group_id,
            date=target_date,
            total_children=total_children,
            present_count=counts.get(AttendanceStatus.PRESENT.value, 0),
            late_count=counts.get(AttendanceStatus.LATE.value, 0),
            absent_count=counts.get(AttendanceStatus.ABSENT.value, 0),
            unmarked_count=total_children - marked_count,
        )

    def create_from_legacy_enrollment(
        self,
        current_user: User,
        *,
        enrol_id: str,
        attend_date: date,
        status: AttendanceStatus,
        notes: str | None = None,
    ) -> Attendance:
        """Support the old single attendance endpoint without duplicating logic."""
        kindergarten_id = self.get_current_kindergarten_id(current_user)
        enrollment = self.db.query(Enrollment).filter(Enrollment.enrol_id == enrol_id).first()
        if not enrollment:
            raise ValidationException("Enrollment not found")

        child = self._get_scoped_child(kindergarten_id, enrollment.child_id)
        group = self.get_group_for_kindergarten(kindergarten_id, enrollment.group_id)
        if child.group_id != group.group_id:
            raise ValidationException("Enrollment child does not belong to the selected group")

        payload = AttendanceBulkSaveRequest(
            group_id=group.group_id,
            date=attend_date,
            records=[{"child_id": child.child_id, "status": status}],
        )
        record = self.bulk_save(current_user, payload)[0]
        if notes != record.notes or enrol_id != record.enrol_id:
            record.notes = notes
            record.enrol_id = enrol_id
            self.db.commit()
            self.db.refresh(record)
        return record
