"""Feedback repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.feedback import Feedback, FeedbackStatus
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository):
    """Repository for Feedback model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Feedback)
    
    def get_by_id(self, feedback_id: str) -> Optional[Feedback]:
        """Get feedback by feedback_id."""
        return self.get_by_id_field('feedback_id', feedback_id)
    
    def get_all_feedback(self, skip: int = 0, limit: int = 20) -> tuple[List[Feedback], int]:
        """Get all feedback (admin view)."""
        total = self.db.query(func.count(Feedback.feedback_id)).scalar()
        records = self.db.query(Feedback).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
        return records, total
    
    def get_feedback_by_status(self, status: FeedbackStatus, skip: int = 0, limit: int = 20) -> tuple[List[Feedback], int]:
        """Get feedback by status."""
        total = self.db.query(func.count(Feedback.feedback_id)).filter(
            Feedback.status == status
        ).scalar()
        records = self.db.query(Feedback).filter(
            Feedback.status == status
        ).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
        return records, total
    
    def get_feedback_from_kindergarten(self, kindergarten_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Feedback], int]:
        """Get feedback from a kindergarten."""
        total = self.db.query(func.count(Feedback.feedback_id)).filter(
            Feedback.from_kindergarten_id == kindergarten_id
        ).scalar()
        records = self.db.query(Feedback).filter(
            Feedback.from_kindergarten_id == kindergarten_id
        ).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
        return records, total
    
    def get_feedback_from_parent(self, parent_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Feedback], int]:
        """Get feedback from a parent."""
        total = self.db.query(func.count(Feedback.feedback_id)).filter(
            Feedback.from_parent_id == parent_id
        ).scalar()
        records = self.db.query(Feedback).filter(
            Feedback.from_parent_id == parent_id
        ).order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
        return records, total
    
    def create_feedback(self, feedback_id: str, message: str,
                       from_kindergarten_id: Optional[str] = None,
                       from_parent_id: Optional[str] = None,
                       child_id: Optional[str] = None) -> Feedback:
        """Create new feedback."""
        feedback = Feedback(
            feedback_id=feedback_id,
            message=message,
            from_kindergarten_id=from_kindergarten_id,
            from_parent_id=from_parent_id,
            child_id=child_id
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
    
    def update_status(self, feedback_id: str, status: FeedbackStatus,
                     handled_by_admin_id: Optional[int] = None) -> Optional[Feedback]:
        """Update feedback status."""
        feedback = self.get_by_id(feedback_id)
        if not feedback:
            return None
        
        feedback.status = status
        if handled_by_admin_id is not None:
            feedback.handled_by_admin_id = handled_by_admin_id
        
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
