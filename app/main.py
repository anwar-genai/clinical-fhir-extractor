"""FastAPI application for FHIR extraction from clinical documents"""

import logging
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from .extractor import FHIRExtractor
from .config import settings
from .database import get_db, init_db
from .auth import get_current_active_user
from .models import User
from .audit import log_audit_event, get_client_ip, get_user_agent
from .routes import auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Clinical FHIR Extractor",
    description="Extract structured FHIR-compliant medical data from clinical documents with authentication",
    version="0.2.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include authentication routes
app.include_router(auth.router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create tables"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

# Initialize extractor (will be created on first request)
extractor = None


def get_extractor() -> FHIRExtractor:
    """Lazy initialization of FHIRExtractor"""
    global extractor
    if extractor is None:
        try:
            extractor = FHIRExtractor()
            logger.info("FHIRExtractor initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize FHIRExtractor: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    return extractor


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Clinical FHIR Extractor API",
        "version": "0.2.0",
        "authentication": "required",
        "endpoints": {
            "/auth/register": "POST - Register new user",
            "/auth/login": "POST - Login and get JWT token",
            "/auth/me": "GET - Get current user info",
            "/extract-fhir": "POST - Extract FHIR data from clinical documents (requires auth)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return {"message": "OK"}


@app.post("/extract-fhir")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def extract_fhir(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Extract structured FHIR-compliant medical data from clinical documents
    
    **Authentication required** - Include JWT token or API key in Authorization header
    
    Args:
        file: Uploaded PDF or text file containing clinical data
        
    Returns:
        FHIR Bundle with Patient, Observation, Condition, and MedicationStatement resources
        
    Raises:
        HTTPException: If file format is unsupported or extraction fails
    """
    logger.info(f"User {current_user.username} - Received file: {file.filename} (content_type: {file.content_type})")
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    allowed_extensions = [".pdf", ".txt", ".text"]
    file_ext = file.filename.lower().split(".")[-1]
    if f".{file_ext}" not in allowed_extensions:
        log_audit_event(
            db, "extract_fhir", "failure",
            user_id=current_user.id,
            resource=file.filename,
            ip_address=get_client_ip(request),
            details={"reason": "invalid_file_type", "extension": file_ext}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            log_audit_event(
                db, "extract_fhir", "failure",
                user_id=current_user.id,
                resource=file.filename,
                ip_address=get_client_ip(request),
                details={"reason": "empty_file"}
            )
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Get extractor instance
        extractor_instance = get_extractor()
        
        # Extract FHIR data
        fhir_data = extractor_instance.extract_fhir_data(file_content, file.filename)
        
        # Validate the extracted data
        extractor_instance.validate_fhir_bundle(fhir_data)
        
        # Log successful extraction
        log_audit_event(
            db, "extract_fhir", "success",
            user_id=current_user.id,
            resource=file.filename,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "file_size": len(file_content),
                "resources_extracted": len(fhir_data.get("entry", []))
            }
        )
        
        logger.info(f"User {current_user.username} - Successfully extracted FHIR data from {file.filename}")
        return JSONResponse(content=fhir_data)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        log_audit_event(
            db, "extract_fhir", "failure",
            user_id=current_user.id,
            resource=file.filename,
            ip_address=get_client_ip(request),
            details={"reason": "validation_error", "error": str(e)}
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        log_audit_event(
            db, "extract_fhir", "failure",
            user_id=current_user.id,
            resource=file.filename,
            ip_address=get_client_ip(request),
            details={"reason": "extraction_error", "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

