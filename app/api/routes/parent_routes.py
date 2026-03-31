"""Parent routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_parent_user, get_db
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.child import ChildResponse
from app.schemas.menu import MenuResponse
from app.services.menu import MenuService
from app.services.parent import ParentService

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


@router.get("/menus/today", response_model=Optional[MenuResponse])
def get_todays_menu(
    child_id: str,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get today's menu for one of the parent's linked children."""
    try:
        from app.repositories.enrollment import EnrollmentRepository

        children = ParentService(db).get_my_children(current_user)
        if child_id not in {child.child_id for child in children}:
            raise ApplicationException("Child is not linked to this parent", status_code=404)

        enrollments = EnrollmentRepository(db).get_by_child(child_id, status="active")
        if not enrollments:
            raise ApplicationException("No active enrollment found", status_code=404)

        return MenuService(db).get_menu_for_group_today(current_user, enrollments[0].group_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
