"""Internal platform admin routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin, get_db
from app.core.exceptions import ApplicationException
from app.models.admin import Admin
from app.models.feedback import FeedbackStatus
from app.repositories.kindergarten import KindergartenRepository
from app.schemas.auth import AdminLoginRequest, TokenResponse
from app.schemas.base import PaginatedResponse
from app.schemas.feedback import FeedbackResponse, FeedbackUpdateRequest
from app.schemas.post import PostCreateRequest, PostResponse
from app.services.auth import AuthService
from app.services.feedback import FeedbackService
from app.services.post import PostService

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    """Internal platform admin login."""
    try:
        _, tokens = AuthService(db).authenticate_admin(request.email, request.password)
        return tokens
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    request: PostCreateRequest,
    current_user: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create an admin post."""
    try:
        return PostService(db).create_post(current_user, request.title, request.body, request.target_kindergarten_id)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/feedback", response_model=PaginatedResponse[FeedbackResponse])
def list_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[FeedbackStatus] = Query(None),
    current_user: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all feedback for platform admins."""
    try:
        service = FeedbackService(db)
        if status_filter:
            items, total = service.list_feedback_by_status(status_filter, skip, limit)
        else:
            items, total = service.list_all_feedback(skip, limit)
        return {"items": items, "total": total, "skip": skip, "limit": limit, "pages": (total + limit - 1) // limit}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback_status(
    feedback_id: str,
    request: FeedbackUpdateRequest,
    current_user: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update feedback status."""
    try:
        return FeedbackService(db).update_feedback_status(current_user, feedback_id, request.status)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/verify-kindergarten/{user_id}", status_code=status.HTTP_200_OK)
def verify_kindergarten(
    user_id: str,
    current_user: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Verify a kindergarten user so they can access the platform."""
    try:
        del current_user
        service = AuthService(db)
        target_user = service.get_user(user_id)
        if not target_user:
            raise ApplicationException("User not found", status_code=404)

        kindergarten = KindergartenRepository(db).get_by_user_id(target_user.user_id)
        if not kindergarten:
            raise ApplicationException("Kindergarten not found for this user", status_code=404)

        kindergarten.is_verified = True
        db.commit()
        return {"success": True, "message": "Kindergarten verified"}
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
