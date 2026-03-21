"""Child repository."""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.child import Child, ParentChildLink
from app.repositories.base import BaseRepository


class ChildRepository(BaseRepository):
    """Repository for Child model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Child)
    
    def get_by_id(self, child_id: str) -> Optional[Child]:
        """Get child by child_id."""
        return self.get_by_id_field('child_id', child_id)
    
    def create_child(
        self,
        child_id: str,
        first_name: str,
        last_name: str,
        birth_date: date,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        kindergarten_id: Optional[str] = None,
    ) -> Child:
        """Create a new child."""
        child = Child(
            child_id=child_id,
            kindergarten_id=kindergarten_id,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            gender=gender,
            address=address
        )
        self.db.add(child)
        self.db.commit()
        self.db.refresh(child)
        return child
    
    def get_children_by_parent(self, parent_id: str, active_only: bool = True) -> List[Child]:
        """Get all children linked to a parent."""
        query = self.db.query(Child).join(
            ParentChildLink, ParentChildLink.child_id == Child.child_id
        ).filter(ParentChildLink.parent_id == parent_id)
        
        if active_only:
            query = query.filter(ParentChildLink.status == "active")
        
        return query.all()
    
    def link_parent_to_child(self, link_id: str, parent_id: str, child_id: str,
                            status: str = "active", note: Optional[str] = None) -> ParentChildLink:
        """Link a parent to a child."""
        link = ParentChildLink(
            link_id=link_id,
            parent_id=parent_id,
            child_id=child_id,
            status=status,
            note=note
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link
    
    def get_parent_child_link(self, link_id: str) -> Optional[ParentChildLink]:
        """Get parent-child link."""
        return self.db.query(ParentChildLink).filter(
            ParentChildLink.link_id == link_id
        ).first()
