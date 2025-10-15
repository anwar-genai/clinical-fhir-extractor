"""Tests for the Clinical FHIR Extractor API"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole
from app.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
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


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Create test database tables before each test"""
    Base.metadata.create_all(bind=engine)
    
    # Create a test user for authenticated endpoints
    db = TestingSessionLocal()
    user = User(
        email="apitest@example.com",
        username="apitest",
        hashed_password=get_password_hash("testpass123"),
        role=UserRole.USER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_token():
    """Get authentication token for testing"""
    response = client.post("/auth/login", json={
        "username": "apitest",
        "password": "testpass123"
    })
    return response.json()["access_token"]


def test_root_endpoint():
    """Test the root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_extract_fhir_no_auth():
    """Test extract-fhir endpoint without authentication"""
    files = {"file": ("test.txt", BytesIO(b"test content"), "text/plain")}
    response = client.post("/extract-fhir", files=files)
    assert response.status_code == 403  # Forbidden (no auth)


def test_extract_fhir_no_file(auth_token):
    """Test extract-fhir endpoint without file upload"""
    response = client.post(
        "/extract-fhir",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422  # Unprocessable Entity (missing file)


def test_extract_fhir_invalid_extension(auth_token):
    """Test extract-fhir endpoint with invalid file extension"""
    files = {"file": ("test.docx", BytesIO(b"test content"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post(
        "/extract-fhir",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_extract_fhir_empty_file(auth_token):
    """Test extract-fhir endpoint with empty file"""
    files = {"file": ("empty.txt", BytesIO(b""), "text/plain")}
    response = client.post(
        "/extract-fhir",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.skipif(
    "OPENAI_API_KEY" not in __import__("os").environ,
    reason="OpenAI API key not set - skipping integration test"
)
def test_extract_fhir_with_sample_text(auth_token):
    """Test extract-fhir endpoint with sample clinical text (requires OPENAI_API_KEY)"""
    # Sample clinical document (non-PHI example)
    sample_text = """
    Clinical Note
    
    Patient: Jane Doe (Example Patient)
    DOB: 1985-03-15
    Gender: Female
    
    Chief Complaint: Annual wellness visit
    
    Vital Signs:
    - Blood Pressure: 120/80 mmHg
    - Heart Rate: 72 bpm
    - Temperature: 98.6°F
    - Weight: 65 kg
    
    Assessment:
    1. Hypertension, controlled
    2. Type 2 Diabetes Mellitus
    
    Current Medications:
    1. Lisinopril 10mg daily
    2. Metformin 500mg twice daily
    
    Plan:
    - Continue current medications
    - Follow-up in 3 months
    """
    
    files = {"file": ("clinical_note.txt", BytesIO(sample_text.encode()), "text/plain")}
    response = client.post(
        "/extract-fhir",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Should succeed if API key is valid
    assert response.status_code == 200
    data = response.json()
    
    # Validate FHIR Bundle structure
    assert data["resourceType"] == "Bundle"
    assert "entry" in data
    assert isinstance(data["entry"], list)
    assert len(data["entry"]) > 0
    
    # Check for expected resource types
    resource_types = [entry["resource"]["resourceType"] for entry in data["entry"]]
    assert "Patient" in resource_types, "Should contain Patient resource"


@pytest.mark.skipif(
    "OPENAI_API_KEY" not in __import__("os").environ,
    reason="OpenAI API key not set - skipping integration test"
)
def test_fhir_bundle_validation(auth_token):
    """Test that extracted FHIR data contains required fields"""
    sample_text = """
    Patient Information
    Name: John Smith
    DOB: 1990-01-01
    Gender: Male
    
    Vital Signs:
    Temperature: 98.6°F
    Blood Pressure: 118/76 mmHg
    
    Diagnosis: Essential Hypertension
    
    Medications: Amlodipine 5mg once daily
    """
    
    files = {"file": ("patient_info.txt", BytesIO(sample_text.encode()), "text/plain")}
    response = client.post(
        "/extract-fhir",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Verify bundle structure
        assert data.get("type") == "collection"
        assert "entry" in data
        
        # Each entry should have a resource with resourceType
        for entry in data["entry"]:
            assert "resource" in entry
            assert "resourceType" in entry["resource"]
            assert "id" in entry["resource"]

