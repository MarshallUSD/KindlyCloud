"""User repository."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Repository for User model."""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_phone(self, phone: str) -> Optional[User]:
        """Get user by phone."""
        return self.db.query(User).filter(User.phone == phone).first()
    
    def get_by_email_or_phone(self, email_or_phone: str) -> Optional[User]:
        """Get user by email or phone."""
        return self.db.query(User).filter(
            or_(User.email == email_or_phone, User.phone == email_or_phone)
        ).first()
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id."""
        return self.get_by_id_field('user_id', user_id)
    
    def create_user(self, user_id: str, role: str, phone: Optional[str], 
                   email: str, password_hash: str, status: str = "active") -> User:
        """Create a new user."""
        user = User(
            user_id=user_id,
            role=role,
            phone=phone,
            email=email,
            password_hash=password_hash,
            status=status
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user_id: str, data: dict) -> Optional[User]:
        """Update user."""
        return self.update('user_id', user_id, data)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        return self.delete('user_id', user_id)
    
    def user_exists(self, email: str = None, phone: str = None, user_id: str = None) -> bool:
        """Check if user exists by email, phone, or user_id."""
        query = self.db.query(User)
        
        if user_id:
            return query.filter(User.user_id == user_id).first() is not None
        
        filters = []
        if email:
            filters.append(User.email == email)
        if phone:
            filters.append(User.phone == phone)
        
        if filters:
            return query.filter(or_(*filters)).first() is not None
        
        return False
