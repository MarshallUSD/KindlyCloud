"""FastAPI dependencies for authentication and database access."""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db_session
from app.core.security import decode_token
from app.models.admin import Admin
from app.models.user import User, UserRole
from app.repositories.admin import AdminRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.parent import ParentRepository
from app.repositories.user import UserRepository

security = HTTPBearer()
KINDERGARTEN_VERIFICATION_PENDING_DETAIL = "Kindergarten account is pending verification"


def get_db() -> Session:
    """Dependency to get a DB session."""
    yield from get_db_session()


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
    payload = decode_token(credentials.credentials)
    if not payload:
        raise _unauthorized()
    if payload.get("type") != "access":
        raise _unauthorized("Access token required")

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise _unauthorized("Invalid token payload")

    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise _unauthorized("User not found")
    if getattr(user, "status", "active") != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Admin | User:
    """Dependency to ensure current token belongs to an admin."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise _unauthorized()
    if payload.get("type") != "access":
        raise _unauthorized("Access token required")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

    admin_id = payload.get("sub")
    if not admin_id:
        raise _unauthorized("Invalid token payload")

    repo = AdminRepository(db)
    admin = repo.get_by_id(int(admin_id))
    if admin:
        if admin.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin is inactive")
        return admin

    user = UserRepository(db).get_by_id(admin_id)
    if not user:
        raise _unauthorized("Admin not found")
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    if getattr(user, "status", "active") != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin is inactive")
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure current user is an admin user record."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


async def get_current_kindergarten_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure current user is a kindergarten user."""
    if current_user.role != UserRole.KINDERGARTEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kindergarten role required")
    return current_user


async def get_verified_kindergarten_user(
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to ensure current kindergarten user belongs to a verified kindergarten."""
    kindergarten = KindergartenRepository(db).get_by_user_id(current_user.user_id)
    if not kindergarten or not kindergarten.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=KINDERGARTEN_VERIFICATION_PENDING_DETAIL,
        )
    return current_user


async def get_current_parent_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure current user is a parent user."""
    if current_user.role != UserRole.PARENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parent role required")
    return current_user


def build_auth_context(db: Session, user: User) -> dict[str, Optional[str]]:
    """Build the auth payload returned to clients and embedded into JWTs."""
    kindergarten = KindergartenRepository(db).get_by_user_id(user.user_id)
    parent = ParentRepository(db).get_by_user_id(user.user_id)
    return {
        "sub": str(user.user_id),
        "role": user.role.value if isinstance(user.role, UserRole) else str(user.role),
        "kindergarten_id": kindergarten.kindergarten_id if kindergarten else None,
        "parent_id": parent.parent_id if parent else None,
        "email": user.email,
        "phone": user.phone,
    }
