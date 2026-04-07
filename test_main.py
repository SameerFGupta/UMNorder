import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app, get_db, Base
from backend.helpers import parse_items_json

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_create_and_get_preset():
    # First create a user
    response = client.post(
        "/api/users",
        json={"name": "Test User", "phone_number": "1234567890"}
    )
    assert response.status_code == 200, response.text
    user_id = response.json()["id"]

    # Create a preset
    response = client.post(
        "/api/presets",
        json={
            "user_id": user_id,
            "preset_name": "Test Preset",
            "items": [{"name": "Burger", "modifiers": ["Cheese"]}],
            "location_name": "Location 1"
        }
    )
    assert response.status_code == 200, response.text
    preset_id = response.json()["id"]

    # Get presets
    response = client.get("/api/presets")
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) >= 1
    assert data[0]["preset_name"] == "Test Preset"

def test_parse_items_json_new_format():
    items = [
        {"name": "Hamburger", "modifiers": ["Bun", "Cheese"]},
        {"name": "Fries", "modifiers": []}
    ]
    items_json = json.dumps(items)
    result = parse_items_json(items_json)

    assert len(result) == 2
    assert result[0]["name"] == "Hamburger"
    assert result[0]["modifiers"] == ["Bun", "Cheese"]
    assert result[1]["name"] == "Fries"
    assert result[1]["modifiers"] == []

def test_parse_items_json_old_format():
    items = ["Hamburger", "Fries"]
    items_json = json.dumps(items)
    result = parse_items_json(items_json)

    assert len(result) == 2
    assert result[0]["name"] == "Hamburger"
    assert result[0]["modifiers"] == []
    assert result[1]["name"] == "Fries"
    assert result[1]["modifiers"] == []

def test_parse_items_json_empty():
    assert parse_items_json("") == []
    assert parse_items_json("[]") == []
    assert parse_items_json(None) == []
