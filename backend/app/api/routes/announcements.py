"""Announcement routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.notification import AnnouncementCreateRequest, AnnouncementResponse
from app.services.announcement_service import AnnouncementService

router = APIRouter()


@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    request: AnnouncementCreateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a new tenant-scoped announcement."""
    try:
        return AnnouncementService(db).create_announcement(
            current_user,
            title=request.title,
            message=request.message,
            target_type=request.target_type,
            target_group_id=request.target_group_id,
            target_child_id=request.target_child_id,
            scheduled_at=request.scheduled_at,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/", response_model=PaginatedResponse[AnnouncementResponse])
def list_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List announcements for the current tenant."""
    try:
        items, total = AnnouncementService(db).list_announcements(current_user, skip=skip, limit=limit)
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one tenant announcement."""
    try:
        return AnnouncementService(db).get_announcement(current_user, announcement_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Delete one tenant announcement record."""
    try:
        AnnouncementService(db).delete_announcement(current_user, announcement_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
