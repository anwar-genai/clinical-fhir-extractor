"""FastAPI application for FHIR extraction from clinical documents"""

import logging
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .extractor import FHIRExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Clinical FHIR Extractor",
    description="Extract structured FHIR-compliant medical data from clinical documents",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "version": "0.1.0",
        "endpoints": {
            "/extract-fhir": "POST - Extract FHIR data from clinical documents"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/extract-fhir")
async def extract_fhir(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Extract structured FHIR-compliant medical data from clinical documents
    
    Args:
        file: Uploaded PDF or text file containing clinical data
        
    Returns:
        FHIR Bundle with Patient, Observation, Condition, and MedicationStatement resources
        
    Raises:
        HTTPException: If file format is unsupported or extraction fails
    """
    logger.info(f"Received file: {file.filename} (content_type: {file.content_type})")
    
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    allowed_extensions = [".pdf", ".txt", ".text"]
    file_ext = file.filename.lower().split(".")[-1]
    if f".{file_ext}" not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Get extractor instance
        extractor_instance = get_extractor()
        
        # Extract FHIR data
        fhir_data = extractor_instance.extract_fhir_data(file_content, file.filename)
        
        # Validate the extracted data
        extractor_instance.validate_fhir_bundle(fhir_data)
        
        logger.info(f"Successfully extracted FHIR data from {file.filename}")
        return JSONResponse(content=fhir_data)
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

