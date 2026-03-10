"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.base import Base
from app.core.db import get_db_session
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
import uuid


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


from app.core.dependencies import get_db
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session for tests."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_admin_user(db_session):
    """Create test admin user."""
    user =User(
        user_id=str(uuid.uuid4()),
        role=UserRole.ADMIN,
        email="admin@test.com",
        phone="+1234567890",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_kindergarten_user(db_session):
    """Create test kindergarten user."""
    user = User(
        user_id=str(uuid.uuid4()),
        role=UserRole.KINDERGARTEN,
        email="kinder@test.com",
        phone="+9876543210",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_parent_user(db_session):
    """Create test parent user."""
    user = User(
        user_id=str(uuid.uuid4()),
        role=UserRole.PARENT,
        email="parent@test.com",
        phone="+5555555555",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_admin_token(test_admin_user):
    """Get auth token for admin user."""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": test_admin_user.user_id})


@pytest.fixture
def test_kindergarten_user_token(test_kindergarten_user):
    """Get auth token for kindergarten user."""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": test_kindergarten_user.user_id})


@pytest.fixture
def test_parent_user_token(test_parent_user):
    """Get auth token for parent user."""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": test_parent_user.user_id})


@pytest.fixture
def test_kindergarten(db_session, test_kindergarten_user):
    """Create test kindergarten."""
    from app.models.kindergarten import Kindergarten, KindergartenUser
    
    kindergarten_id = str(uuid.uuid4())
    kindergarten = Kindergarten(
        kindergarten_id=kindergarten_id,
        kinder_name="Test Kindergarten",
        region="Tashkent",
        district="Chilanzar",
        address="Test Address",
        phone="+998901111111",
        email="testkinder@test.com",
        payment_note="Monthly"
    )
    db_session.add(kindergarten)
    
    kinder_user_id = str(uuid.uuid4())
    kinder_user = KindergartenUser(
        kindergarten_user_id=kinder_user_id,
        user_id=test_kindergarten_user.user_id,
        kindergarten_id=kindergarten_id
    )
    db_session.add(kinder_user)
    db_session.commit()
    db_session.refresh(kindergarten)
    return kindergarten


@pytest.fixture
def test_pedagogue(db_session, test_kindergarten):
    """Create test pedagogue."""
    from app.models.pedagogue import Pedagogue
    from datetime import date
    
    teacher_id = str(uuid.uuid4())
    pedagogue = Pedagogue(
        teacher_id=teacher_id,
        kindergarten_id=test_kindergarten.kindergarten_id,
        first_name="Maria",
        last_name="Ivanova",
        email="maria@test.com",
        hire_date=date(2020, 1, 1)
    )
    db_session.add(pedagogue)
    db_session.commit()
    db_session.refresh(pedagogue)
    return pedagogue


@pytest.fixture
def test_group(db_session, test_kindergarten, test_pedagogue):
    """Create test group."""
    from app.models.group import Group
    from datetime import date
    
    group_id = str(uuid.uuid4())
    group = Group(
        group_id=group_id,
        kindergarten_id=test_kindergarten.kindergarten_id,
        group_name="Sunflower Group",
        teacher_id=test_pedagogue.teacher_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        schedule="Mon-Fri 8-18",
        max_capacity=20
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def test_child(db_session):
    """Create test child."""
    from app.models.child import Child
    from datetime import date
    
    child_id = str(uuid.uuid4())
    child = Child(
        child_id=child_id,
        first_name="Aziz",
        last_name="Rahimov",
        birth_date=date(2021, 3, 15),
        gender="male",
        address="123 Test Street"
    )
    db_session.add(child)
    db_session.commit()
    db_session.refresh(child)
    return child


@pytest.fixture
def test_parent(db_session, test_parent_user):
    """Create test parent profile."""
    from app.models.parent import Parent, ParentUser
    from datetime import date
    
    parent_id = str(uuid.uuid4())
    parent = Parent(
        parent_id=parent_id,
        first_name="John",
        last_name="Doe",
        phone="+5555555555",
        email="parent@test.com",
        address="Parent Address",
        birth_date=date(1990, 1, 1)
    )
    db_session.add(parent)
    
    parent_user_id = str(uuid.uuid4())
    parent_user = ParentUser(
        parent_user_id=parent_user_id,
        user_id=test_parent_user.user_id,
        parent_id=parent_id
    )
    db_session.add(parent_user)
    db_session.commit()
    db_session.refresh(parent)
    return parent


@pytest.fixture
def test_enrollment(db_session, test_child, test_group):
    """Create test enrollment."""
    from app.models.enrollment import Enrollment
    from datetime import date
    from decimal import Decimal
    
    enrol_id = str(uuid.uuid4())
    enrollment = Enrollment(
        enrol_id=enrol_id,
        child_id=test_child.child_id,
        group_id=test_group.group_id,
        enrol_date=date(2026, 3, 1),
        status="active",
        total_fees=Decimal("500000.00"),
        paid_amount=Decimal("0.00"),
        remaining_fees=Decimal("500000.00")
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
def test_parent_child_link(db_session, test_parent, test_child):
    """Create parent-child link."""
    from app.models.child import ParentChildLink
    
    link_id = str(uuid.uuid4())
    link = ParentChildLink(
        link_id=link_id,
        parent_id=test_parent.parent_id,
        child_id=test_child.child_id,
        note="My child"
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link

