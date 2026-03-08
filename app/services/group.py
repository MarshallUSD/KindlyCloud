"""Group service."""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.user import User
from app.repositories.group import GroupRepository
from app.repositories.kindergarten import KindergartenRepository
from app.core.exceptions import NotFoundException, AuthorizationException


class GroupService:
    """Service for group management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.group_repo = GroupRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
    
    def create_group(self, current_user: User, group_name: str, teacher_id: str,
                    start_date, end_date=None, schedule: Optional[str] = None,
                    max_capacity: Optional[int] = None) -> Group:
        """Create a new group (kindergarten staff only)."""
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")
        
        group_id = str(uuid.uuid4())
        return self.group_repo.create_group(
            group_id=group_id,
            kindergarten_id=kinder.kindergarten_id,
            group_name=group_name,
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            schedule=schedule,
            max_capacity=max_capacity
        )
    
    def get_group(self, group_id: str) -> Group:
        """Get group by ID."""
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundException("Group not found")
        return group
    
    def update_group(self, current_user: User, group_id: str, **kwargs) -> Group:
        """Update group."""
        group = self.get_group(group_id)
        
        # Check authorization
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder or kinder.kindergarten_id != group.kindergarten_id:
            raise AuthorizationException("You do not have permission to update this group")
        
        for key, value in kwargs.items():
            if value is not None and hasattr(group, key):
                setattr(group, key, value)
        
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def delete_group(self, current_user: User, group_id: str) -> bool:
        """Delete group."""
        group = self.get_group(group_id)
        
        # Check authorization
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder or kinder.kindergarten_id != group.kindergarten_id:
            raise AuthorizationException("You do not have permission to delete this group")
        
        self.db.delete(group)
        self.db.commit()
        return True
    
    def list_groups_for_kindergarten(self, current_user: User, skip: int = 0, 
                                     limit: int = 20) -> Tuple[List[Group], int]:
        """List groups for user's kindergarten."""
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")
        
        return self.group_repo.get_by_kindergarten(kinder.kindergarten_id, skip=skip, limit=limit)
