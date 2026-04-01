"""Staff routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_kindergarten_user, get_db
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.staff import StaffCreate, StaffResponse, StaffUpdate
from app.services.staff_service import StaffService

router = APIRouter()


@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    request: StaffCreate,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a staff member inside the current tenant."""
    try:
        return StaffService(db).create_staff(current_user, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/", response_model=PaginatedResponse[StaffResponse])
def list_staff(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=200),
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List staff for the current tenant."""
    try:
        items, total = StaffService(db).get_staff(
            current_user,
            skip=skip,
            limit=limit,
            search=search,
            group_id=group_id,
        )
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff_member(
    staff_id: str,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one staff member from the current tenant."""
    try:
        return StaffService(db).get_staff_member(current_user, staff_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.put("/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: str,
    request: StaffUpdate,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Update one staff member from the current tenant."""
    try:
        return StaffService(db).update_staff(current_user, staff_id, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: str,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Delete one staff member from the current tenant."""
    try:
        StaffService(db).delete_staff(current_user, staff_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
