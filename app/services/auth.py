"""Authentication service."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import AuthenticationException, ConflictException
from app.models.user import User, UserRole, UserStatus
from app.models.parent import Parent, ParentUser
from app.repositories.user import UserRepository


class AuthService:
    """Service for authentication and user management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def register_user(self, role: UserRole, phone: Optional[str], email: str, password: str) -> User:
        """Register a new user."""
        # Check if user already exists
        if self.user_repo.user_exists(email=email, phone=phone):
            raise ConflictException("User with this email or phone already exists")
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = get_password_hash(password)
        
        user = self.user_repo.create_user(
            user_id=user_id,
            role=role,
            phone=phone,
            email=email,
            password_hash=password_hash,
            status=UserStatus.ACTIVE.value
        )
        
        return user
    
    def login(self, phone_or_email: str, password: str) -> tuple[User, str]:
        """Authenticate user and return user object and JWT token."""
        # Find user
        user = self.user_repo.get_by_email_or_phone(phone_or_email)
        if not user:
            raise AuthenticationException("Invalid credentials")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            raise AuthenticationException("Invalid credentials")
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("User is inactive")
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.user_id})
        
        return user, access_token
    
    def register_parent_user(self, phone: Optional[str], email: str, password: str,
                            first_name: str, last_name: str,
                            phone_profile: str, address: Optional[str] = None,
                            birth_date=None) -> tuple[User, Parent]:
        """Register a parent user with parent profile."""
        # Register user
        user = self.register_user(UserRole.PARENT, phone, email, password)
        
        # Create parent profile
        parent_id = str(uuid.uuid4())
        parent = Parent(
            parent_id=parent_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone_profile,
            email=email,
            address=address,
            birth_date=birth_date
        )
        self.db.add(parent)
        
        # Link parent to user
        parent_user_id = str(uuid.uuid4())
        parent_user = ParentUser(
            parent_user_id=parent_user_id,
            user_id=user.user_id,
            parent_id=parent_id
        )
        self.db.add(parent_user)
        
        self.db.commit()
        self.db.refresh(parent)
        
        return user, parent
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.user_repo.get_by_id(user_id)
