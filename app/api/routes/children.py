from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate
from app.models.child import Child

router = APIRouter()


@router.get("/", response_model=list[ChildResponse])
async def list_children(db: Session = Depends(get_db)):
    return db.query(Child).all()


@router.post("/", response_model=ChildResponse)
async def create_child(child: ChildCreate, db: Session = Depends(get_db)):
    db_child = Child(**child.dict())
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    return db_child


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(child_id: int, db: Session = Depends(get_db)):
    return db.query(Child).filter(Child.id == child_id).first()


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(child_id: int, child: ChildUpdate, db: Session = Depends(get_db)):
    db_child = db.query(Child).filter(Child.id == child_id).first()
    if db_child:
        for key, value in child.dict(exclude_unset=True).items():
            setattr(db_child, key, value)
        db.commit()
        db.refresh(db_child)
    return db_child


@router.delete("/{child_id}")
async def delete_child(child_id: int, db: Session = Depends(get_db)):
    db_child = db.query(Child).filter(Child.id == child_id).first()
    if db_child:
        db.delete(db_child)
        db.commit()
    return {"deleted": True}
