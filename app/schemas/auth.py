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


class ParentOTPRequest(BaseModel):
    """Request OTP for parent login/registration."""
    phone: str = Field(..., description="Phone number")


class ParentOTPVerifyRequest(BaseModel):
    """Verify OTP and set password."""
    phone: str = Field(..., description="Phone number")
    otp_code: str = Field(..., description="OTP Code")
    password: str = Field(..., min_length=8, description="Password to set")
    confirm_password: str = Field(..., description="Confirm password")


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
