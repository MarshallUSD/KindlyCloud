"""Group repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.group import Group
from app.repositories.base import BaseRepository


class GroupRepository(BaseRepository):
    """Repository for Group model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Group)
    
    def get_by_id(self, group_id: str) -> Optional[Group]:
        """Get group by group_id."""
        return self.get_by_id_field('group_id', group_id)
    
    def get_by_kindergarten(self, kindergarten_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Group], int]:
        """Get groups by kindergarten."""
        total = self.db.query(func.count(Group.group_id)).filter(
            Group.kindergarten_id == kindergarten_id
        ).scalar()
        records = self.db.query(Group).filter(
            Group.kindergarten_id == kindergarten_id
        ).offset(skip).limit(limit).all()
        return records, total
    
    def get_by_teacher(self, teacher_id: str) -> List[Group]:
        """Get groups by teacher."""
        return self.db.query(Group).filter(Group.teacher_id == teacher_id).all()
    
    def create_group(self, group_id: str, kindergarten_id: str, group_name: str,
                    teacher_id: str, start_date, end_date=None,
                    schedule: Optional[str] = None, max_capacity: Optional[int] = None) -> Group:
        """Create a new group."""
        group = Group(
            group_id=group_id,
            kindergarten_id=kindergarten_id,
            group_name=group_name,
            teacher_id=teacher_id,
            start_date=start_date,
            end_date=end_date,
            schedule=schedule,
            max_capacity=max_capacity
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group
