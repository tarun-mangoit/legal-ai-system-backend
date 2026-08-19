import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    @abstractmethod
    async def analyze_document(self, text: str, prompt: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Analyze the document text using the given prompt.
        Returns a tuple of (parsed_json_result, usage_metadata).
        """
        pass



class GeminiProvider(AIProvider):
    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                "gemini-3.5-flash", 
                generation_config={"response_mime_type": "application/json"}
            )
        except ImportError:
            self.model = None
            logger.error("google-generativeai library is not installed")

    async def analyze_document(self, text: str, prompt: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        if not self.model:
            raise RuntimeError("Gemini model is not initialized.")
            
        full_prompt = f"Output valid JSON ONLY.\n\n{prompt.replace('{document_text}', text)}"
        
        try:
            response = await self.model.generate_content_async(full_prompt)
            content = response.text
        except Exception as e:
            logger.error(f"Gemini API failed: {e}")
            raise RuntimeError(f"Gemini API failed: {e}") from e
        
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {content}")
            raise ValueError("Gemini response was not valid JSON") from e
            
        input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
        output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
        total_tokens = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            
        usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "model": "gemini-3.5-flash",
            "provider": "Gemini"
        }
        
        return parsed, usage
