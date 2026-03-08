from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.group import Group

router = APIRouter()


@router.get("/")
async def list_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@router.post("/")
async def create_group(group_data: dict, db: Session = Depends(get_db)):
    db_group = Group(**group_data)
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


@router.get("/{group_id}")
async def get_group(group_id: int, db: Session = Depends(get_db)):
    return db.query(Group).filter(Group.id == group_id).first()


@router.delete("/{group_id}")
async def delete_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group:
        db.delete(db_group)
        db.commit()
    return {"deleted": True}
