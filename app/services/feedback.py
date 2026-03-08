"""Feedback service."""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.feedback import Feedback, FeedbackStatus
from app.models.user import User
from app.repositories.feedback import FeedbackRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.parent import ParentRepository
from app.core.exceptions import NotFoundException, AuthorizationException


class FeedbackService:
    """Service for feedback management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.feedback_repo = FeedbackRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.parent_repo = ParentRepository(db)
    
    def create_feedback_from_kindergarten(self, current_user: User, message: str,
                                         child_id: Optional[str] = None) -> Feedback:
        """Create feedback from kindergarten."""
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")
        
        feedback_id = str(uuid.uuid4())
        return self.feedback_repo.create_feedback(
            feedback_id=feedback_id,
            message=message,
            from_kindergarten_id=kinder.kindergarten_id,
            child_id=child_id
        )
    
    def create_feedback_from_parent(self, current_user: User, message: str,
                                   child_id: Optional[str] = None) -> Feedback:
        """Create feedback from parent."""
        parent = self.parent_repo.get_by_user_id(current_user.user_id)
        if not parent:
            raise AuthorizationException("Parent profile not found")
        
        feedback_id = str(uuid.uuid4())
        return self.feedback_repo.create_feedback(
            feedback_id=feedback_id,
            message=message,
            from_parent_id=parent.parent_id,
            child_id=child_id
        )
    
    def get_feedback(self, feedback_id: str) -> Feedback:
        """Get feedback by ID."""
        feedback = self.feedback_repo.get_by_id(feedback_id)
        if not feedback:
            raise NotFoundException("Feedback not found")
        return feedback
    
    def update_feedback_status(self, current_user: User, feedback_id: str,
                              status: FeedbackStatus) -> Feedback:
        """Update feedback status (admin only)."""
        return self.feedback_repo.update_status(
            feedback_id=feedback_id,
            status=status,
            handled_by_admin_user_id=current_user.user_id
        )
    
    def list_all_feedback(self, skip: int = 0, limit: int = 20) -> Tuple[List[Feedback], int]:
        """List all feedback (admin view)."""
        return self.feedback_repo.get_all_feedback(skip=skip, limit=limit)
    
    def list_feedback_by_status(self, status: FeedbackStatus, skip: int = 0,
                               limit: int = 20) -> Tuple[List[Feedback], int]:
        """List feedback by status (admin view)."""
        return self.feedback_repo.get_feedback_by_status(status, skip=skip, limit=limit)
