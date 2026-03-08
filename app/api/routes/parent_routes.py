"""Parent routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.core.dependencies import get_db, get_current_parent_user
from app.schemas.child import ChildResponse, ParentChildLinkRequest, ParentChildLinkResponse
from app.schemas.menu import MenuResponse
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.schemas.base import PaginatedResponse
from app.services.parent import ParentService
from app.services.menu import MenuService
from app.services.payment import PaymentService
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.models.payment import PaymentProvider

router = APIRouter()


@router.post("/link-child", response_model=ParentChildLinkResponse, status_code=status.HTTP_201_CREATED)
def link_child(
    request: ParentChildLinkRequest,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Link child to parent."""
    try:
        service = ParentService(db)
        link = service.link_child(current_user, request.child_id, request.note)
        return link
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/children", response_model=list[ChildResponse])
def get_my_children(
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get my linked children."""
    try:
        service = ParentService(db)
        children = service.get_my_children(current_user)
        return children
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/menus/today", response_model=Optional[MenuResponse])
def get_todays_menu(
    child_id: str,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get today's menu for child's group."""
    try:
        from app.repositories.child import ChildRepository
        from app.repositories.enrollment import EnrollmentRepository
        
        child_repo = ChildRepository(db)
        enrol_repo = EnrollmentRepository(db)
        
        enrollments = enrol_repo.get_by_child(child_id, status="active")
        if not enrollments:
            raise ValueError("No active enrollment found")
        
        service = MenuService(db)
        menu = service.get_menu_for_group_today(current_user, enrollments[0].group_id)
        return menu
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    enrol_id: str,
    amount: float,
    provider: PaymentProvider,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Create payment."""
    try:
        from decimal import Decimal
        service = PaymentService(db)
        payment = service.create_payment(
            current_user, enrol_id, Decimal(str(amount)),
            date.today(), provider
        )
        return payment
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/payments", response_model=PaginatedResponse[PaymentResponse])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db)
):
    """Get payment history."""
    try:
        service = PaymentService(db)
        items, total = service.list_payments_for_parent(current_user, skip, limit)
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
