"""Parent routes."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_parent_user, get_db
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.child import ChildResponse
from app.schemas.menu import MenuResponse
from app.models.notification import NotificationEventType, NotificationType
from app.schemas.notification import NotificationResponse
from app.schemas.notification import (
    ParentNotificationSettingsResponse,
    ParentNotificationSettingsUpdateRequest,
)
from app.schemas.parent import (
    ParentAttendanceItemResponse,
    ParentDashboardResponse,
    ParentMenuResponse,
)
from app.services.parent import ParentService
from app.services.notification import NotificationService

router = APIRouter()


@router.get("/children", response_model=list[ChildResponse])
def get_my_children(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get my linked children."""
    try:
        return ParentService(db).get_my_children(current_user)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/dashboard", response_model=ParentDashboardResponse)
def get_parent_dashboard(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Return the current parent's dashboard."""
    try:
        return ParentService(db).get_dashboard(current_user)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/attendance", response_model=list[ParentAttendanceItemResponse])
def get_parent_attendance(
    child_id: Optional[str] = Query(None),
    date_filter: Optional[date] = Query(None, alias="date"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get attendance history for linked children."""
    try:
        return ParentService(db).get_attendance(
            current_user,
            child_id=child_id,
            exact_date=date_filter,
            date_from=date_from,
            date_to=date_to,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/menu", response_model=ParentMenuResponse)
def get_parent_menu(
    child_id: Optional[str] = Query(None),
    date_filter: Optional[date] = Query(None, alias="date"),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get the published menu for a linked child's group."""
    try:
        return ParentService(db).get_menu(current_user, child_id=child_id, target_date=date_filter)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/menus/today", response_model=Optional[MenuResponse])
def get_todays_menu(
    child_id: str,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Backward-compatible today's menu route for one linked child."""
    try:
        return ParentService(db).get_menu_model(current_user, child_id=child_id, target_date=date.today())
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/notifications", response_model=PaginatedResponse[NotificationResponse])
def list_parent_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[NotificationType] = Query(None),
    event_type: Optional[NotificationEventType] = Query(None),
    is_read: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """List notifications for the current parent."""
    try:
        items, total = ParentService(db).list_notifications(
            current_user,
            skip=skip,
            limit=limit,
            type_=type,
            event_type=event_type,
            is_read=is_read,
        )
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_parent_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Mark one notification as read for the current parent."""
    try:
        return ParentService(db).mark_notification_read(current_user, notification_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/notification-settings", response_model=ParentNotificationSettingsResponse)
def get_parent_notification_settings(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get notification preferences for the current parent."""
    try:
        return NotificationService(db).get_settings(current_user)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/notification-settings", response_model=ParentNotificationSettingsResponse)
def update_parent_notification_settings(
    request: ParentNotificationSettingsUpdateRequest,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences for the current parent."""
    try:
        return NotificationService(db).update_settings(
            current_user,
            attendance_enabled=request.attendance_enabled,
            payments_enabled=request.payments_enabled,
            announcements_enabled=request.announcements_enabled,
            telegram_enabled=request.telegram_enabled,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
