"""Child service."""
import uuid
from typing import Optional, List, Tuple
from datetime import date
from sqlalchemy.orm import Session

from app.models.child import Child, ChildStatus
from app.models.user import User
from app.repositories.child import ChildRepository
from app.repositories.kindergarten import KindergartenRepository
from app.core.exceptions import NotFoundException


class ChildService:
    """Service for child management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.child_repo = ChildRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
    
    def create_child(self, first_name: str, last_name: str, birth_date: date,
                    gender: Optional[str] = None, address: Optional[str] = None) -> Child:
        """Create a new child record."""
        child_id = str(uuid.uuid4())
        return self.child_repo.create_child(
            child_id=child_id,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            gender=gender,
            address=address
        )
    
    def get_child(self, child_id: str) -> Child:
        """Get child by ID."""
        child = self.child_repo.get_by_id(child_id)
        if not child:
            raise NotFoundException("Child not found")
        return child
    
    def update_child(self, child_id: str, **kwargs) -> Child:
        """Update child profile."""
        child = self.get_child(child_id)
        
        for key, value in kwargs.items():
            if value is not None and hasattr(child, key):
                setattr(child, key, value)
        
        self.db.commit()
        self.db.refresh(child)
        return child
    
    def list_children(self, skip: int = 0, limit: int = 20) -> Tuple[List[Child], int]:
        """List all children."""
        return self.child_repo.list(skip=skip, limit=limit)
