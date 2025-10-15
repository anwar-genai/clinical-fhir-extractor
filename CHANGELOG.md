# Changelog

All notable changes to the Clinical FHIR Extractor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-15

### Added
- **Authentication & Authorization System**
  - JWT-based authentication with access and refresh tokens
  - API key support for programmatic access
  - User registration and login endpoints
  - Password hashing with bcrypt
  - Token refresh mechanism
  
- **Role-Based Access Control (RBAC)**
  - Four user roles: USER, RESEARCHER, CLINICIAN, ADMIN
  - Role-based endpoint protection
  - Admin-only endpoints for user management
  
- **Security Features**
  - Rate limiting (10 requests/minute per user)
  - IP address tracking
  - User agent logging
  - Secure password requirements (min 8 characters)
  - Automatic token expiration (30 min for access, 7 days for refresh)
  
- **Audit Logging**
  - Comprehensive audit trail for all operations
  - Track user login, extraction requests, API key operations
  - Store IP addresses, user agents, and action details
  - Admin endpoint to view audit logs
  
- **Database Layer**
  - SQLAlchemy integration
  - User, APIKey, and AuditLog models
  - SQLite default (production-ready with PostgreSQL)
  
- **API Endpoints**
  - `/auth/register` - User registration
  - `/auth/login` - User authentication
  - `/auth/refresh` - Token refresh
  - `/auth/me` - Get current user info
  - `/auth/api-keys` - API key management (create, list, delete)
  - `/auth/users` - List users (admin only)
  - `/auth/audit-logs` - View audit logs (admin only)
  
- **Documentation**
  - Comprehensive AUTHENTICATION.md guide
  - Updated README with authentication examples
  - Python client examples
  - Security best practices
  
- **Testing**
  - Authentication test suite (tests/test_auth.py)
  - Updated API tests with authentication
  - Database fixtures for testing
  
- **Utilities**
  - Admin user creation script (scripts/create_admin.py)
  - Environment configuration with Pydantic Settings
  - `.env.example` template

### Changed
- **Breaking**: `/extract-fhir` endpoint now requires authentication
- Updated FastAPI app version to 0.2.0
- Enhanced error messages with detailed security context
- All FHIR extraction operations now logged for audit

### Security
- All endpoints except registration and login now require authentication
- Passwords are hashed using bcrypt
- JWT tokens signed with configurable secret key
- Rate limiting to prevent abuse
- Comprehensive audit logging for compliance

## [0.1.0] - Initial Release

### Added
- FHIR extraction from PDF and text documents
- LangChain integration for document processing
- FAISS vector store for semantic search
- OpenAI GPT-4 integration
- FastAPI REST API
- Basic validation of FHIR bundles
- Support for Patient, Observation, Condition, and MedicationStatement resources

