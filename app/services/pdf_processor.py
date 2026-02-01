"""
PDF Processor Service
Handles PDF text extraction with OCR support for scanned documents
"""
import io
from typing import Optional
import PyPDF2
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from app.core.config import settings
from app.core.logging import app_logger


class PDFProcessor:
    """Process PDF files and extract text"""
    
    def __init__(self):
        self.ocr_languages = settings.ocr_languages
        self.enable_ocr = settings.enable_ocr
    
    async def extract_text(self, pdf_data: bytes, source_url: str) -> str:
        """
        Extract text from PDF
        
        Args:
            pdf_data: PDF file as bytes
            source_url: Source URL for logging
            
        Returns:
            Extracted text content
        """
        try:
            # First, try to extract text directly
            text = self._extract_text_pypdf2(pdf_data)
            
            # If no text found or very little text, try pdfplumber
            if not text or len(text.strip()) < 100:
                text = self._extract_text_pdfplumber(pdf_data)
            
            # If still no text and OCR is enabled, use OCR
            if (not text or len(text.strip()) < 100) and self.enable_ocr:
                app_logger.info(f"Using OCR for {source_url}")
                text = await self._extract_text_ocr(pdf_data)
            
            return text.strip()
        
        except Exception as e:
            app_logger.error(f"Error extracting text from PDF {source_url}: {e}")
            return ""
    
    def _extract_text_pypdf2(self, pdf_data: bytes) -> str:
        """Extract text using PyPDF2"""
        try:
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            max_pages = min(len(pdf_reader.pages), settings.pdf_max_pages)
            
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return '\n\n'.join(text_parts)
        
        except Exception as e:
            app_logger.debug(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def _extract_text_pdfplumber(self, pdf_data: bytes) -> str:
        """Extract text using pdfplumber (better for complex layouts)"""
        try:
            pdf_file = io.BytesIO(pdf_data)
            text_parts = []
            
            with pdfplumber.open(pdf_file) as pdf:
                max_pages = min(len(pdf.pages), settings.pdf_max_pages)
                
                for page_num in range(max_pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return '\n\n'.join(text_parts)
        
        except Exception as e:
            app_logger.debug(f"pdfplumber extraction failed: {e}")
            return ""
    
    async def _extract_text_ocr(self, pdf_data: bytes) -> str:
        """Extract text using OCR (for scanned PDFs)"""
        try:
            # Convert PDF to images
            images = convert_from_bytes(
                pdf_data,
                dpi=200,  # Good balance between quality and speed
                fmt='jpeg'
            )
            
            text_parts = []
            max_pages = min(len(images), settings.pdf_max_pages)
            
            for i, image in enumerate(images[:max_pages]):
                # Perform OCR
                text = pytesseract.image_to_string(
                    image,
                    lang=self.ocr_languages
                )
                
                if text.strip():
                    text_parts.append(f"[Page {i+1}]\n{text}")
                
                app_logger.debug(f"OCR processed page {i+1}/{max_pages}")
            
            return '\n\n'.join(text_parts)
        
        except Exception as e:
            app_logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def extract_text_by_page(self, pdf_data: bytes) -> dict:
        """
        Extract text page by page (useful for citations)
        
        Returns:
            Dictionary with page numbers as keys and text as values
        """
        try:
            pdf_file = io.BytesIO(pdf_data)
            pages_text = {}
            
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        pages_text[page_num] = text
            
            return pages_text
        
        except Exception as e:
            app_logger.error(f"Error extracting text by page: {e}")
            return {}
