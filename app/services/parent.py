"""Parent service."""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.parent import Parent
from app.models.user import User
from app.repositories.parent import ParentRepository
from app.repositories.child import ChildRepository
from app.repositories.kindergarten import KindergartenRepository
from app.core.exceptions import NotFoundException


class ParentService:
    """Service for parent management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.parent_repo = ParentRepository(db)
        self.child_repo = ChildRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
    
    def create_parent(self, first_name: str, last_name: str, phone: str,
                     email: Optional[str] = None, address: Optional[str] = None,
                     birth_date=None) -> Parent:
        """Create a new parent profile."""
        parent_id = str(uuid.uuid4())
        return self.parent_repo.create_parent(
            parent_id=parent_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            birth_date=birth_date
        )
    
    def get_parent(self, parent_id: str) -> Parent:
        """Get parent by ID."""
        parent = self.parent_repo.get_by_id(parent_id)
        if not parent:
            raise NotFoundException("Parent not found")
        return parent
    
    def get_my_parent_profile(self, current_user: User) -> Parent:
        """Get current user's parent profile."""
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise NotFoundException("Parent profile not found")
        return parent
    
    def link_child(self, current_user: User, child_id: str, note: Optional[str] = None):
        """Link a child to the parent."""
        parent = self.get_my_parent_profile(current_user)
        child = self.child_repo.get_by_id(child_id)
        
        if not child:
            raise NotFoundException("Child not found")
        
        link_id = str(uuid.uuid4())
        return self.child_repo.link_parent_to_child(
            link_id=link_id,
            parent_id=parent.parent_id,
            child_id=child_id,
            note=note
        )
    
    def get_my_children(self, current_user: User) -> List:
        """Get all children linked to the parent."""
        parent = self.get_my_parent_profile(current_user)
        return self.child_repo.get_children_by_parent(parent.parent_id, active_only=True)
    
    def list_parents(self, skip: int = 0, limit: int = 20) -> Tuple[List[Parent], int]:
        """List all parents."""
        return self.parent_repo.list(skip=skip, limit=limit)
