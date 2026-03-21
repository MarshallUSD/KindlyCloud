"""Parent routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_parent_user, get_db
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.child import ChildResponse
from app.schemas.menu import MenuResponse
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.services.menu import MenuService
from app.services.parent import ParentService
from app.services.payment import PaymentService

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


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Create payment."""
    try:
        return PaymentService(db).create_payment(
            current_user,
            request.enrol_id,
            request.amount,
            request.payment_date,
            request.provider,
            request.transaction_id,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/payments", response_model=PaginatedResponse[PaymentResponse])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get payment history."""
    try:
        items, total = PaymentService(db).list_payments_for_parent(current_user, skip, limit)
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
