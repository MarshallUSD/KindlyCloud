from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_kindergarten_user, get_verified_kindergarten_user
from app.core.exceptions import ApplicationException
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.child import ChildCreateRequest, ChildResponse
from app.schemas.enrollment import EnrollmentCreateRequest, EnrollmentResponse
from app.schemas.group import GroupCreateRequest, GroupResponse
from app.schemas.kindergarten import KindergartenCreateRequest, KindergartenResponse
from app.schemas.attendance import AttendanceCreateRequest, AttendanceResponse
from app.schemas.menu import MenuCreateRequest, MenuResponse
from app.schemas.parent import ParentCreateRequest, ParentResponse
from app.services.auth import AuthService
from app.services.child import ChildService
from app.services.enrollment import EnrollmentService
from app.services.group import GroupService
from app.services.kindergarten import KindergartenService
from app.services.menu import MenuService

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
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create a group."""
    try:
        return GroupService(db).create_group(current_user, request)
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/groups", response_model=PaginatedResponse[GroupResponse])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db)
):
    """List groups."""
    try:
        items, total = GroupService(db).list_groups(current_user, skip, limit)
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
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db)
):
    """Create child record."""
    try:
        return ChildService(db).create_child(current_user, request)
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/parents", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
def create_parent_account(
    request: ParentCreateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
    db: Session = Depends(get_db),
):
    """Create a parent account inside the current kindergarten tenant."""
    try:
        service = AuthService(db)
        parent = service.create_parent_account(
            current_user=current_user,
            first_name=request.first_name,
            last_name=request.last_name,
            phone_number=request.phone,
            password=request.password,
            email=request.email,
            address=request.address,
            birth_date=request.birth_date,
            child_ids=request.child_ids,
        )
        return parent
    except ApplicationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    request: EnrollmentCreateRequest,
    current_user: User = Depends(get_verified_kindergarten_user),
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
    current_user: User = Depends(get_verified_kindergarten_user),
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
    current_user: User = Depends(get_verified_kindergarten_user),
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
