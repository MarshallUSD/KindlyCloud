"""Group routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.group import GroupCreateRequest, GroupResponse, GroupUpdateRequest
from app.services.group import GroupService

router = APIRouter()


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    request: GroupCreateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a group inside the current tenant."""
    try:
        return GroupService(db).create_group(current_user, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/", response_model=PaginatedResponse[GroupResponse])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List groups for the current tenant."""
    try:
        items, total = GroupService(db).list_groups(current_user, skip=skip, limit=limit)
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one group from the current tenant."""
    try:
        return GroupService(db).get_group(current_user, group_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: str,
    request: GroupUpdateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Update one group from the current tenant."""
    try:
        return GroupService(db).update_group(current_user, group_id, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Delete one group from the current tenant."""
    try:
        GroupService(db).delete_group(current_user, group_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
