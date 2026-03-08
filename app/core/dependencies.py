"""FastAPI dependencies for authentication and database access."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

security = HTTPBearer()


def get_db() -> Session:
    """
    Dependency to get a DB session (sync SQLAlchemy).
    get_db_session() generator bo‘lsa, uni yield qilib beramiz.
    """
    db = next(get_db_session())
    try:
        yield db
    finally:
        db.close()


def _unauthorized(detail: str = "Invalid or expired token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise _unauthorized()

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token payload")

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    

    if not user:
        raise _unauthorized("User not found")

    # Agar modelda status bo‘lmasa, bu qator xato bermasin:
    if getattr(user, "status", "active") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_current_kindergarten_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure current user is a kindergarten user."""
    if current_user.role != UserRole.KINDERGARTEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kindergarten role required",
        )
    return current_user


async def get_current_parent_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to ensure current user is a parent user."""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent role required",
        )
    return current_user 