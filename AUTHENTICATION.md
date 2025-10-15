# Authentication & Authorization Guide

This document describes the authentication and authorization system for the Clinical FHIR Extractor API.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Authentication Methods](#authentication-methods)
- [User Roles](#user-roles)
- [API Endpoints](#api-endpoints)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Clinical FHIR Extractor now requires authentication for all data extraction operations. This ensures:

- **Audit trails** - Track who accessed what and when
- **Access control** - Manage permissions with role-based access control (RBAC)
- **Rate limiting** - Prevent API abuse
- **Compliance** - Meet healthcare security requirements

### Features

✅ JWT-based authentication  
✅ API key support for programmatic access  
✅ Role-based access control (RBAC)  
✅ Comprehensive audit logging  
✅ Rate limiting (10 requests/minute per user)  
✅ Password hashing with bcrypt  
✅ Token refresh mechanism  

## Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and set required variables:

```bash
cp .env.example .env
```

**Important**: Change the `JWT_SECRET_KEY` in production!

```env
JWT_SECRET_KEY=your-secure-random-string-at-least-32-characters
OPENAI_API_KEY=your-openai-api-key
```

Generate a secure key:
```bash
# Linux/macOS
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Start the Server

```bash
uv run python main.py
```

### 3. Register a User

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

### 4. Login and Get Token

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

### 5. Use Token to Extract FHIR Data

```bash
curl -X POST "http://localhost:8000/extract-fhir" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@clinical_note.txt"
```

## Authentication Methods

### Method 1: JWT Tokens (Recommended for Web/Mobile Apps)

1. **Login** to get access and refresh tokens
2. **Use access token** in Authorization header for API requests
3. **Refresh token** when access token expires (30 minutes default)

**Pros:**
- Short-lived access tokens (more secure)
- Automatic expiration
- Token refresh mechanism

**Cons:**
- Requires login flow
- Tokens expire and need refresh

### Method 2: API Keys (Recommended for Scripts/Automation)

1. **Login** to get JWT token
2. **Create API key** using the token
3. **Use API key** directly in Authorization header (no expiration needed)

**Pros:**
- Long-lived credentials
- Simpler for automation
- Can be easily revoked

**Cons:**
- More responsibility to keep secure
- Need to manage key rotation

#### Creating an API Key

```bash
# First, login to get a JWT token
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"myusername","password":"securepassword123"}' \
  | jq -r '.access_token')

# Create an API key
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Automation Script",
    "expires_in_days": 90
  }'
```

Response:
```json
{
  "id": 1,
  "key": "p8JGHxK3N9mQs2vW5yZ...",
  "name": "My Automation Script",
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-04-15T10:30:00Z"
}
```

**⚠️ Important**: The API key is only shown once! Save it securely.

#### Using an API Key

```bash
curl -X POST "http://localhost:8000/extract-fhir" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@clinical_note.txt"
```

## User Roles

The system supports role-based access control (RBAC) with four roles:

| Role | Permissions | Use Case |
|------|-------------|----------|
| **USER** | Extract FHIR data, manage own profile, create API keys | Default role for new users |
| **RESEARCHER** | All USER permissions + (future: batch operations) | Research projects |
| **CLINICIAN** | All RESEARCHER permissions + (future: PHI access) | Clinical staff |
| **ADMIN** | Full access, manage users, view audit logs | System administrators |

### Role Hierarchy

```
ADMIN > CLINICIAN > RESEARCHER > USER
```

## API Endpoints

### Public Endpoints (No Authentication)

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Full Name"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "username",
  "password": "password123"
}
```

### Protected Endpoints (Authentication Required)

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <token>
```

#### Update Profile
```http
PUT /auth/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "New Name",
  "email": "newemail@example.com"
}
```

#### Refresh Access Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

#### Create API Key
```http
POST /auth/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Key Name",
  "expires_in_days": 90
}
```

#### List API Keys
```http
GET /auth/api-keys
Authorization: Bearer <token>
```

#### Delete API Key
```http
DELETE /auth/api-keys/{key_id}
Authorization: Bearer <token>
```

#### Extract FHIR Data (Protected)
```http
POST /extract-fhir
Authorization: Bearer <token_or_api_key>
Content-Type: multipart/form-data

file: <clinical_document.pdf>
```

### Admin-Only Endpoints

#### List All Users
```http
GET /auth/users
Authorization: Bearer <admin_token>
```

#### View Audit Logs
```http
GET /auth/audit-logs?limit=100
Authorization: Bearer <admin_token>
```

## Audit Logging

All security-relevant events are logged to the database:

- User registration
- Login attempts (success/failure)
- FHIR extraction requests
- API key creation/deletion
- Profile updates

### Audit Log Fields

- `user_id` - User who performed the action
- `action` - Type of action (login, extract_fhir, etc.)
- `resource` - Resource affected (filename, user ID, etc.)
- `status` - success or failure
- `ip_address` - Client IP address
- `user_agent` - Client user agent
- `details` - Additional JSON details
- `created_at` - Timestamp

### Viewing Audit Logs (Admin Only)

```bash
curl -X GET "http://localhost:8000/auth/audit-logs?limit=50" \
  -H "Authorization: Bearer <admin_token>"
