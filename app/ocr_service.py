"""OCR service for extracting text from images and scanned PDFs using Tesseract"""

import logging
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
import io

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class OCRService:
    """Service for OCR text extraction from images and scanned PDFs"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """Initialize OCR service
        
        Args:
            tesseract_path: Path to tesseract executable (auto-detected if None)
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Try to find Tesseract on Windows
            import platform
            if platform.system() == "Windows":
                possible_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    "tesseract"  # If it's in PATH
                ]
                
                for path in possible_paths:
                    try:
                        pytesseract.pytesseract.tesseract_cmd = path
                        # Test if this path works
                        pytesseract.get_tesseract_version()
                        logger.info(f"Found Tesseract at: {path}")
                        break
                    except Exception:
                        continue
                else:
                    # If none of the paths work, try the default
                    pytesseract.pytesseract.tesseract_cmd = "tesseract"
        
        # Verify Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR initialized - version: {version}")
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise ValueError(f"Tesseract OCR not available: {e}")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize image if it's too small (OCR works better on larger images)
        width, height = image.size
        if width < 300 or height < 300:
            # Calculate scale factor to make image at least 300px in smallest dimension
            scale_factor = max(300 / width, 300 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Enhance contrast more aggressively
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)  # Increased from 2.0
        
        # Enhance brightness slightly
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.1)
        
        # Enhance sharpness more aggressively
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.5)  # Increased from 2.0
        
        # Apply Gaussian blur to reduce noise (instead of median filter)
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Apply additional noise reduction
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def extract_text_with_multiple_configs(self, image: Image.Image) -> str:
        """Try multiple OCR configurations and return the best result
        
        Args:
            image: Preprocessed PIL Image
            
        Returns:
            Best extracted text string
        """
        configs = [
            '--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,-/:() ',
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,-/:() ',  # Single word
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,-/:() ',  # Single text line
            '--psm 6',  # Default without whitelist
        ]
        
        results = []
        for config in configs:
            try:
                text = pytesseract.image_to_string(image, lang='eng', config=config).strip()
                if text:
                    results.append(text)
                    logger.debug(f"OCR config '{config}' produced: {text[:50]}...")
            except Exception as e:
                logger.debug(f"OCR config '{config}' failed: {e}")
        
        if not results:
            return ""
        
        # Return the result with the most characters (usually most complete)
        best_result = max(results, key=len)
        logger.info(f"Selected best OCR result: {best_result[:100]}...")
        return best_result
    
    def extract_text_from_image(self, image_path: str, preprocess: bool = True) -> str:
        """Extract text from image file using OCR
        
        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess image for better OCR
            
        Returns:
            Extracted text string
        """
        try:
            # Load image
            image = Image.open(image_path)
            
            # Preprocess if requested
            if preprocess:
                image = self.preprocess_image(image)
            
            # Extract text using multiple OCR configurations for better accuracy
            text = self.extract_text_with_multiple_configs(image)
            
            logger.info(f"OCR extracted {len(text)} characters from {image_path}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            raise ValueError(f"Failed to extract text from image: {e}")
    
    def extract_text_from_image_bytes(self, image_bytes: bytes, preprocess: bool = True) -> str:
        """Extract text from image bytes using OCR
        
        Args:
            image_bytes: Raw image bytes
            preprocess: Whether to preprocess image for better OCR
            
        Returns:
            Extracted text string
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Preprocess if requested
            if preprocess:
                image = self.preprocess_image(image)
            
            # Extract text using multiple OCR configurations for better accuracy
            text = self.extract_text_with_multiple_configs(image)
            
            logger.info(f"OCR extracted {len(text)} characters from image bytes")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed from image bytes: {e}")
            raise ValueError(f"Failed to extract text from image bytes: {e}")
    
    def extract_text_from_scanned_pdf(self, pdf_path: str, dpi: int = 300) -> str:
        """Extract text from scanned PDF by converting pages to images
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion (higher = better quality, slower)
            
        Returns:
            Extracted text from all pages
        """
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(pdf_path)
            all_text = []
            
            for page_num in range(len(pdf_document)):
                # Get page
                page = pdf_document[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Extract text from image
                page_text = self.extract_text_from_image_bytes(img_data, preprocess=True)
                
                if page_text.strip():
                    all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
            
            pdf_document.close()
            
            combined_text = "\n\n".join(all_text)
            logger.info(f"OCR extracted {len(combined_text)} characters from scanned PDF {pdf_path}")
            return combined_text
            
        except Exception as e:
            logger.error(f"OCR extraction failed for scanned PDF {pdf_path}: {e}")
            raise ValueError(f"Failed to extract text from scanned PDF: {e}")
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """Check if PDF is scanned (no extractable text)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF appears to be scanned
        """
        try:
            pdf_document = fitz.open(pdf_path)
            
            # Check first few pages for extractable text
            text_length = 0
            pages_to_check = min(3, len(pdf_document))
            
            for page_num in range(pages_to_check):
                page = pdf_document[page_num]
                text = page.get_text()
                text_length += len(text.strip())
            
            pdf_document.close()
            
            # If very little text, likely scanned
            is_scanned = text_length < 100
            logger.info(f"PDF {pdf_path} appears to be {'scanned' if is_scanned else 'text-based'}")
            return is_scanned
            
        except Exception as e:
            logger.error(f"Failed to check if PDF is scanned: {e}")
            return True  # Assume scanned if check fails
    
    def get_supported_image_formats(self) -> List[str]:
        """Get list of supported image formats
        
        Returns:
            List of supported file extensions
        """
        return ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif']
    
    def get_supported_pdf_formats(self) -> List[str]:
        """Get list of supported PDF formats
        
        Returns:
            List of supported file extensions
        """
        return ['.pdf']
