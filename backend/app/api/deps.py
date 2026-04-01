"""FastAPI dependencies for authentication and database access."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.core.security import decode_token
from app.models.user import User, UserRole, UserStatus
from app.repositories.user import UserRepository

security = HTTPBearer()


def get_db() -> Session:
    """Dependency to get database session."""
    for db in get_db_session():
        yield db


def get_current_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get the current authenticated user."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    
    return user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_current_kindergarten_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure current user is a kindergarten."""
    if current_user.role != UserRole.KINDERGARTEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kindergarten role required"
        )
    return current_user


def get_current_parent_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure current user is a parent."""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent role required"
        )
    return current_user
