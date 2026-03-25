"""Teacher routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.teacher import TeacherCreateRequest, TeacherResponse, TeacherUpdateRequest
from app.services.teacher import TeacherService

router = APIRouter()


@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(
    request: TeacherCreateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a teacher inside the current tenant."""
    try:
        return TeacherService(db).create_teacher(current_user, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/", response_model=PaginatedResponse[TeacherResponse])
def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List teachers for the current tenant."""
    try:
        items, total = TeacherService(db).list_teachers(current_user, skip=skip, limit=limit, group_id=group_id)
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{teacher_id}", response_model=TeacherResponse)
def get_teacher(
    teacher_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one teacher from the current tenant."""
    try:
        return TeacherService(db).get_teacher(current_user, teacher_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.put("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: str,
    request: TeacherUpdateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Update one teacher from the current tenant."""
    try:
        return TeacherService(db).update_teacher(current_user, teacher_id, request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    teacher_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Delete one teacher from the current tenant."""
    try:
        TeacherService(db).delete_teacher(current_user, teacher_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
