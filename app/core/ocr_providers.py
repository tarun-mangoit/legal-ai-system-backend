from abc import ABC, abstractmethod
import os
import io

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text from an image file."""
        pass

class GoogleVisionProvider(OCRProvider):
    def extract_text(self, file_path: str) -> str:
        raise NotImplementedError("Google Vision Provider is not yet implemented.")

class EasyOCRProvider(OCRProvider):
    def __init__(self):
        # Lazy loading to prevent slow startup times if not used
        self._reader = None
        
    @property
    def reader(self):
        if self._reader is None:
            import easyocr
            # Note: For production with large volumes, GPU is recommended.
            self._reader = easyocr.Reader(['en'], gpu=False)
        return self._reader

    def extract_text(self, file_path: str) -> str:
        """
        Extracts text from the given image file path using EasyOCR.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        results = self.reader.readtext(file_path)
        
        # results is a list of tuples: (bbox, text, confidence)
        extracted_text = []
        for (bbox, text, prob) in results:
            extracted_text.append(text)
            
        return "\n".join(extracted_text)
