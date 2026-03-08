"""Enrollment service."""
import uuid
from typing import Optional, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.models.user import User
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.kindergarten import KindergartenRepository
from app.repositories.child import ChildRepository
from app.repositories.group import GroupRepository
from app.core.exceptions import NotFoundException, AuthorizationException


class EnrollmentService:
    """Service for enrollment management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.enrollment_repo = EnrollmentRepository(db)
        self.kindergarten_repo = KindergartenRepository(db)
        self.child_repo = ChildRepository(db)
        self.group_repo = GroupRepository(db)
    
    def create_enrollment(self, current_user: User, child_id: str, group_id: str,
                         enrol_date, total_fees: Optional[Decimal] = None) -> Enrollment:
        """Create enrollment (kindergarten staff)."""
        # Check authorization
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder:
            raise AuthorizationException("User does not belong to a kindergarten")
        
        group = self.group_repo.get_by_id(group_id)
        if not group or group.kindergarten_id != kinder.kindergarten_id:
            raise NotFoundException("Group not found or does not belong to your kindergarten")
        
        child = self.child_repo.get_by_id(child_id)
        if not child:
            raise NotFoundException("Child not found")
        
        enrol_id = str(uuid.uuid4())
        return self.enrollment_repo.create_enrollment(
            enrol_id=enrol_id,
            child_id=child_id,
            group_id=group_id,
            enrol_date=enrol_date,
            total_fees=total_fees
        )
    
    def get_enrollment(self, enrol_id: str) -> Enrollment:
        """Get enrollment by ID."""
        enrollment = self.enrollment_repo.get_by_id(enrol_id)
        if not enrollment:
            raise NotFoundException("Enrollment not found")
        return enrollment
    
    def list_enrollments_for_group(self, current_user: User, group_id: str,
                                   skip: int = 0, limit: int = 20) -> Tuple[List[Enrollment], int]:
        """List enrollments for a group."""
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundException("Group not found")
        
        kinder = self.kindergarten_repo.get_by_user_id(current_user.user_id)
        if not kinder or kinder.kindergarten_id != group.kindergarten_id:
            raise AuthorizationException("You do not have access to this group")
        
        return self.enrollment_repo.get_by_group(group_id, skip=skip, limit=limit)
