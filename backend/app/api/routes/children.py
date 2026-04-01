"""Child routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_kindergarten_user, get_db
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.services.child_service import ChildService

router = APIRouter()


@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    request: ChildCreate,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a child inside the current tenant."""
    try:
        return ChildService(db).create_child(current_user, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/", response_model=PaginatedResponse[ChildResponse])
def list_children(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=200),
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List children for the current tenant."""
    try:
        items, total = ChildService(db).get_children(
            current_user,
            skip=skip,
            limit=limit,
            group_id=group_id,
            search=search,
        )
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{child_id}", response_model=ChildResponse)
def get_child(
    child_id: str,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one child from the current tenant."""
    try:
        return ChildService(db).get_child(current_user, child_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.put("/{child_id}", response_model=ChildResponse)
def update_child(
    child_id: str,
    request: ChildUpdate,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Update one child from the current tenant."""
    try:
        return ChildService(db).update_child(current_user, child_id, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_child(
    child_id: str,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Delete one child from the current tenant."""
    try:
        ChildService(db).delete_child(current_user, child_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
