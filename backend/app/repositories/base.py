"""Base repository with common CRUD operations."""
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from sqlalchemy import func

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository providing generic CRUD operations."""
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def get(self, id: str) -> Optional[T]:
        """Get a single record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first() if hasattr(self.model, 'id') else None
    
    def get_by_id_field(self, id_field: str, id_value: str) -> Optional[T]:
        """Get a single record by a specific ID field."""
        return self.db.query(self.model).filter(
            getattr(self.model, id_field) == id_value
        ).first()
    
    def list(self, skip: int = 0, limit: int = 20) -> tuple[List[T], int]:
        """Get a list of records with pagination."""
        total = self.db.query(func.count(self.model.id)).scalar() if hasattr(self.model, 'id') else 0
        records = self.db.query(self.model).offset(skip).limit(limit).all()
        return records, total
    
    def list_all(self) -> List[T]:
        """Get all records."""
        return self.db.query(self.model).all()
    
    def create(self, data: dict) -> T:
        """Create a new record."""
        record = self.model(**data)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def update(self, id_field: str, id_value: str, data: dict) -> Optional[T]:
        """Update an existing record."""
        record = self.get_by_id_field(id_field, id_value)
        if not record:
            return None
        
        for key, value in data.items():
            if value is not None and hasattr(record, key):
                setattr(record, key, value)
        
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def delete(self, id_field: str, id_value: str) -> bool:
        """Delete a record."""
        record = self.get_by_id_field(id_field, id_value)
        if not record:
            return False
        
        self.db.delete(record)
        self.db.commit()
        return True
    
    def exists(self, id_field: str, id_value: str) -> bool:
        """Check if a record exists."""
        return self.db.query(self.model).filter(
            getattr(self.model, id_field) == id_value
        ).first() is not None
