# Clinical FHIR Extractor

A secure backend service that extracts structured medical data from PDF, text, and image clinical documents and outputs FHIR R4-compliant JSON using LangChain, FAISS, OpenAI, and OCR.

**Version 0.2.0** - Now with authentication, authorization, audit logging, and OCR support!

## ✨ What's New in v0.2.0

🔐 **Authentication & Authorization**
- JWT-based authentication
- API key support for programmatic access
- Role-based access control (RBAC)
- Comprehensive audit logging

🛡️ **Security Features**
- Rate limiting (10 requests/minute)
- Password hashing with bcrypt
- Token refresh mechanism
- IP address tracking

📊 **Monitoring & Compliance**
- Audit logs for all operations
- User activity tracking
- Admin dashboard endpoints

🔍 **OCR Support** (NEW!)
- Scanned PDF processing with Tesseract OCR
- Image file support (PNG, JPG, TIFF, BMP, GIF)
- Automatic scanned vs text-based PDF detection
- Image preprocessing for better OCR accuracy
- Support for complex medical document layouts

📖 **[Full Authentication Documentation →](AUTHENTICATION.md)**

## 🏗️ Architecture

This application uses:
- **FastAPI** for the REST API
- **LangChain** for document processing and LLM orchestration
- **FAISS** for vector storage and semantic search
- **OpenAI GPT-4** for intelligent medical data extraction
- **PyPDF** for PDF document parsing
- **Tesseract OCR** for scanned document and image processing
- **PIL/Pillow** for image preprocessing
- **PyMuPDF** for advanced PDF handling
- **SQLAlchemy** for database management
- **JWT** for secure authentication

### Workflow

1. **Upload**: Client uploads a PDF, text, or image clinical document
2. **Detect**: System automatically detects file type and processing method
3. **Process**: 
   - Text-based PDFs: Direct text extraction
   - Scanned PDFs: OCR processing with image preprocessing
   - Images: OCR processing with enhancement
   - Text files: Direct processing
4. **Load & Chunk**: Document is loaded and split into manageable chunks
5. **Embed**: Chunks are embedded using OpenAI embeddings
6. **Store**: Embeddings are stored in FAISS vector database
7. **Retrieve**: Relevant chunks are retrieved based on semantic search
8. **Extract**: OpenAI LLM extracts structured FHIR resources
9. **Validate**: Output is validated against FHIR bundle structure
10. **Return**: FHIR-compliant JSON is returned to client

## 📁 Project Structure

```
clinical-fhir-extractor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI routes and endpoints
│   ├── extractor.py         # Core extraction logic with LangChain
│   └── prompts/
│       └── fhir_prompt.txt  # LLM prompt template for FHIR extraction
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # API endpoint tests
│   └── conftest.py          # Pytest fixtures
├── main.py                  # Application entry point
├── pyproject.toml           # Project dependencies and metadata
├── pytest.ini               # Pytest configuration
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Installation

#### Option 1: Using uv (Recommended)

```bash
# Install uv if you haven't already
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

#### Option 2: Using pip

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Copy example configuration
cp .env.example .env
```

**Required Environment Variables:**

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# JWT Secret (IMPORTANT: Change in production!)
JWT_SECRET_KEY=CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING
```

**Generate a secure JWT secret:**

```bash
# Linux/macOS
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Optional Configuration:**

```env
# Database (SQLite by default, use PostgreSQL for production)
DATABASE_URL=sqlite:///./clinical_fhir.db

# Token expiration
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate limiting
RATE_LIMIT_PER_MINUTE=10
```

Note on .env loading:
- If you use `uv`, you can pass an env file directly:

```bash
# Use .env automatically when running with uv
uv run --env-file .env python main.py

# Or with uvicorn
uv run --env-file .env uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🏃 Running the Application

### Development Server

```bash
# Using uv
uv run python main.py

# Or using the app directly
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using standard Python
python main.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## 📡 API Endpoints

### 🔓 Public Endpoints

#### POST /auth/register
Register a new user account.

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "myusername",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

#### POST /auth/login
Login and receive JWT tokens.

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myusername",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 🔐 Protected Endpoints (Authentication Required)

All protected endpoints require an `Authorization: Bearer <token>` header.

#### POST /extract-fhir

Extract FHIR-compliant medical data from a clinical document.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Authorization: `Bearer <access_token>` or `Bearer <api_key>`
- Body: File upload (PDF or TXT)

**Example using curl:**

```bash
# First, get your token from /auth/login
TOKEN="your-access-token-here"

curl -X POST "http://localhost:8000/extract-fhir" \
  -H "Authorization: Bearer $TOKEN" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@clinical_note.txt"
```

**Example using Python:**

```python
import requests

# Login first
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "myusername", "password": "mypassword"}
)
token = login_response.json()["access_token"]

# Extract FHIR data
url = "http://localhost:8000/extract-fhir"
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("clinical_note.txt", "rb")}
response = requests.post(url, headers=headers, files=files)
fhir_data = response.json()
print(fhir_data)
```

#### GET /auth/me
Get current user information.

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

#### POST /auth/api-keys
Create an API key for programmatic access.

```bash
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Automation Script",
    "expires_in_days": 90
  }'
