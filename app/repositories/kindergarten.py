"""Kindergarten repository."""
from typing import List, Optional

from sqlalchemy import func, inspect
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.models.kindergarten import Kindergarten, KindergartenUser
from app.repositories.base import BaseRepository


class KindergartenRepository(BaseRepository):
    """Repository for Kindergarten model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Kindergarten)

    def _table_exists(self, table_name: str) -> bool:
        """Check whether a table exists in the current database."""
        bind = self.db.get_bind()
        if bind is None:
            return False
        return inspect(bind).has_table(table_name)
    
    def get_by_id(self, kindergarten_id: str) -> Optional[Kindergarten]:
        """Get kindergarten by kindergarten_id."""
        if not self._table_exists("kindergartens"):
            return None
        try:
            return self.get_by_id_field('kindergarten_id', kindergarten_id)
        except ProgrammingError:
            self.db.rollback()
            return None
    
    def get_by_email(self, email: str) -> Optional[Kindergarten]:
        """Get kindergarten by email."""
        if not self._table_exists("kindergartens"):
            return None
        try:
            return self.db.query(Kindergarten).filter(Kindergarten.email == email).first()
        except ProgrammingError:
            self.db.rollback()
            return None
    
    def create_kindergarten(
        self,
        kindergarten_id: str,
        kinder_name: str,
        region: Optional[str] = None,
        city: Optional[str] = None,
        district: Optional[str] = None,
        street: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        payment_note: Optional[str] = None,
    ) -> Kindergarten:
        """Create a new kindergarten."""
        kinder = Kindergarten(
            kindergarten_id=kindergarten_id,
            kinder_name=kinder_name,
            region=region,
            city=city,
            district=district,
            street=street,
            address=address,
            phone=phone,
            email=email,
            payment_note=payment_note
        )
        self.db.add(kinder)
        self.db.commit()
        self.db.refresh(kinder)
        return kinder
    
    def list_verified(self, skip: int = 0, limit: int = 20) -> tuple[List[Kindergarten], int]:
        """Get list of verified kindergartens."""
        total = self.db.query(func.count(Kindergarten.kindergarten_id)).filter(
            Kindergarten.is_verified == True
        ).scalar()
        records = self.db.query(Kindergarten).filter(
            Kindergarten.is_verified == True
        ).offset(skip).limit(limit).all()
        return records, total
    
    def get_by_user_id(self, user_id: str) -> Optional[Kindergarten]:
        """Get kindergarten by user_id (owner/staff)."""
        if not self._table_exists("kindergarten_users") or not self._table_exists("kindergartens"):
            return None
        try:
            kinder_user = self.db.query(KindergartenUser).filter(
                KindergartenUser.user_id == user_id
            ).first()
        except ProgrammingError:
            self.db.rollback()
            return None
        if kinder_user:
            return self.get_by_id(kinder_user.kindergarten_id)
        return None
