from fastapi.testclient import TestClient
from src.app import app
import os

client = TestClient(app)

os.environ["CUSTOM_API_KEY"] = "1234"


def test_moderation_valid_request():
    """Test the moderation endpoint with valid categories."""
    response = client.post(
        "/moderate",
        json={
            "message_id": "test123",
            "content": "This is a test message.",
            "categories": ["sexual", "violence"],
        },
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "test123"
    assert data["content"] == "This is a test message."
    assert "sexual" in data["category_scores"]
    assert "violence" in data["category_scores"]


def test_moderation_invalid_category():
    """Test the moderation endpoint with an invalid category."""
    response = client.post(
        "/moderate",
        json={
            "message_id": "test123",
            "content": "This is a test message.",
            "categories": ["invalid_category"],
        },
        headers={"Authorization": "Bearer 1234"},
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_authentication_required():
    """Test that authentication is required."""
    response = client.post(
        "/moderate",
        json={
            "message_id": "test123",
            "content": "This is a test message.",
            "categories": ["sexual"],
        },
    )
    assert response.status_code == 403  # Unauthorized
