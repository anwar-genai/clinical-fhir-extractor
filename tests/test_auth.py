"""Tests for authentication and authorization"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole
from app.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.USER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def admin_user(test_db):
    """Create an admin user"""
    db = TestingSessionLocal()
    user = User(
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def test_register_user(test_db):
    """Test user registration"""
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "password123"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


def test_register_duplicate_username(test_user):
    """Test registration with duplicate username"""
    response = client.post("/auth/register", json={
        "email": "another@example.com",
        "username": "testuser",  # Already exists
        "password": "password123"
    })
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(test_user):
    """Test successful login"""
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(test_user):
    """Test login with wrong password"""
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401


def test_login_nonexistent_user(test_db):
    """Test login with non-existent user"""
    response = client.post("/auth/login", json={
        "username": "doesnotexist",
        "password": "password123"
    })
    
    assert response.status_code == 401


def test_get_current_user(test_user):
    """Test getting current user info"""
    # Login first
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_get_current_user_no_auth(test_db):
    """Test getting current user without authentication"""
    response = client.get("/auth/me")
    assert response.status_code == 403  # Forbidden (no auth header)


def test_update_profile(test_user):
    """Test updating user profile"""
    # Login first
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Update profile
    response = client.put(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Updated Name"}
    )
    
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_create_api_key(test_user):
    """Test creating API key"""
    # Login first
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Create API key
    response = client.post(
        "/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test API Key", "expires_in_days": 30}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["name"] == "Test API Key"


def test_list_api_keys(test_user):
    """Test listing API keys"""
    # Login first
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Create an API key
    client.post(
        "/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test API Key"}
    )
    
    # List API keys
    response = client.get(
        "/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test API Key"
    assert "key" not in data[0]  # Key should not be returned in list


def test_admin_list_users(admin_user):
    """Test admin can list all users"""
    # Login as admin
    login_response = client.post("/auth/login", json={
        "username": "admin",
        "password": "adminpass123"
    })
    token = login_response.json()["access_token"]
    
    # List users
    response = client.get(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_non_admin_cannot_list_users(test_user):
    """Test non-admin cannot list all users"""
    # Login as regular user
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["access_token"]
    
    # Try to list users
    response = client.get(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403  # Forbidden


def test_refresh_token(test_user):
    """Test refreshing access token"""
    # Login first
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = client.post("/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

