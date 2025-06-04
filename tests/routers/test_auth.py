# tests/routers/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from routers.auth import UserCreate # For password validation access

# Clear OTPs at the beginning of the test session for auth tests, or per test
from routers.auth import CURRENT_OTPS
@pytest.fixture(autouse=True)
def clear_otps():
    CURRENT_OTPS.clear()

def test_register_user_success(client: TestClient, db_session: Session, mock_send_email):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data
    assert data["is_verified"] is False # Default for new registration

    # Check user in DB (optional, but good for confirmation)
    user_in_db = db_session.query(UserModel).filter(UserModel.email == "test@example.com").first()
    assert user_in_db is not None
    assert user_in_db.username == "testuser"

def test_register_user_email_exists(client: TestClient, create_test_user):
    create_test_user(username="existinguser", email="test@example.com", password="Password123!")
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "email": "test@example.com", "password": "Password456!"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_register_user_username_exists(client: TestClient, create_test_user):
    create_test_user(username="testuser", email="original@example.com", password="Password123!")
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "new@example.com", "password": "Password456!"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_register_user_invalid_password_short(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "short"},
    )
    assert response.status_code == 422 # Pydantic validation for constr
    # Pydantic error response structure might vary, adjust assertion accordingly
    # For FastAPI 0.100+ it's usually a list of errors in response.json()["detail"]
    # Example: assert "ensure this value has at least 8 characters" in response.text

def test_register_user_invalid_password_strength(client: TestClient):
    # Assuming UserCreate.validate_password is called and raises HTTPException for strength
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}, # No special char
    )
    assert response.status_code == 400
    assert "Password must be at least 8 characters long" in response.json()["detail"]


def test_login_success(client: TestClient, create_test_user):
    create_test_user(username="loginuser", email="login@example.com", password="Password123!", is_verified=True)
    response = client.post(
        "/auth/token",
        json={"email": "login@example.com", "password": "Password123!"} # Changed from data to json
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data

def test_login_incorrect_password(client: TestClient, create_test_user):
    create_test_user(username="loginuser", email="login@example.com", password="Password123!", is_verified=True)
    response = client.post(
        "/auth/token",
        json={"email": "login@example.com", "password": "WrongPassword!"} # Changed from data to json
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_login_user_not_verified(client: TestClient, create_test_user, mock_send_email):
    create_test_user(username="unverified", email="unverified@example.com", password="Password123!", is_verified=False)
    response = client.post(
        "/auth/token",
        json={"email": "unverified@example.com", "password": "Password123!"} # Changed from data to json
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Please verify your email first"

def test_login_user_not_found(client: TestClient):
    response = client.post(
        "/auth/token",
        json={"email": "nonexistent@example.com", "password": "Password123!"} # Changed from data to json
    )
    assert response.status_code == 401 # Same error as incorrect password for security
    assert response.json()["detail"] == "Incorrect email or password"

# Placeholder for User model import in test_auth.py if not already there
from models.user import User as UserModel
