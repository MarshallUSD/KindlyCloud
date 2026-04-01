"""Enrollment repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository):
    """Repository for Enrollment model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Enrollment)
    
    def get_by_id(self, enrol_id: str) -> Optional[Enrollment]:
        """Get enrollment by enrol_id."""
        return self.get_by_id_field('enrol_id', enrol_id)
    
    def get_by_child(self, child_id: str, status: Optional[EnrollmentStatus] = None) -> List[Enrollment]:
        """Get enrollments by child."""
        query = self.db.query(Enrollment).filter(Enrollment.child_id == child_id)
        if status:
            query = query.filter(Enrollment.status == status)
        return query.all()
    
    def get_by_group(self, group_id: str, skip: int = 0, limit: int = 20) -> tuple[List[Enrollment], int]:
        """Get enrollments by group."""
        total = self.db.query(func.count(Enrollment.enrol_id)).filter(
            Enrollment.group_id == group_id
        ).scalar()
        records = self.db.query(Enrollment).filter(
            Enrollment.group_id == group_id
        ).offset(skip).limit(limit).all()
        return records, total
    
    def create_enrollment(self, enrol_id: str, child_id: str, group_id: str,
                         enrol_date, total_fees: Optional[Decimal] = None) -> Enrollment:
        """Create a new enrollment."""
        enrollment = Enrollment(
            enrol_id=enrol_id,
            child_id=child_id,
            group_id=group_id,
            enrol_date=enrol_date,
            total_fees=total_fees,
            amount_paid=Decimal('0.00')
        )
        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def update_balance(self, enrol_id: str, amount_paid: Decimal) -> Optional[Enrollment]:
        """Update amount paid and calculate balance."""
        enrollment = self.get_by_id(enrol_id)
        if not enrollment:
            return None
        
        enrollment.amount_paid = amount_paid
        if enrollment.total_fees:
            enrollment.balance = enrollment.total_fees - amount_paid
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