```

## Security Best Practices

### For Development

1. ✅ Use `.env` file for configuration
2. ✅ Never commit `.env` to version control
3. ✅ Use strong passwords (8+ characters)
4. ✅ Rotate JWT secret regularly

### For Production

1. ✅ **Change JWT_SECRET_KEY** - Use a long random string (32+ chars)
2. ✅ **Use HTTPS** - Always use SSL/TLS in production
3. ✅ **Use PostgreSQL** - Replace SQLite with production database
4. ✅ **Enable CORS properly** - Don't use `["*"]` in production
5. ✅ **Set strong password policy** - Enforce minimum length, complexity
6. ✅ **Monitor audit logs** - Set up alerts for suspicious activity
7. ✅ **Rotate API keys** - Set expiration dates
8. ✅ **Use environment-specific configs** - Different secrets per environment
9. ✅ **Implement rate limiting** - Already enabled (10 req/min)
10. ✅ **Regular security audits** - Review logs and access patterns

### Password Requirements

- Minimum 8 characters (configurable via `PASSWORD_MIN_LENGTH`)
- Store as bcrypt hashes (automatically handled)
- No maximum length enforced

### Token Expiration

- **Access tokens**: 30 minutes (configurable)
- **Refresh tokens**: 7 days (configurable)
- **API keys**: Optional expiration (set during creation)

## Rate Limiting

The API enforces rate limiting to prevent abuse:

- **Default**: 10 requests per minute per user/IP
- **Configurable**: Set `RATE_LIMIT_PER_MINUTE` in `.env`
- **Applies to**: `/extract-fhir` endpoint

When rate limit is exceeded:
```json
{
  "detail": "Rate limit exceeded: 10 per minute"
}
```

## Python Client Example

```python
import requests
import os

class FHIRClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def register(self, email, username, password, full_name=None):
        """Register a new user"""
        response = requests.post(f"{self.base_url}/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": full_name
        })
        response.raise_for_status()
        return response.json()
    
    def login(self, username, password):
        """Login and store token"""
        response = requests.post(f"{self.base_url}/auth/login", json={
            "username": username,
            "password": password
        })
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data
    
    def extract_fhir(self, file_path):
        """Extract FHIR data from a clinical document"""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/extract-fhir",
                headers={"Authorization": f"Bearer {self.token}"},
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()
    
    def create_api_key(self, name, expires_in_days=None):
        """Create an API key for programmatic access"""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        
        response = requests.post(
            f"{self.base_url}/auth/api-keys",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"name": name, "expires_in_days": expires_in_days}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = FHIRClient()

# Login
client.login("myusername", "mypassword")

# Extract FHIR data
fhir_bundle = client.extract_fhir("clinical_note.txt")
print(fhir_bundle)

# Create API key for automation
api_key = client.create_api_key("Automation Script", expires_in_days=90)
print(f"API Key: {api_key['key']}")
```

## Troubleshooting

### "Invalid authentication credentials"

- Check that token is not expired (access tokens expire in 30 min)
- Verify you're using `Bearer` prefix: `Authorization: Bearer <token>`
- Try refreshing your token or logging in again

### "Insufficient permissions"

- Check your user role with `GET /auth/me`
- Some endpoints require admin role
- Contact admin to upgrade your role if needed

### "Rate limit exceeded"

- Wait 1 minute before retrying
- Use API keys instead of tokens for automation (same rate limit applies)
- Contact admin to increase rate limit if needed

### "User not found or inactive"

- Verify username is correct
- Check if account has been deactivated
- Contact administrator

### Token Refresh Fails

- Refresh tokens expire after 7 days
- Login again to get new tokens
- Check that refresh token is correct

## Migration from Previous Version

If upgrading from version 0.1.0 (without authentication):

1. **Update dependencies**: `uv sync` or `pip install -e .`
2. **Run database migrations**: Database will auto-initialize on first run
3. **Create first admin user**: Register via `/auth/register`, then manually promote to admin in database
4. **Update client code**: Add authentication headers to all API calls
5. **Update frontend**: Implement login flow

### Creating First Admin User

```bash
# Register user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","username":"admin","password":"adminpass123"}'

# Manually promote to admin (requires database access)
sqlite3 clinical_fhir.db "UPDATE users SET role='admin' WHERE username='admin';"
```

## Additional Resources

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Need Help?** Open an issue on GitHub or contact the development team.

