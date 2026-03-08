"""Authentication schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.user import UserRole, UserStatus


class UserRegisterRequest(BaseModel):
    """User registration request."""
    role: UserRole = Field(..., description="User role: admin, kindergarten, or parent")
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLoginRequest(BaseModel):
    """User login request."""
    phone_or_email: str = Field(..., description="Phone number or email address")
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response schema."""
    user_id: str
    role: UserRole
    email: str
    phone: Optional[str]
    status: UserStatus
    created_at: str
    
    class Config:
        from_attributes = True
