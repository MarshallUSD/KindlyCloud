"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_user, get_current_admin
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, ParentOTPRequest, ParentOTPVerifyRequest
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
        access_token = create_access_token(data={"sub": str(user.user_id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login with phone or email."""
    try:
        service = AuthService(db)
        user, access_token = service.login(request.phone_or_email, request.password)
        
        # Additional check for Kindergarten
        from app.models.user import UserRole
        if user.role == UserRole.KINDERGARTEN and not user.is_verified:
            # If Kindergarten, we could throw AuthenticationException("Not Verified")
            # But the user might want them to be able to login to see their "pending" status
            # We'll let them login but the profile routes might be blocked, or we just let them login.
            pass
            
        return {"access_token": access_token, "token_type": "bearer"}
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/parent/send-otp", status_code=status.HTTP_200_OK)
def send_parent_otp(request: ParentOTPRequest, db: Session = Depends(get_db)):
    """Send OTP for parent login/registration."""
    try:
        service = AuthService(db)
        service.send_parent_otp(request.phone)
        return {"success": True, "message": "OTP sent successfully"}
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/parent/verify-otp", response_model=TokenResponse)
def verify_parent_otp(request: ParentOTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and set password, returns token."""
    try:
        if request.password != request.confirm_password:
            raise ApplicationException("Passwords do not match", status_code=400)
            
        service = AuthService(db)
        user, access_token = service.verify_parent_otp(request.phone, request.otp_code, request.password)
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

@router.post("/admin/verify-kindergarten/{user_id}", status_code=status.HTTP_200_OK)
def verify_kindergarten(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Verify a kindergarten user so they can access the platform."""
    try:
        service = AuthService(db)
        target_user = service.get_user(user_id)
        if not target_user:
            raise ApplicationException("User not found", status_code=404)
            
        target_user.is_verified = True
        db.commit()
        
        return {"success": True, "message": "Kindergarten effectively verified"}
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
