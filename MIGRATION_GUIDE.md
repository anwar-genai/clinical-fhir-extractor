# Migration Guide: v0.1.0 → v0.2.0

This guide helps you migrate from Clinical FHIR Extractor v0.1.0 (without authentication) to v0.2.0 (with authentication).

## Breaking Changes

⚠️ **The `/extract-fhir` endpoint now requires authentication**

All FHIR extraction requests must include an `Authorization` header with either:
- A JWT access token (from `/auth/login`)
- An API key (from `/auth/api-keys`)

## Migration Steps

### 1. Update Dependencies

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file with required configuration:

```bash
cp .env.example .env
```

**Required variables:**

```env
# Your existing OpenAI key
OPENAI_API_KEY=your-openai-api-key-here

# NEW: Generate a secure JWT secret
JWT_SECRET_KEY=your-secure-random-string-at-least-32-characters
```

Generate a secure JWT secret:
```bash
openssl rand -hex 32
```

### 3. Initialize Database

The database will automatically initialize on first run. Start the server:

```bash
uv run python main.py
```

This creates `clinical_fhir.db` with user, api_key, and audit_log tables.

### 4. Create First Admin User

**Option A: Using the admin creation script**

```bash
python scripts/create_admin.py
```

**Option B: Register normally, then promote to admin**

```bash
# 1. Register a user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "securepassword123",
    "full_name": "Admin User"
  }'

# 2. Manually promote to admin (requires database access)
sqlite3 clinical_fhir.db "UPDATE users SET role='admin' WHERE username='admin';"
```

### 5. Update Client Code

#### Before (v0.1.0):

```python
import requests

response = requests.post(
    "http://localhost:8000/extract-fhir",
    files={"file": open("clinical_note.txt", "rb")}
)
fhir_data = response.json()
```

#### After (v0.2.0):

```python
import requests

# 1. Login first
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "myusername", "password": "mypassword"}
)
token = login_response.json()["access_token"]

# 2. Use token in extraction request
response = requests.post(
    "http://localhost:8000/extract-fhir",
    headers={"Authorization": f"Bearer {token}"},
    files={"file": open("clinical_note.txt", "rb")}
)
fhir_data = response.json()
```

### 6. Update Automation Scripts

For automation/scripts, use API keys instead of JWT tokens:

```python
import requests

# One-time: Create API key (requires initial login)
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "myusername", "password": "mypassword"}
)
token = login_response.json()["access_token"]

api_key_response = requests.post(
    "http://localhost:8000/auth/api-keys",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "Automation Script", "expires_in_days": 90}
)
api_key = api_key_response.json()["key"]

# Save this API key securely!
print(f"API Key: {api_key}")

# Use API key in all subsequent requests
response = requests.post(
    "http://localhost:8000/extract-fhir",
    headers={"Authorization": f"Bearer {api_key}"},  # Use API key instead of token
    files={"file": open("clinical_note.txt", "rb")}
)
```

### 7. Update Frontend/Web Applications

Add a login flow to your frontend:

```javascript
// 1. Login and store tokens
async function login(username, password) {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  // Store tokens securely (e.g., in localStorage or secure cookie)
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  return data;
}

// 2. Use token in API calls
async function extractFHIR(file) {
  const token = localStorage.getItem('access_token');
  
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/extract-fhir', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  if (response.status === 401) {
    // Token expired, refresh it
    await refreshToken();
    return extractFHIR(file);  // Retry
  }
  
  return response.json();
}

// 3. Refresh token when it expires
async function refreshToken() {
  const refresh_token = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}
```

## Database Migration

If you have existing data that needs to be preserved:

### SQLite (Development)

No special migration needed - v0.2.0 creates new tables alongside any existing data.

### PostgreSQL (Production)

If migrating to PostgreSQL:

```bash
# Update .env
DATABASE_URL=postgresql://user:password@localhost:5432/clinical_fhir

# Restart application (tables will be created automatically)
uv run python main.py
```

For production migrations with Alembic (optional):

```bash
# Install Alembic
pip install alembic

# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add authentication tables"

# Apply migration
alembic upgrade head
```

## Testing the Migration

### 1. Start the server

```bash
uv run python main.py
```

### 2. Register a test user

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 3. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'
```

### 4. Extract FHIR data

```bash
# Save the token from previous step
TOKEN="your-access-token-here"

curl -X POST "http://localhost:8000/extract-fhir" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@example_clinical_note.txt"
```

### 5. Verify audit logging

```bash
# Create admin user first, then:
ADMIN_TOKEN="admin-token-here"

curl -X GET "http://localhost:8000/auth/audit-logs" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Rollback Plan

If you need to rollback to v0.1.0:

```bash
# 1. Checkout previous version
git checkout v0.1.0

# 2. Reinstall dependencies
uv sync

# 3. Remove database (optional)
rm clinical_fhir.db

# 4. Start server
uv run python main.py
```

## Common Issues

### "Invalid authentication credentials"

- Verify you're including the `Authorization: Bearer <token>` header
- Check that your token hasn't expired (30 minutes for access tokens)
- Try logging in again to get a fresh token

### Database errors on startup

- Delete `clinical_fhir.db` and let it recreate
- Ensure no other process is using the database file
- Check file permissions

### Import errors

- Run `uv sync` or `pip install -e .` to install new dependencies
- Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`

## Need Help?

- 📖 Read the [Authentication Guide](AUTHENTICATION.md)
- 💬 Open an issue on GitHub
- 📧 Contact the development team

---

**Migration completed successfully?** Welcome to v0.2.0! 🎉

