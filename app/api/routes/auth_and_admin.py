"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_user, get_current_admin
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.schemas.base import PaginatedResponse
from app.services.auth import AuthService
from app.services.post import PostService
from app.services.feedback import FeedbackService
from app.schemas.post import PostCreateRequest, PostResponse
from app.schemas.feedback import FeedbackCreateRequest, FeedbackUpdateRequest, FeedbackResponse
from app.models.feedback import FeedbackStatus
from app.core.exceptions import ApplicationException
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        service = AuthService(db)
        user = service.register_user(request.role, request.phone, request.email, request.password)
        from app.core.security import create_access_token
        access_token = create_access_token(data={"sub": user.user_id})
        return {"access_token": access_token, "token_type": "bearer"}
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login with phone or email."""
    try:
        service = AuthService(db)
        user, access_token = service.login(request.phone_or_email, request.password)
        return {"access_token": access_token, "token_type": "bearer"}
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/admin/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    request: PostCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create an admin post."""
    try:
        service = PostService(db)
        post = service.create_post(current_user, request.title, request.body, request.target_kindergarten_id)
        return post
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/admin/feedback", response_model=PaginatedResponse[FeedbackResponse])
def list_feedback(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[FeedbackStatus] = Query(None),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all feedback (admin)."""
    try:
        service = FeedbackService(db)
        if status_filter:
            items, total = service.list_feedback_by_status(status_filter, skip, limit)
        else:
            items, total = service.list_all_feedback(skip, limit)
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.patch("/admin/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback_status(
    feedback_id: str,
    request: FeedbackUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update feedback status."""
    try:
        service = FeedbackService(db)
        feedback = service.update_feedback_status(current_user, feedback_id, request.status)
        return feedback
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
