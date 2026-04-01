"""Kindergarten service."""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.kindergarten import Kindergarten, KindergartenUser
from app.models.user import User
from app.repositories.kindergarten import KindergartenRepository
from app.core.exceptions import NotFoundException, AuthorizationException


class KindergartenService:
    """Service for kindergarten management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = KindergartenRepository(db)
    
    def create_kindergarten(self, current_user: User, kinder_name: str, region: Optional[str] = None,
                           city: Optional[str] = None, district: Optional[str] = None, 
                           street: Optional[str] = None, address: Optional[str] = None,
                           phone: Optional[str] = None, email: Optional[str] = None,
                           payment_note: Optional[str] = None) -> Kindergarten:
        """Create a new kindergarten (only kindergarten role)."""
        existing = self.repo.get_by_user_id(current_user.user_id)
        if existing:
            raise AuthorizationException("User already belongs to a kindergarten")

        kindergarten_id = str(uuid.uuid4())
        
        kinder = self.repo.create_kindergarten(
            kindergarten_id=kindergarten_id,
            kinder_name=kinder_name,
            region=region,
            city=city,
            district=district,
            street=street,
            address=address,
            phone=phone,
            email=email,
            payment_note=payment_note
        )
        
        # Create kindergarten user link (owner)
        kinder_user_id = str(uuid.uuid4())
        kinder_user = KindergartenUser(
            kindergarten_user_id=kinder_user_id,
            user_id=current_user.user_id,
            kindergarten_id=kindergarten_id,
            position="Director",
            is_owner=True
        )
        self.db.add(kinder_user)
        self.db.commit()
        
        return kinder
    
    def get_kindergarten(self, kindergarten_id: str) -> Kindergarten:
        """Get kindergarten by ID."""
        kinder = self.repo.get_by_id(kindergarten_id)
        if not kinder:
            raise NotFoundException("Kindergarten not found")
        return kinder
    
    def get_my_kindergarten(self, current_user: User) -> Kindergarten:
        """Get current user's kindergarten."""
        kinder = self.repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise NotFoundException("No kindergarten found for this user")
        return kinder
    
    def update_kindergarten(self, current_user: User, kindergarten_id: str, **kwargs) -> Kindergarten:
        """Update kindergarten (only owner/staff)."""
        kinder = self.get_kindergarten(kindergarten_id)
        
        # Check authorization
        kinder_user = self.db.query(KindergartenUser).filter(
            KindergartenUser.user_id == current_user.user_id,
            KindergartenUser.kindergarten_id == kindergarten_id
        ).first()
        
        if not kinder_user:
            raise AuthorizationException("You do not have permission to update this kindergarten")
        
        # Update fields
        for key, value in kwargs.items():
            if value is not None and hasattr(kinder, key):
                setattr(kinder, key, value)
        
        self.db.commit()
        self.db.refresh(kinder)
        return kinder
    
    def list_kindergartens(self, skip: int = 0, limit: int = 20) -> Tuple[List[Kindergarten], int]:
        """List all kindergartens."""
        return self.repo.list(skip=skip, limit=limit)
    
    def list_verified_kindergartens(self, skip: int = 0, limit: int = 20) -> Tuple[List[Kindergarten], int]:
        """List verified kindergartens."""
        return self.repo.list_verified(skip=skip, limit=limit)
