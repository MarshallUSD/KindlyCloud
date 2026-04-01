from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.parent import ParentCreate, ParentResponse, ParentUpdate
from app.models.parent import Parent

router = APIRouter()


@router.get("/", response_model=list[ParentResponse])
async def list_parents(db: Session = Depends(get_db)):
    return db.query(Parent).all()


@router.post("/", response_model=ParentResponse)
async def create_parent(parent: ParentCreate, db: Session = Depends(get_db)):
    db_parent = Parent(**parent.dict())
    db.add(db_parent)
    db.commit()
    db.refresh(db_parent)
    return db_parent


@router.get("/{parent_id}", response_model=ParentResponse)
async def get_parent(parent_id: int, db: Session = Depends(get_db)):
    return db.query(Parent).filter(Parent.id == parent_id).first()


@router.put("/{parent_id}", response_model=ParentResponse)
async def update_parent(parent_id: int, parent: ParentUpdate, db: Session = Depends(get_db)):
    db_parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if db_parent:
        for key, value in parent.dict(exclude_unset=True).items():
            setattr(db_parent, key, value)
        db.commit()
        db.refresh(db_parent)
    return db_parent


@router.delete("/{parent_id}")
async def delete_parent(parent_id: int, db: Session = Depends(get_db)):
    db_parent = db.query(Parent).filter(Parent.id == parent_id).first()
    if db_parent:
        db.delete(db_parent)
        db.commit()
    return {"deleted": True}
