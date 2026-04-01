"""Authentication service."""
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.dependencies import build_auth_context
from app.core.exceptions import AuthenticationException, ConflictException, NotFoundException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    revoke_token,
    verify_password,
)
from app.core.time import utcnow
from app.models.admin import Admin
from app.models.kindergarten import KindergartenUser
from app.models.parent import Parent, ParentUser
from app.models.user import User, UserRole, UserStatus
from app.repositories.admin import AdminRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.parent import ParentRepository
from app.repositories.user import UserRepository


class AuthService:
    """Service for authentication and user management."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.admin_repo = AdminRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.parent_repo = ParentRepository(db)

    def _build_token_response(self, user: User) -> dict[str, str]:
        claims = build_auth_context(self.db, user)
        return {
            "access_token": create_access_token(claims),
            "refresh_token": create_refresh_token(claims),
            "token_type": "bearer",
        }

    def register_kindergarten_user(
        self,
        email: str,
        password: str,
        phone: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Register a public kindergarten-side user."""
        if self.user_repo.user_exists(email=email, phone=phone):
            raise ConflictException("User with this email or phone already exists")

        user = self.user_repo.create_user(
            role=UserRole.KINDERGARTEN,
            phone=phone,
            email=email,
            password_hash=get_password_hash(password),
            status=UserStatus.ACTIVE,
        )
        if full_name:
            user.full_name = full_name
            self.db.commit()
            self.db.refresh(user)
        return user

    def authenticate_kindergarten(self, email: str, password: str) -> tuple[User, dict[str, str]]:
        """Authenticate a kindergarten-side user."""
        user = self.user_repo.get_by_email(email)
        if not user or user.role != UserRole.KINDERGARTEN:
            raise AuthenticationException("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid credentials")
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("User is inactive")
        return user, self._build_token_response(user)

    def authenticate_parent(self, phone_number: str, password: str) -> tuple[User, dict[str, str]]:
        """Authenticate a parent with phone number and password."""
        user = self.user_repo.get_by_phone(phone_number)
        if not user or user.role != UserRole.PARENT:
            raise AuthenticationException("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid credentials")
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("User is inactive")
        if not self.parent_repo.get_by_user_id(user.user_id):
            raise AuthenticationException("Parent account is not linked")
        return user, self._build_token_response(user)

    def authenticate_admin(self, email: str, password: str) -> tuple[Admin, dict[str, str]]:
        """Authenticate an internal platform admin."""
        admin = self.admin_repo.get_by_email(email)
        if not admin or not verify_password(password, admin.password_hash):
            raise AuthenticationException("Invalid credentials")
        if admin.status != "active":
            raise AuthenticationException("Admin is inactive")

        admin.last_login_at = utcnow()
        self.db.commit()
        claims = {"sub": str(admin.admin_id), "role": "admin", "email": admin.email, "phone": admin.phone}
        return admin, {
            "access_token": create_access_token(claims),
            "refresh_token": create_refresh_token(claims),
            "token_type": "bearer",
        }

    def refresh_tokens(self, refresh_token: str) -> dict[str, str]:
        """Refresh access and refresh tokens."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationException("Invalid or expired refresh token")

        claims = {
            "sub": payload.get("sub"),
            "role": payload.get("role"),
            "kindergarten_id": payload.get("kindergarten_id"),
            "parent_id": payload.get("parent_id"),
            "email": payload.get("email"),
            "phone": payload.get("phone"),
        }
        revoke_token(refresh_token)
        return {
            "access_token": create_access_token(claims),
            "refresh_token": create_refresh_token(claims),
            "token_type": "bearer",
        }

    def logout(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Invalidate currently issued tokens for the running process."""
        revoke_token(access_token)
        if refresh_token:
            revoke_token(refresh_token)

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.user_repo.get_by_id(user_id)

    def create_parent_account(
        self,
        current_user: User,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str,
        email: Optional[str] = None,
        address: Optional[str] = None,
        birth_date=None,
        child_ids: Optional[list[str]] = None,
    ) -> Parent:
        """Create a parent account from inside a kindergarten tenant."""
        kindergarten = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kindergarten:
            raise NotFoundException("Kindergarten not found for this user")
        if self.user_repo.user_exists(phone=phone_number):
            raise ConflictException("User with this phone already exists")
        if email and self.parent_repo.get_by_email(email):
            raise ConflictException("Parent with this email already exists")

        user = self.user_repo.create_user(
            role=UserRole.PARENT,
            phone=phone_number,
            email="",
            password_hash=get_password_hash(password),
            status=UserStatus.ACTIVE,
        )
        user.phone_or_email = phone_number
        self.db.flush()

        parent = Parent(
            parent_id=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            phone=phone_number,
            email=email,
            address=address,
            birth_date=birth_date,
        )
        self.db.add(parent)
        self.db.flush()

        self.db.add(
            ParentUser(
                parent_user_id=str(uuid.uuid4()),
                user_id=user.user_id,
                parent_id=parent.parent_id,
            )
        )

        if child_ids:
            from app.models.child import ParentChildLink
            from app.repositories.child import ChildRepository

            child_repo = ChildRepository(self.db)
            for child_id in child_ids:
                child = child_repo.get_by_id(child_id)
                if not child or child.kindergarten_id != kindergarten.kindergarten_id:
                    raise NotFoundException(f"Child {child_id} not found in your kindergarten")
                self.db.add(
                    ParentChildLink(
                        link_id=str(uuid.uuid4()),
                        parent_id=parent.parent_id,
                        child_id=child_id,
                    )
                )

        self.db.commit()
        self.db.refresh(parent)
        return parent
