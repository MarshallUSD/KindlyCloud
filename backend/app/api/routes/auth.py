"""Public business authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.dependencies import build_auth_context, get_current_user, get_db
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    LogoutRequest,
    ParentLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.auth import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a kindergarten-side account."""
    try:
        service = AuthService(db)
        user = service.register_kindergarten_user(
            email=request.email,
            password=request.password,
            phone=request.phone,
            full_name=request.full_name,
        )
        return service._build_token_response(user)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Login a kindergarten-side user with email and password."""
    try:
        service = AuthService(db)
        _, tokens = service.authenticate_kindergarten(request.email, request.password)
        return tokens
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/parent-login", response_model=TokenResponse)
def parent_login(request: ParentLoginRequest, db: Session = Depends(get_db)):
    """Login a parent with phone number and password."""
    try:
        service = AuthService(db)
        _, tokens = service.authenticate_parent(request.phone_number, request.password)
        return tokens
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh an access token."""
    try:
        return AuthService(db).refresh_tokens(request.refresh_token)
    except ApplicationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Logout the current user."""
    AuthService(db).logout(credentials.credentials, request.refresh_token)
    return {"success": True}


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the current authenticated business user."""
    payload = build_auth_context(db, current_user)
    return CurrentUserResponse(
        user_id=payload["sub"],
        role=str(payload["role"]),
        kindergarten_id=payload["kindergarten_id"],
        parent_id=payload["parent_id"],
        email=payload["email"],
        phone=payload["phone"],
    )
