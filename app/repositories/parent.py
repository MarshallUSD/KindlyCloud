"""Parent repository."""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.parent import Parent, ParentUser
from app.repositories.base import BaseRepository


class ParentRepository(BaseRepository):
    """Repository for Parent model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Parent)
    
    def get_by_id(self, parent_id: str) -> Optional[Parent]:
        """Get parent by parent_id."""
        return self.get_by_id_field('parent_id', parent_id)
    
    def get_by_email(self, email: str) -> Optional[Parent]:
        """Get parent by email."""
        return self.db.query(Parent).filter(Parent.email == email).first()
    
    def get_by_phone(self, phone: str) -> Optional[Parent]:
        """Get parent by phone."""
        return self.db.query(Parent).filter(Parent.phone == phone).first()
    
    def get_by_user_id(self, user_id: str) -> Optional[Parent]:
        """Get parent by user_id."""
        parent_user = self.db.query(ParentUser).filter(
            ParentUser.user_id == user_id
        ).first()
        if parent_user:
            return self.get_by_id(parent_user.parent_id)
        return None
    
    def create_parent(self, parent_id: str, first_name: str, last_name: str,
                     phone: str, email: Optional[str] = None,
                     address: Optional[str] = None, birth_date=None) -> Parent:
        """Create a new parent."""
        parent = Parent(
            parent_id=parent_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            birth_date=birth_date
        )
        self.db.add(parent)
        self.db.commit()
        self.db.refresh(parent)
        return parent
