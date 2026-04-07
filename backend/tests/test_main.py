import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app, Base, get_db

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_user_success():
    """Test successful user creation."""
    response = client.post(
        "/api/users",
        json={"name": "Test User", "phone_number": "1234567890"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    assert data["phone_number"] == "1234567890"
    assert "id" in data

def test_create_user_invalid_data():
    """Test user creation with missing fields (should fail validation)."""
    # Missing phone_number
    response = client.post(
        "/api/users",
        json={"name": "Test User"}
    )
    assert response.status_code == 422

def test_create_user_duplicate_phone():
    """Test user creation with duplicate phone number (should handle DB error)."""
    # Create first user
    client.post(
        "/api/users",
        json={"name": "User 1", "phone_number": "1112223333"}
    )

    # Try to create second user with same phone number
    response = client.post(
        "/api/users",
        json={"name": "User 2", "phone_number": "1112223333"}
    )

    # Currently, backend/main.py handles SQLAlchemyError with a 500 status code
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]
