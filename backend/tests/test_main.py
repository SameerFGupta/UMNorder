import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from backend.main import app, get_db, Base, User, Preset

# Setup an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_client():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables in the test database for each test
    Base.metadata.create_all(bind=engine)

    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Drop tables after test finishes
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


# --- Tests ---

def test_read_main(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_create_user(test_client):
    response = test_client.post(
        "/api/users",
        json={"name": "Test User", "phone_number": "1234567890"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    assert data["phone_number"] == "1234567890"
    assert "id" in data

def test_get_users(test_client):
    # First create a user
    test_client.post(
        "/api/users",
        json={"name": "Test User", "phone_number": "1234567890"},
    )

    response = test_client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Test User"
    assert data[0]["phone_number"] == "1234567890"

def test_create_preset(test_client):
    # First, create a user
    user_response = test_client.post(
        "/api/users",
        json={"name": "Preset User", "phone_number": "0987654321"},
    )
    user_id = user_response.json()["id"]

    # Now create a preset for this user
    preset_data = {
        "user_id": user_id,
        "preset_name": "Test Preset",
        "items": [
            {"name": "Hamburger", "modifiers": ["Bun", "Cheese"]}
        ],
        "location_name": "Test Location"
    }
    response = test_client.post("/api/presets", json=preset_data)
    assert response.status_code == 200
    data = response.json()
    assert data["preset_name"] == "Test Preset"
    assert data["location_name"] == "Test Location"
    assert data["user_id"] == user_id
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Hamburger"
    assert data["items"][0]["modifiers"] == ["Bun", "Cheese"]
    assert "id" in data

def test_get_presets(test_client):
    # Create user and preset
    user_response = test_client.post(
        "/api/users",
        json={"name": "Preset User", "phone_number": "0987654321"},
    )
    user_id = user_response.json()["id"]
    test_client.post("/api/presets", json={
        "user_id": user_id,
        "preset_name": "Test Preset",
        "items": []
    })

    response = test_client.get("/api/presets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["preset_name"] == "Test Preset"

def test_get_preset_by_id(test_client):
    # Create user and preset
    user_response = test_client.post(
        "/api/users",
        json={"name": "Preset User", "phone_number": "0987654321"},
    )
    user_id = user_response.json()["id"]
    preset_response = test_client.post("/api/presets", json={
        "user_id": user_id,
        "preset_name": "Test Preset",
        "items": []
    })
    preset_id = preset_response.json()["id"]

    # Get specific preset
    response = test_client.get(f"/api/presets/{preset_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == preset_id
    assert data["preset_name"] == "Test Preset"

def test_delete_preset(test_client):
    # Create user and preset
    user_response = test_client.post(
        "/api/users",
        json={"name": "Preset User", "phone_number": "0987654321"},
    )
    user_id = user_response.json()["id"]
    preset_response = test_client.post("/api/presets", json={
        "user_id": user_id,
        "preset_name": "Test Preset",
        "items": []
    })
    preset_id = preset_response.json()["id"]

    # Delete it
    response = test_client.delete(f"/api/presets/{preset_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Preset deleted successfully"}

    # Verify it's gone
    get_response = test_client.get(f"/api/presets/{preset_id}")
    assert get_response.status_code == 404

@patch("backend.main.run_order_automation")
def test_order_cooldown(mock_run_order, test_client):
    # Mock the automation function
    mock_run_order.return_value = {"success": True, "message": "Order placed successfully!"}

    # Create user and preset
    user_res = test_client.post("/api/users", json={"name": "Order Test", "phone_number": "9998887777"})
    user_id = user_res.json()["id"]

    preset_res = test_client.post("/api/presets", json={
        "user_id": user_id,
        "preset_name": "Order Preset",
        "items": [{"name": "Fries", "modifiers": []}]
    })
    preset_id = preset_res.json()["id"]

    # Place order
    order_res = test_client.post("/api/order", json={"preset_id": preset_id})
    assert order_res.status_code == 200
    assert order_res.json()["success"] == True

    # Place order again to trigger cooldown
    order_res2 = test_client.post("/api/order", json={"preset_id": preset_id})
    assert order_res2.status_code == 200
    assert order_res2.json()["success"] == False
    assert "Cooldown active" in order_res2.json()["message"]
