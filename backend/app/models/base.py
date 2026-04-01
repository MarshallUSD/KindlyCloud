"""Base model configuration."""
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declarative_base

from app.core.time import utcnow

Base = declarative_base()


class BaseModel(Base):
    """Abstract base model with common fields."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
