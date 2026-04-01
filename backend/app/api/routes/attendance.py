"""Attendance routes."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.attendance import (
    AttendanceBulkSaveRequest,
    AttendanceBulkSaveResponse,
    AttendanceHistoryItemResponse,
    AttendanceSummaryResponse,
    DailyAttendanceResponse,
)
from app.services.attendance import AttendanceService

router = APIRouter()


@router.post("/bulk", response_model=AttendanceBulkSaveResponse, status_code=status.HTTP_200_OK)
def bulk_save_attendance(
    request: AttendanceBulkSaveRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create or update daily attendance records for one group."""
    try:
        records = AttendanceService(db).bulk_save(current_user, request)
        return {"group_id": request.group_id, "date": request.date, "records": records}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/daily", response_model=DailyAttendanceResponse)
def get_daily_attendance(
    group_id: str = Query(...),
    date: date = Query(...),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List all children in a group and any existing attendance for the selected day."""
    try:
        items = AttendanceService(db).get_daily(current_user, group_id, date)
        return {"group_id": group_id, "date": date, "items": items}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/history", response_model=list[AttendanceHistoryItemResponse])
def get_attendance_history(
    date_from: date = Query(...),
    date_to: date = Query(...),
    group_id: str | None = Query(None),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List attendance history for the current tenant."""
    try:
        return AttendanceService(db).get_history(
            current_user,
            date_from=date_from,
            date_to=date_to,
            group_id=group_id,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/summary", response_model=AttendanceSummaryResponse)
def get_attendance_summary(
    group_id: str = Query(...),
    date: date = Query(...),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Return counts for one group and day."""
    try:
        return AttendanceService(db).get_summary(current_user, group_id=group_id, target_date=date)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
