"""Kindergarten repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.kindergarten import Kindergarten, KindergartenUser
from app.repositories.base import BaseRepository


class KindergartenRepository(BaseRepository):
    """Repository for Kindergarten model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Kindergarten)
    
    def get_by_id(self, kindergarten_id: str) -> Optional[Kindergarten]:
        """Get kindergarten by kindergarten_id."""
        return self.get_by_id_field('kindergarten_id', kindergarten_id)
    
    def get_by_email(self, email: str) -> Optional[Kindergarten]:
        """Get kindergarten by email."""
        return self.db.query(Kindergarten).filter(Kindergarten.email == email).first()
    
    def create_kindergarten(self, kindergarten_id: str, kinder_name: str, 
                           region: Optional[str] = None, district: Optional[str] = None,
                           address: Optional[str] = None, phone: Optional[str] = None,
                           email: Optional[str] = None, payment_note: Optional[str] = None) -> Kindergarten:
        """Create a new kindergarten."""
        kinder = Kindergarten(
            kindergarten_id=kindergarten_id,
            kinder_name=kinder_name,
            region=region,
            district=district,
            address=address,
            phone=phone,
            email=email,
            payment_note=payment_note
        )
        self.db.add(kinder)
        self.db.commit()
        self.db.refresh(kinder)
        return kinder
    
    def list_verified(self, skip: int = 0, limit: int = 20) -> tuple[List[Kindergarten], int]:
        """Get list of verified kindergartens."""
        total = self.db.query(func.count(Kindergarten.kindergarten_id)).filter(
            Kindergarten.is_verified == True
        ).scalar()
        records = self.db.query(Kindergarten).filter(
            Kindergarten.is_verified == True
        ).offset(skip).limit(limit).all()
        return records, total
    
    def get_by_user_id(self, user_id: str) -> Optional[Kindergarten]:
        """Get kindergarten by user_id (owner/staff)."""
        kinder_user = self.db.query(KindergartenUser).filter(
            KindergartenUser.user_id == user_id
        ).first()
        if kinder_user:
            return self.get_by_id(kinder_user.kindergarten_id)
        return None
