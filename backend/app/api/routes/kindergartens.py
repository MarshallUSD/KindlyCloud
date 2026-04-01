from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.kindergarten import KindergartenCreate, KindergartenResponse, KindergartenUpdate
from app.models.kindergarten import Kindergarten

router = APIRouter()


@router.get("/", response_model=list[KindergartenResponse])
async def list_kindergartens(db: Session = Depends(get_db)):
    return db.query(Kindergarten).all()


@router.post("/", response_model=KindergartenResponse)
async def create_kindergarten(kindergarten: KindergartenCreate, db: Session = Depends(get_db)):
    db_kindergarten = Kindergarten(**kindergarten.dict())
    db.add(db_kindergarten)
    db.commit()
    db.refresh(db_kindergarten)
    return db_kindergarten


@router.get("/{kindergarten_id}", response_model=KindergartenResponse)
async def get_kindergarten(kindergarten_id: int, db: Session = Depends(get_db)):
    return db.query(Kindergarten).filter(Kindergarten.id == kindergarten_id).first()


@router.put("/{kindergarten_id}", response_model=KindergartenResponse)
async def update_kindergarten(kindergarten_id: int, kindergarten: KindergartenUpdate, db: Session = Depends(get_db)):
    db_kindergarten = db.query(Kindergarten).filter(Kindergarten.id == kindergarten_id).first()
    if db_kindergarten:
        for key, value in kindergarten.dict(exclude_unset=True).items():
            setattr(db_kindergarten, key, value)
        db.commit()
        db.refresh(db_kindergarten)
    return db_kindergarten


@router.delete("/{kindergarten_id}")
async def delete_kindergarten(kindergarten_id: int, db: Session = Depends(get_db)):
    db_kindergarten = db.query(Kindergarten).filter(Kindergarten.id == kindergarten_id).first()
    if db_kindergarten:
        db.delete(db_kindergarten)
        db.commit()
    return {"deleted": True}
