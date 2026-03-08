from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.payment import Payment

router = APIRouter()


@router.get("/")
async def list_payments(db: Session = Depends(get_db)):
    return db.query(Payment).all()


@router.post("/")
async def create_payment(payment_data: dict, db: Session = Depends(get_db)):
    db_payment = Payment(**payment_data)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


@router.get("/{payment_id}")
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    return db.query(Payment).filter(Payment.id == payment_id).first()


@router.delete("/{payment_id}")
async def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if db_payment:
        db.delete(db_payment)
        db.commit()
    return {"deleted": True}
