import os
import io
import logging
from ..core.ocr_providers import EasyOCRProvider

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        self.image_ocr = EasyOCRProvider()
        
    def extract_text(self, file_path: str, mime_type: str, extension: str) -> str:
        """
        Routes the file to the appropriate extraction engine based on mime type.
        Supports PDF, DOCX, TXT, PNG, JPG.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cannot extract text, file missing: {file_path}")
            
        ext = extension.lower().strip('.')
        
        if ext == 'pdf' or 'pdf' in mime_type:
            return self._extract_pdf(file_path)
            
        elif ext in ['txt', 'csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        elif ext in ['png', 'jpg', 'jpeg'] or 'image' in mime_type:
            logger.info(f"Using OCR for image: {file_path}")
            return self.image_ocr.extract_text(file_path)
            
        elif ext in ['doc', 'docx']:
            return self._extract_docx(file_path)
            
        else:
            raise ValueError(f"Unsupported file format for extraction: {ext}")

    def _extract_pdf(self, file_path: str) -> str:
        """Attempt to extract text using pdfplumber, fallback to PyPDF2, and finally OCR if empty."""
        text = ""
        
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pages_text.append(extracted)
                text = "\n".join(pages_text)
        except Exception as e:
            logger.warning(f"pdfplumber failed for {file_path}: {e}")
            
        if not text.strip():
            logger.info("pdfplumber extracted no text, trying PyPDF2...")
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    pages_text = []
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            pages_text.append(extracted)
                    text = "\n".join(pages_text)
            except Exception as e:
                logger.warning(f"PyPDF2 failed for {file_path}: {e}")

        # If it's a scanned PDF, the text will be empty or very short.
        if len(text.strip()) < 50:
            logger.info("PDF appears to be scanned. OCR is required (not implemented yet for PDF pages here, returning empty or fallback).")
            # In a full implementation, we would convert PDF pages to images using pdf2image and run image_ocr.
            # For Sprint 6, we'll return what we have (or empty).
            
        return text

    def _extract_docx(self, file_path: str) -> str:
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            # Quick pure-python docx text extraction
            text = []
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read('word/document.xml')
                tree = ET.XML(xml_content)
                
                # Namespaces
                WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                PARA = WORD_NAMESPACE + 'p'
                TEXT = WORD_NAMESPACE + 't'
                
                for paragraph in tree.iter(PARA):
                    texts = [node.text for node in paragraph.iter(TEXT) if node.text]
                    if texts:
                        text.append(''.join(texts))
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Failed to extract docx text: {e}")
            return ""
