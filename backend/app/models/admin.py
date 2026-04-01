"""Admin model."""
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.base import Base
from app.core.time import utcnow


class Admin(Base):
    """Administrator account model."""

    __tablename__ = "admins"

    admin_id_type = BigInteger().with_variant(Integer, "sqlite")

    admin_id = Column(admin_id_type, primary_key=True, autoincrement=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)
    email = Column(String(150), unique=True, nullable=True, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(30), nullable=False, default="super_admin")
    status = Column(String(20), nullable=False, default="active")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    posts = relationship(
        "Post",
        back_populates="creator",
        foreign_keys="Post.created_by_admin_id",
    )
    feedback_handled = relationship(
        "Feedback",
        back_populates="handled_by_admin",
        foreign_keys="Feedback.handled_by_admin_id",
    )
