"""Authentication schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class UserRegisterRequest(BaseModel):
    """Public kindergarten registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)


class UserLoginRequest(BaseModel):
    """Public kindergarten login request."""

    email: EmailStr
    password: str


class ParentLoginRequest(BaseModel):
    """Parent login request."""

    phone_number: str = Field(..., min_length=7, max_length=20)
    password: str


class AdminLoginRequest(BaseModel):
    """Internal platform admin login request."""

    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request."""

    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    """Authenticated subject payload."""

    user_id: str
    role: str
    kindergarten_id: Optional[str] = None
    parent_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    token_type: str = "access"


class UserResponse(BaseModel):
    """User response schema."""

    user_id: str
    role: UserRole
    email: Optional[str]
    phone: Optional[str]
    status: UserStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
