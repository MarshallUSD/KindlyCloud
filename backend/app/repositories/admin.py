"""Admin repository."""
from typing import Optional

from sqlalchemy import or_
from sqlalchemy import inspect
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository):
    """Repository for the Admin model."""

    def __init__(self, db: Session):
        super().__init__(db, Admin)

    def table_exists(self) -> bool:
        """Check whether the admins table exists in the current database."""
        bind = self.db.get_bind()
        if bind is None:
            return False
        return inspect(bind).has_table("admins")

    def get_by_id(self, admin_id: int) -> Optional[Admin]:
        """Get admin by primary key."""
        if not self.table_exists():
            return None
        try:
            return self.get_by_id_field("admin_id", admin_id)
        except ProgrammingError:
            self.db.rollback()
            return None

    def get_by_email(self, email: str) -> Optional[Admin]:
        """Get admin by email."""
        if not self.table_exists():
            return None
        try:
            return self.db.query(Admin).filter(Admin.email == email).first()
        except ProgrammingError:
            self.db.rollback()
            return None

    def get_by_phone(self, phone: str) -> Optional[Admin]:
        """Get admin by phone."""
        if not self.table_exists():
            return None
        try:
            return self.db.query(Admin).filter(Admin.phone == phone).first()
        except ProgrammingError:
            self.db.rollback()
            return None

    def get_by_email_or_phone(self, email_or_phone: str) -> Optional[Admin]:
        """Get admin by email or phone."""
        if not self.table_exists():
            return None
        try:
            return self.db.query(Admin).filter(
                or_(Admin.email == email_or_phone, Admin.phone == email_or_phone)
            ).first()
        except ProgrammingError:
            self.db.rollback()
            return None
