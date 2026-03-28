"""Shared pytest fixtures for Milestone 1-3 integration tests."""
from __future__ import annotations

from datetime import date
import itertools
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.base import Base
from app.core.dependencies import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.admin import Admin
from app.models.child import Child
from app.models.enrollment import Enrollment
from app.models.group import Group
from app.models.kindergarten import Kindergarten, KindergartenUser
from app.models.parent import Parent, ParentUser
from app.models.pedagogue import Pedagogue
from app.models.user import User, UserRole
import logging


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_sequence = itertools.count(1)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create all tables for each test and tear them down after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """SQLAlchemy session for direct test setup."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def tenant_factory(db_session, client):
    """Create kindergarten users with optional tenant linkage and real login tokens."""

    def _create(
        *,
        email: str | None = None,
        password: str = "Password123!",
        full_name: str = "Kindergarten User",
        verified: bool = True,
        create_kindergarten: bool = True,
        kindergarten_name: str | None = None,
        via_register: bool = False,
    ):
        idx = next(_sequence)
        email_value = email or f"tenant{idx}@test.com"
        full_name_value = full_name if full_name != "Kindergarten User" else f"Kindergarten User {idx}"

        if via_register:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email_value,
                    "password": password,
                    "full_name": full_name_value,
                    "phone": f"+9989000{idx:05d}",
                },
            )
            assert response.status_code == 201, response.text
            user = db_session.query(User).filter(User.phone_or_email == email_value).one()
        else:
            user = User(
                full_name=full_name_value,
                phone_or_email=email_value,
                role=UserRole.KINDERGARTEN,
                password_hash=get_password_hash(password),
                is_active=True,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

        kindergarten = None
        if create_kindergarten:
            kindergarten = Kindergarten(
                kindergarten_id=str(uuid.uuid4()),
                kinder_name=kindergarten_name or f"Kindergarten {idx}",
                region="Tashkent",
                district="Yunusabad",
                address=f"Address {idx}",
                phone=f"+9989111{idx:05d}",
                email=f"kindergarten{idx}@test.com",
                payment_note="Monthly",
                is_verified=verified,
            )
            db_session.add(kindergarten)
            db_session.flush()
            db_session.add(
                KindergartenUser(
                    kindergarten_user_id=str(uuid.uuid4()),
                    user_id=user.user_id,
                    kindergarten_id=kindergarten.kindergarten_id,
                    is_owner=True,
                    position="Director",
                )
            )
            db_session.commit()
            db_session.refresh(kindergarten)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email_value, "password": password},
        )
        assert login_response.status_code == 200, login_response.text
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        return {
            "user": user,
            "kindergarten": kindergarten,
            "email": email_value,
            "password": password,
            "tokens": tokens,
            "headers": headers,
        }

    return _create


@pytest.fixture
def parent_factory(db_session, client):
    """Create a parent account with real parent-login tokens."""

    def _create(*, phone: str | None = None, password: str = "Password123!", email: str | None = None):
        idx = next(_sequence)
        phone_value = phone or f"+9989300{idx:05d}"
        user = User(
            full_name=f"Parent User {idx}",
            phone_or_email=phone_value,
            role=UserRole.PARENT,
            password_hash=get_password_hash(password),
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        parent = Parent(
            parent_id=str(uuid.uuid4()),
            first_name="Parent",
            last_name=f"User{idx}",
            phone=phone_value,
            email=email,
            address=f"Parent Address {idx}",
            birth_date=date(1990, 1, 1),
        )
        db_session.add(parent)
        db_session.flush()

        db_session.add(
            ParentUser(
                parent_user_id=str(uuid.uuid4()),
                user_id=user.user_id,
                parent_id=parent.parent_id,
            )
        )
        db_session.commit()

        login_response = client.post(
            "/api/v1/auth/parent-login",
            json={"phone_number": phone_value, "password": password},
        )
        assert login_response.status_code == 200, login_response.text
        tokens = login_response.json()

        return {
            "user": user,
            "parent": parent,
            "phone": phone_value,
            "password": password,
            "tokens": tokens,
            "headers": {"Authorization": f"Bearer {tokens['access_token']}"},
        }

    return _create


@pytest.fixture
def verified_tenant(tenant_factory):
    """A verified kindergarten tenant with a valid access token."""
    return tenant_factory()


@pytest.fixture
def second_verified_tenant(tenant_factory):
    """A second verified kindergarten tenant for isolation tests."""
    return tenant_factory()


@pytest.fixture
def unverified_tenant(tenant_factory):
    """An unverified kindergarten tenant."""
    return tenant_factory(verified=False)


@pytest.fixture
def parent_account(parent_factory):
    """A parent account and access token."""
    return parent_factory()


@pytest.fixture
def group_payload():
    """Valid group payload."""
    return {
        "name": "Sunflower Group",
        "age_from": 3,
        "age_to": 5,
        "capacity": 20,
        "schedule_from": "08:00:00",
        "schedule_to": "18:00:00",
        "monthly_fee": "500000",
    }


@pytest.fixture
def child_payload():
    """Valid child payload."""
    return {
        "full_name": "Ali Karimov",
        "birth_date": "2021-05-15",
        "gender": "male",
        "parent_phone": "+998901234567",
        "notes": "No allergies",
    }


@pytest.fixture
def staff_payload():
    """Valid staff payload."""
    return {
        "full_name": "Nargiza Xasanova",
        "phone": "+998901999888",
        "role": "teacher",
        "salary": "4500000",
        "hired_at": "2025-09-01",
    }


@pytest.fixture
def create_group(client, group_payload):
    """Create a group for a tenant through the real API."""

    def _create(tenant, **overrides):
        payload = {**group_payload, **overrides}
        response = client.post("/api/v1/groups/", json=payload, headers=tenant["headers"])
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def create_child(client, child_payload):
    """Create a child for a tenant through the real API."""

    def _create(tenant, group_id: str, **overrides):
        payload = {**child_payload, "group_id": group_id, **overrides}
        response = client.post("/api/v1/children/", json=payload, headers=tenant["headers"])
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def create_staff(client, staff_payload):
    """Create a staff member for a tenant through the real API."""

    def _create(tenant, **overrides):
        payload = {**staff_payload, **overrides}
        response = client.post("/api/v1/staff/", json=payload, headers=tenant["headers"])
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def test_admin_user(db_session):
    """Compatibility admin fixture used by the existing test suite."""
    user = Admin(
        first_name="Test",
        last_name="Admin",
        phone="+1234567890",
        email="admin@test.com",
        password_hash=get_password_hash("password123"),
        role="super_admin",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_kindergarten_user(db_session):
    """Compatibility kindergarten user fixture."""
    user = User(
        full_name="Kinder User",
        phone_or_email="kinder@test.com",
        role=UserRole.KINDERGARTEN,
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_parent_user(db_session):
    """Compatibility parent user fixture."""
    user = User(
        full_name="Parent User",
        phone_or_email="parent@test.com",
        role=UserRole.PARENT,
        password_hash=get_password_hash("password123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_token(test_admin_user):
    """Compatibility admin access token fixture."""
    return create_access_token(data={"sub": str(test_admin_user.admin_id), "role": "admin"})


@pytest.fixture
def test_kindergarten_user_token(test_kindergarten_user):
    """Compatibility kindergarten access token fixture."""
    return create_access_token(data={"sub": str(test_kindergarten_user.user_id), "role": test_kindergarten_user.role})


@pytest.fixture
def test_parent_user_token(test_parent_user):
    """Compatibility parent access token fixture."""
    return create_access_token(data={"sub": str(test_parent_user.user_id), "role": test_parent_user.role})


@pytest.fixture
def test_kindergarten(db_session, test_kindergarten_user):
    """Compatibility verified kindergarten fixture."""
    kindergarten = Kindergarten(
        kindergarten_id=str(uuid.uuid4()),
        kinder_name="Test Kindergarten",
        region="Tashkent",
        district="Chilanzar",
        address="Test Address",
        phone="+998901111111",
        email="testkinder@test.com",
        payment_note="Monthly",
        is_verified=True,
    )
    db_session.add(kindergarten)
    db_session.flush()
    db_session.add(
        KindergartenUser(
            kindergarten_user_id=str(uuid.uuid4()),
            user_id=test_kindergarten_user.user_id,
            kindergarten_id=kindergarten.kindergarten_id,
        )
    )
    db_session.commit()
    db_session.refresh(kindergarten)
    return kindergarten


@pytest.fixture
def test_unverified_kindergarten(db_session, test_kindergarten_user):
    """Compatibility unverified kindergarten fixture."""
    kindergarten = Kindergarten(
        kindergarten_id=str(uuid.uuid4()),
        kinder_name="Pending Kindergarten",
        region="Tashkent",
        district="Mirzo-Ulugbek",
        address="Pending Address",
        phone="+998902222222",
        email="pendingkinder@test.com",
        payment_note="Pending",
        is_verified=False,
    )
    db_session.add(kindergarten)
    db_session.flush()
    db_session.add(
        KindergartenUser(
            kindergarten_user_id=str(uuid.uuid4()),
            user_id=test_kindergarten_user.user_id,
            kindergarten_id=kindergarten.kindergarten_id,
        )
    )
    db_session.commit()
    db_session.refresh(kindergarten)
    return kindergarten


@pytest.fixture
def test_pedagogue(db_session, test_kindergarten):
    """Compatibility pedagogue fixture."""
    pedagogue = Pedagogue(
        teacher_id=str(uuid.uuid4()),
        kindergarten_id=test_kindergarten.kindergarten_id,
        full_name="Maria Ivanova",
        phone="+998901234500",
        experience_year=6,
        first_name="Maria",
        last_name="Ivanova",
        email="maria@test.com",
        role="teacher",
    )
    db_session.add(pedagogue)
    db_session.commit()
    db_session.refresh(pedagogue)
    return pedagogue


@pytest.fixture
def test_group(db_session, test_kindergarten, test_pedagogue):
    """Compatibility group fixture."""
    group = Group(
        group_id=str(uuid.uuid4()),
        kindergarten_id=test_kindergarten.kindergarten_id,
        group_name="Sunflower Group",
        teacher_id=test_pedagogue.teacher_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        schedule="Mon-Fri 8-18",
        max_capacity=20,
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def test_child(db_session, test_kindergarten, test_group):
    """Compatibility child fixture."""
    child = Child(
        child_id=str(uuid.uuid4()),
        kindergarten_id=test_kindergarten.kindergarten_id,
        group_id=test_group.group_id,
        full_name="Aziz Rahimov",
        parent_phone="+998901111222",
        first_name="Aziz",
        last_name="Rahimov",
        birth_date=date(2021, 3, 15),
        gender="male",
        address="123 Test Street",
    )
    db_session.add(child)
    db_session.commit()
    db_session.refresh(child)
    return child


@pytest.fixture
def test_parent(db_session, test_parent_user):
    """Compatibility parent fixture."""
    parent = Parent(
        parent_id=str(uuid.uuid4()),
        first_name="John",
        last_name="Doe",
        phone="+5555555555",
        email="parent@test.com",
        address="Parent Address",
        birth_date=date(1990, 1, 1),
    )
    db_session.add(parent)
    db_session.flush()
    db_session.add(
        ParentUser(
            parent_user_id=str(uuid.uuid4()),
            user_id=test_parent_user.user_id,
            parent_id=parent.parent_id,
        )
    )
    db_session.commit()
    db_session.refresh(parent)
    return parent


@pytest.fixture
def test_enrollment(db_session, test_child, test_group):
    """Compatibility enrollment fixture."""
    enrollment = Enrollment(
        enrol_id=str(uuid.uuid4()),
        child_id=test_child.child_id,
        group_id=test_group.group_id,
        enrol_date=date(2026, 3, 1),
        status="active",
        total_fees="500000.00",
        amount_paid="0.00",
        balance="500000.00",
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
def test_parent_child_link(db_session, test_parent, test_child):
    """Compatibility parent-child link fixture."""
    from app.models.child import ParentChildLink

    link = ParentChildLink(
        link_id=str(uuid.uuid4()),
        parent_id=test_parent.parent_id,
        child_id=test_child.child_id,
        note="My child",
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link