```

### 👑 Admin Endpoints

#### GET /auth/users
List all users (admin only).

#### GET /auth/audit-logs
View audit logs (admin only).

**For complete API documentation, see:**
- **Interactive docs**: http://localhost:8000/docs
- **Authentication guide**: [AUTHENTICATION.md](AUTHENTICATION.md)

**Response:**

```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "patient-1",
        "name": [{"text": "Jane Doe", "family": "Doe", "given": ["Jane"]}],
        "birthDate": "1985-03-15",
        "gender": "female"
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "id": "obs-1",
        "status": "final",
        "code": {"text": "Blood Pressure"},
        "subject": {"reference": "Patient/patient-1"},
        "valueQuantity": {"value": 120, "unit": "mmHg"}
      }
    },
    {
      "resource": {
        "resourceType": "Condition",
        "id": "cond-1",
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {"text": "Hypertension"},
        "subject": {"reference": "Patient/patient-1"}
      }
    },
    {
      "resource": {
        "resourceType": "MedicationStatement",
        "id": "med-1",
        "status": "active",
        "medicationCodeableConcept": {"text": "Lisinopril 10mg"},
        "subject": {"reference": "Patient/patient-1"},
        "dosage": [{"text": "10mg daily"}]
      }
    }
  ]
}
```

### GET /

Returns API information and available endpoints.

### GET /health

Health check endpoint.

## 🧪 Testing

Run the test suite:

```bash
# Using uv
uv run pytest

# Using pytest directly (in virtual environment)
pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_api.py

# Run tests with verbose output
uv run pytest -v
```

**Note:** Integration tests that require OpenAI API calls will be skipped if `OPENAI_API_KEY` is not set.

## 📝 Example Clinical Document

Create a file named `example_note.txt`:

```text
Clinical Assessment

Patient: John Smith (Example)
Date of Birth: 1980-06-15
Gender: Male

Chief Complaint: Follow-up for hypertension

Vital Signs:
- Blood Pressure: 138/88 mmHg
- Heart Rate: 75 bpm
- Temperature: 98.4°F
- Weight: 82 kg

Assessment:
1. Essential Hypertension
2. Hyperlipidemia

Current Medications:
1. Lisinopril 20mg once daily
2. Atorvastatin 40mg at bedtime

Plan:
- Continue current medications
- Recheck BP in 2 weeks
- Order lipid panel
```

Test the extraction:

```bash
curl -X POST "http://localhost:8000/extract-fhir" \
  -F "file=@example_note.txt" \
  -o fhir_output.json
```

## 🔧 Configuration

### LLM Model

By default, the application uses `gpt-4o-mini`. To change the model, edit `app/extractor.py`:

```python
self.llm = ChatOpenAI(
    model="gpt-4o",  # Change to your preferred model
    temperature=0,
    openai_api_key=self.api_key
)
```

### Vector Store Settings

Adjust retrieval settings in `app/extractor.py`:

```python
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}  # Number of chunks to retrieve
)
```

### Chunking Parameters

Modify text splitting in `app/extractor.py`:

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Adjust chunk size
    chunk_overlap=200,    # Adjust overlap
    length_function=len,
)
```

## 🛠️ Development

### Code Style

This project follows PEP 8 conventions. Format code using:

```bash
# Install formatters
uv pip install black isort

# Format code
black .
isort .
```

### Adding New FHIR Resources

To extract additional FHIR resources, update `app/prompts/fhir_prompt.txt` with the resource structure and ensure the LLM prompt includes instructions for the new resource type.

## 🐳 Docker Support (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t clinical-fhir-extractor .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key clinical-fhir-extractor
```

## ⚠️ Important Notes

### PHI and HIPAA Compliance

**WARNING**: This is a proof-of-concept application and is **NOT** HIPAA-compliant. Do not use with real Protected Health Information (PHI) without proper security measures:

- Implement proper authentication and authorization
- Use encrypted storage and transmission
- Maintain audit logs
- Ensure proper data retention and deletion policies
- Conduct security audits
- Sign Business Associate Agreements (BAA) with cloud providers

### OpenAI API Considerations

- OpenAI's API is **not** HIPAA-compliant by default
- Data sent to OpenAI API may be used for model training (opt-out available)
- Consider using Azure OpenAI Service for enterprise/healthcare use cases
- Monitor API costs and implement rate limiting for production use

## 🔍 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Run from project root or install with `pip install -e .`

**Issue**: `OpenAI API key is required`
- **Solution**: Set `OPENAI_API_KEY` environment variable

**Issue**: `FAISS import error`
- **Solution**: Install `faiss-cpu` with `pip install faiss-cpu`

**Issue**: PDF parsing fails
- **Solution**: Ensure PDF is not password-protected or corrupted

## 📚 Additional Resources

- [FHIR R4 Documentation](https://www.hl7.org/fhir/)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

## 📄 License

MIT License - Feel free to use this for your projects.

## 🤝 Contributing

This is a proof-of-concept project. Feel free to fork and adapt for your needs.

## 📞 Support

For issues or questions, please open an issue on the GitHub repository.

---

**Built with ❤️ using LangChain, FastAPI, and OpenAI**

