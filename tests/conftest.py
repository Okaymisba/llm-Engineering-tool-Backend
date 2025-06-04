# tests/conftest.py
import os
import pytest
from typing import Generator, Any
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set environment variables for testing BEFORE importing main app or models
os.environ["SECRET_KEY"] = "testsecretkey"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["OTP_EXPIRY_MINUTES"] = "5"
os.environ["MAX_OTP_ATTEMPTS"] = "3"
# Add other necessary env vars if your app crashes without them during import
# e.g., for database connection if not using a separate test DB config
os.environ["DATABASE_URL"] = "sqlite:///:memory:" # Example if needed by main app logic

from main import app  # Import your FastAPI app
from models import Base, get_db # Import Base for table creation and get_db for overriding
from models.user import User as UserModel # To avoid confusion with User fixture

# --- Database Fixtures ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db_once():
    # Create tables once per session
    Base.metadata.create_all(bind=engine)
    yield
    # Optional: drop tables after session if needed, or let memory DB handle it
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, Any, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

# --- Override get_db dependency ---
def override_get_db() -> Generator[Session, Any, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback() # Ensure changes are rolled back after each test
        connection.close()

app.dependency_overrides[get_db] = override_get_db

# --- API Client Fixture ---
@pytest.fixture(scope="module") # Can be function scope if preferred
def client() -> Generator[TestClient, Any, None]:
    with TestClient(app) as c:
        yield c

# --- Mocking Fixtures ---
@pytest.fixture(scope="function")
def mock_send_email():
    with patch("routers.auth.send_email") as mock:
        mock.return_value = None # Simulate successful email sending by default
        yield mock

# --- Utility Fixtures ---
@pytest.fixture(scope="function")
def create_test_user(db_session: Session):
    def _create_test_user(username, email, password, is_verified=False):
        user = UserModel(
            username=username,
            email=email,
            hashed_password=UserModel.get_password_hash(password),
            is_verified=is_verified
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_test_user

@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, create_test_user, db_session: Session) -> TestClient:
    # Create a verified user first
    test_username = "authtestuser"
    test_email = "authtest@example.com"
    test_password = "Password123!"

    # Ensure user doesn't exist from a previous failed test run if DB is not perfectly clean
    user_in_db = db_session.query(UserModel).filter(UserModel.email == test_email).first()
    if user_in_db:
        db_session.delete(user_in_db)
        db_session.commit()

    user = create_test_user(
        username=test_username,
        email=test_email,
        password=test_password,
        is_verified=True
    )

    # Log in the user to get a token
    login_data = {"email": test_email, "password": test_password}
    response = client.post("/auth/token", json=login_data) # use json for Pydantic model
    assert response.status_code == 200, "Failed to log in test user for authenticated_client"

    token_data = response.json()
    access_token = token_data["access_token"]

    # Set the token for subsequent requests made by this client instance
    client.headers["Authorization"] = f"Bearer {access_token}"
    yield client
    # Clean up: remove the header after the test
    del client.headers["Authorization"]
