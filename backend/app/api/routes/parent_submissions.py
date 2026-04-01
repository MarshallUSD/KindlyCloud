"""Parent submission routes."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.parent_submission import ParentSubmissionStatus, ParentSubmissionType
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.parent_submission import (
    ParentSubmissionCreateInternal,
    ParentSubmissionDetail,
    ParentSubmissionFilterParams,
    ParentSubmissionListItem,
    ParentSubmissionReviewRequest,
)
from app.services.parent_submission import ParentSubmissionService

router = APIRouter()
integration_router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ParentSubmissionListItem])
def list_parent_submissions(
    status_filter: Optional[ParentSubmissionStatus] = Query(None, alias="status"),
    submission_type: Optional[ParentSubmissionType] = Query(None),
    parent_id: Optional[str] = Query(None),
    child_id: Optional[str] = Query(None),
    payment_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """List parent submissions for the current kindergarten tenant."""
    try:
        filters = ParentSubmissionFilterParams(
            status=status_filter,
            submission_type=submission_type,
            parent_id=parent_id,
            child_id=child_id,
            payment_id=payment_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size,
        )
        items, total = ParentSubmissionService(db).list_for_kindergarten(current_user, filters)
        skip = (page - 1) * size
        return {"items": items, "total": total, "skip": skip, "limit": size, "pages": (total + size - 1) // size}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/{submission_id}", response_model=ParentSubmissionDetail)
def get_parent_submission(
    submission_id: str,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Get one parent submission for the current kindergarten tenant."""
    try:
        return ParentSubmissionService(db).get_for_kindergarten(current_user, submission_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/{submission_id}/review", response_model=ParentSubmissionDetail)
def review_parent_submission(
    submission_id: str,
    request: ParentSubmissionReviewRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Review, approve, or reject a submission."""
    try:
        return ParentSubmissionService(db).review_submission(
            current_user,
            submission_id,
            action=request.action,
            admin_note=request.admin_note,
        )
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@integration_router.post(
    "/telegram/parent-submissions",
    response_model=ParentSubmissionDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_parent_submission_from_telegram(
    request: ParentSubmissionCreateInternal,
    x_integration_secret: Optional[str] = Header(None, alias="X-Integration-Secret"),
    db: Session = Depends(get_db),
):
    """Protected ingestion endpoint for the Telegram bot integration."""
    service = ParentSubmissionService(db)
    try:
        service.authenticate_integration_request(x_integration_secret)
        return service.ingest_submission(request)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
