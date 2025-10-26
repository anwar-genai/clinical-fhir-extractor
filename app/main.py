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
import json

from .extractor import FHIRExtractor
from .config import settings
from .database import get_db, init_db
from .auth import get_current_active_user
from .models import User
from .audit import log_audit_event, get_client_ip, get_user_agent
from .routes import auth
from .routes import extractions as extractions_routes

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

# Include routes
app.include_router(auth.router)
app.include_router(extractions_routes.router)

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
        "features": {
            "text_extraction": "PDF and text files",
            "ocr_extraction": "Scanned PDFs and images (PNG, JPG, TIFF, etc.)",
            "fhir_compliance": "FHIR R4-compliant output"
        },
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
        file: Uploaded PDF, text file, or image file containing clinical data
               Supported formats: PDF (.pdf), Text (.txt), Images (.png, .jpg, .jpeg, .tiff, .tif, .bmp, .gif)
               Scanned PDFs and images are processed using OCR
        
    Returns:
        FHIR Bundle with Patient, Observation, Condition, and MedicationStatement resources
        
    Raises:
        HTTPException: If file format is unsupported or extraction fails
    """
    logger.info(f"User {current_user.username} - Received file: {file.filename} (content_type: {file.content_type})")
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Get supported formats from OCR service if available
    from .extractor import FHIRExtractor
    extractor_instance = get_extractor()
    
    # Define supported formats
    image_formats = ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif']
    pdf_formats = ['.pdf']
    text_formats = ['.txt', '.text']
    allowed_extensions = pdf_formats + text_formats
    
    # Add image formats if OCR is available
    if extractor_instance.ocr_service:
        allowed_extensions.extend(image_formats)
        logger.info(f"OCR service available - image formats added. Allowed: {allowed_extensions}")
    else:
        logger.warning("OCR service not available - only PDF and text files allowed")
        logger.warning("Image files will be rejected. Check Tesseract installation and PATH.")
    
    file_ext = file.filename.lower().split(".")[-1]
    logger.info(f"File validation - filename: {file.filename}, extension: {file_ext}, content_type: {file.content_type}")
    
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
        
        # Persist extraction
        from .models import Extraction
        extraction = Extraction(
            user_id=current_user.id,
            filename=file.filename,
            content_type=file.content_type,
            file_size=len(file_content),
            result_json=json.dumps(fhir_data),
        )
        db.add(extraction)
        db.commit()
        db.refresh(extraction)

        # Log successful extraction
        log_audit_event(
            db, "extract_fhir", "success",
            user_id=current_user.id,
            resource=file.filename,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details={
                "file_size": len(file_content),
                "resources_extracted": len(fhir_data.get("entry", [])),
                "extraction_id": extraction.id,
            }
        )
        
        logger.info(f"User {current_user.username} - Successfully extracted FHIR data from {file.filename}")
        # Return both bundle and extraction id
        response_payload = {"extraction_id": extraction.id, "bundle": fhir_data}
        return JSONResponse(content=response_payload)
    
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

