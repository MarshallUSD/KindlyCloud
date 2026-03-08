from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.attendance import Attendance

router = APIRouter()


@router.get("/")
async def list_attendance(db: Session = Depends(get_db)):
    return db.query(Attendance).all()


@router.post("/")
async def create_attendance(attendance_data: dict, db: Session = Depends(get_db)):
    db_attendance = Attendance(**attendance_data)
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance


@router.get("/{attendance_id}")
async def get_attendance(attendance_id: int, db: Session = Depends(get_db)):
    return db.query(Attendance).filter(Attendance.id == attendance_id).first()


@router.delete("/{attendance_id}")
async def delete_attendance(attendance_id: int, db: Session = Depends(get_db)):
    db_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if db_attendance:
        db.delete(db_attendance)
        db.commit()
    return {"deleted": True}
