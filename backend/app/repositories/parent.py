"""Parent repository."""
from typing import Optional

from sqlalchemy import inspect
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.models.parent import Parent, ParentUser
from app.repositories.base import BaseRepository


class ParentRepository(BaseRepository):
    """Repository for Parent model."""
    
    def __init__(self, db: Session):
        super().__init__(db, Parent)

    def _table_exists(self, table_name: str) -> bool:
        """Check whether a table exists in the current database."""
        bind = self.db.get_bind()
        if bind is None:
            return False
        return inspect(bind).has_table(table_name)
    
    def get_by_id(self, parent_id: str) -> Optional[Parent]:
        """Get parent by parent_id."""
        if not self._table_exists("parents"):
            return None
        try:
            return self.get_by_id_field('parent_id', parent_id)
        except ProgrammingError:
            self.db.rollback()
            return None
    
    def get_by_email(self, email: str) -> Optional[Parent]:
        """Get parent by email."""
        if not self._table_exists("parents"):
            return None
        try:
            return self.db.query(Parent).filter(Parent.email == email).first()
        except ProgrammingError:
            self.db.rollback()
            return None
    
    def get_by_phone(self, phone: str) -> Optional[Parent]:
        """Get parent by phone."""
        if not self._table_exists("parents"):
            return None
        try:
            return self.db.query(Parent).filter(Parent.phone == phone).first()
        except ProgrammingError:
            self.db.rollback()
            return None

    def get_by_telegram_id(self, telegram_id: str | None) -> Optional[Parent]:
        """Get parent by telegram identifier."""
        if not telegram_id or not self._table_exists("parents"):
            return None
        try:
            return self.db.query(Parent).filter(Parent.telegram_id == telegram_id).first()
        except ProgrammingError:
            self.db.rollback()
            return None
    
    def get_by_user_id(self, user_id: str) -> Optional[Parent]:
        """Get parent by user_id."""
        if not self._table_exists("parent_users") or not self._table_exists("parents"):
            return None
        try:
            parent_user = self.db.query(ParentUser).filter(
                ParentUser.user_id == user_id
            ).first()
        except ProgrammingError:
            self.db.rollback()
            return None
        if parent_user:
            return self.get_by_id(parent_user.parent_id)
        return None
    
    def create_parent(self, parent_id: str, first_name: str, last_name: str,
                     phone: str, email: Optional[str] = None,
                     address: Optional[str] = None, birth_date=None) -> Parent:
        """Create a new parent."""
        parent = Parent(
            parent_id=parent_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            birth_date=birth_date
        )
        self.db.add(parent)
        self.db.commit()
        self.db.refresh(parent)
        return parent
