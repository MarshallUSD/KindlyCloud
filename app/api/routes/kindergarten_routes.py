"""Kindergarten routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_user, get_current_kindergarten_user
from app.schemas.kindergarten import KindergartenCreateRequest, KindergartenUpdateRequest, KindergartenResponse
from app.schemas.group import GroupCreateRequest, GroupUpdateRequest, GroupResponse
from app.schemas.child import ChildCreateRequest, ChildUpdateRequest, ChildResponse
from app.schemas.enrollment import EnrollmentCreateRequest, EnrollmentResponse
from app.schemas.attendance import AttendanceCreateRequest, AttendanceResponse
from app.schemas.menu import MenuCreateRequest, MenuResponse
from app.schemas.base import PaginatedResponse
from app.services.kindergarten import KindergartenService
from app.services.group import GroupService
from app.services.child import ChildService
from app.services.enrollment import EnrollmentService
from app.services.menu import MenuService
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.repositories.attendance import AttendanceRepository
import uuid
from datetime import date

router = APIRouter()


@router.post("/", response_model=KindergartenResponse, status_code=status.HTTP_201_CREATED)
def create_kindergarten(
    request: KindergartenCreateRequest,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create kindergarten profile."""
    try:
        service = KindergartenService(db)
        kinder = service.create_kindergarten(
            current_user, request.kinder_name, request.region, request.district,
            request.address, request.phone, request.email, request.payment_note
        )
        return kinder
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/me", response_model=KindergartenResponse)
def get_my_kindergarten(
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Get own kindergarten."""
    try:
        service = KindergartenService(db)
        kinder = service.get_my_kindergarten(current_user)
        return kinder
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    request: GroupCreateRequest,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create a group."""
    try:
        service = GroupService(db)
        group = service.create_group(
            current_user, request.group_name, request.teacher_ids,
            request.start_date, request.end_date, request.schedule, request.max_capacity,
            request.age_from, request.age_to, request.room_number, request.monthly_fee,
            request.active_time_start, request.active_time_end
        )
        return group
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/groups", response_model=PaginatedResponse[GroupResponse])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """List groups."""
    try:
        service = GroupService(db)
        items, total = service.list_groups_for_kindergarten(current_user, skip, limit)
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/children", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    request: ChildCreateRequest,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create child record."""
    try:
        service = ChildService(db)
        child = service.create_child(
            request.first_name, request.last_name, request.birth_date,
            request.gender, request.address
        )
        return child
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    request: EnrollmentCreateRequest,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create enrollment."""
    try:
        service = EnrollmentService(db)
        enrollment = service.create_enrollment(
            current_user, request.child_id, request.group_id,
            request.enrol_date, request.total_fees
        )
        return enrollment
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(
    request: AttendanceCreateRequest,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Mark attendance."""
    try:
        from app.models.attendance import Attendance
        attendance_id = str(uuid.uuid4())
        
        # Get enrollment to extract child_id
        from app.repositories.enrollment import EnrollmentRepository
        enrol_repo = EnrollmentRepository(db)
        enrollment = enrol_repo.get_by_id(request.enrol_id)
        if not enrollment:
            raise ValueError("Enrollment not found")
        
        attendance = Attendance(
            attendance_id=attendance_id,
            enrol_id=request.enrol_id,
            child_id=enrollment.child_id,
            attend_date=request.attend_date,
            status=request.status,
            notes=request.notes
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/menus", response_model=MenuResponse,status_code=status.HTTP_201_CREATED)
def create_menu(
    request: MenuCreateRequest,
    current_user: User = Depends(get_current_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create menu."""
    try:
        service = MenuService(db)
        menu = service.create_menu(current_user, request.menu_date, 
                                   [item.dict() for item in request.items],
                                   request.group_ids)
        return menu
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
