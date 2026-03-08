"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.base import Base
from app.core.db import get_db_session
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
import uuid


# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


from app.core.dependencies import get_db
app.dependency_overrides[get_db] = override_get_db




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
