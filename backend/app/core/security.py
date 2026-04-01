"""Security utilities for authentication and password handling."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_revoked_token_ids: set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


def _create_token(data: dict, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    to_encode = data.copy()
    to_encode.update(
        {
            "exp": now + expires_delta,
            "iat": now,
            "type": token_type,
            "jti": str(uuid4()),
        }
    )
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    return _create_token(
        data=data,
        token_type="access",
        expires_delta=expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    return _create_token(
        data=data,
        token_type="refresh",
        expires_delta=expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    token_id = payload.get("jti")
    if token_id and token_id in _revoked_token_ids:
        return None
    return payload


def revoke_token(token: str) -> bool:
    """Mark a token as revoked for the current process."""
    payload = decode_token(token)
    if not payload:
        return False

    token_id = payload.get("jti")
    if not token_id:
        return False

    _revoked_token_ids.add(token_id)
    return True
