"""Payment routes."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_parent_user, get_db, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.payment import PaymentStatus
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.payment import (
    ParentPaymentResponse,
    PaymentCreateRequest,
    PaymentMarkPaidRequest,
    PaymentReportPeriod,
    PaymentResponse,
    PaymentUpdateRequest,
)
from app.services.payment import PaymentService
from app.services.payment_report import PaymentReportService

router = APIRouter()
parent_router = APIRouter()
report_router = APIRouter()


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a payment record for the current tenant."""
    try:
        return PaymentService(db).create_payment(
            current_user,
            child_id=request.child_id,
            amount=request.amount,
            due_date=request.due_date,
            billing_period=request.billing_period,
            status=request.status,
            notes=request.notes,
            paid_at=request.paid_at,
            payment_method=request.payment_method,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/", response_model=PaginatedResponse[PaymentResponse])
def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    child_id: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    status_filter: Optional[PaymentStatus] = Query(None, alias="status"),
    billing_period: Optional[str] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List tenant payments with filters."""
    try:
        items, total = PaymentService(db).list_payments_for_kindergarten(
            current_user,
            skip=skip,
            limit=limit,
            child_id=child_id,
            group_id=group_id,
            status=status_filter,
            billing_period=billing_period,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
        )
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one tenant payment record."""
    try:
        return PaymentService(db).get_payment_for_kindergarten(current_user, payment_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: str,
    request: PaymentUpdateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Update editable payment fields."""
    try:
        return PaymentService(db).update_payment(
            current_user,
            payment_id,
            amount=request.amount,
            due_date=request.due_date,
            notes=request.notes,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/{payment_id}/mark-paid", response_model=PaymentResponse)
def mark_payment_paid(
    payment_id: str,
    request: PaymentMarkPaidRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Mark a payment record as paid."""
    try:
        return PaymentService(db).mark_paid(
            current_user,
            payment_id,
            paid_at=request.paid_at,
            payment_method=request.payment_method,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@parent_router.get("/payments", response_model=PaginatedResponse[ParentPaymentResponse])
def list_parent_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """List payment records for the current parent."""
    try:
        items, total = PaymentService(db).list_payments_for_parent(current_user, skip=skip, limit=limit)
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@parent_router.get("/payments/{payment_id}", response_model=ParentPaymentResponse)
def get_parent_payment(
    payment_id: str,
    current_user: User = Depends(get_current_parent_user),
    db: Session = Depends(get_db),
):
    """Get one payment visible to the current parent."""
    try:
        return PaymentService(db).get_payment_for_parent(current_user, payment_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@report_router.get("/payments/export")
def export_payment_report(
    period: PaymentReportPeriod = Query(...),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    group_id: Optional[str] = Query(None),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Export tenant-scoped payment report as a PDF."""
    try:
        pdf_bytes, filename = PaymentReportService(db).export_pdf(
            current_user,
            period=period,
            from_date=from_date,
            to_date=to_date,
            group_id=group_id,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
