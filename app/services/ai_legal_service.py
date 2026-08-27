import os
import json
import google.generativeai as genai
from typing import Type, TypeVar
from pydantic import BaseModel
from app.ai.prompts.document_summary import DOCUMENT_SUMMARY_PROMPT
from app.ai.prompts.case_analysis import CASE_ANALYSIS_PROMPT
from app.ai.prompts.legal_opinion import LEGAL_OPINION_PROMPT
from app.schemas.ai_legal import DocumentSummaryBase, CaseAnalysisBase, LegalOpinionBase
from app.config import settings

T = TypeVar("T", bound=BaseModel)

class AILegalService:
    def __init__(self):
        # Configure Gemini
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "your_gemini_api_key":
            raise ValueError("GEMINI_API_KEY not found or invalid in environment variables")
        genai.configure(api_key=api_key)
        # Use gemini-3.5-flash
        self.model = genai.GenerativeModel('gemini-3.5-flash')

    async def _generate_structured_output(self, prompt: str, schema: Type[T]) -> T:
        # We instruct Gemini to return JSON conforming to the schema
        # In gemini 1.5 pro we can use response_mime_type="application/json"
        
        # Pydantic v2 schema extraction
        schema_json = schema.model_json_schema()
        
        full_prompt = f"""
        {prompt}
        
        IMPORTANT INSTRUCTIONS:
        You must return ONLY a valid JSON object matching this exact JSON Schema:
        {json.dumps(schema_json, indent=2)}
        
        Do not include markdown formatting like ```json in your response. Just the raw JSON object.
        """
        
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2, # Low temperature for factual extraction
            )
        )
        
        try:
            # Parse the text response into our Pydantic model
            json_dict = json.loads(response.text)
            return schema(**json_dict)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response into schema: {e}\nRaw Response: {response.text}")

    async def generate_document_summary(self, document_text: str) -> DocumentSummaryBase:
        prompt = DOCUMENT_SUMMARY_PROMPT.format(document_text=document_text)
        return await self._generate_structured_output(prompt, DocumentSummaryBase)

    async def generate_case_analysis(self, document_summaries: list[dict]) -> CaseAnalysisBase:
        summaries_text = json.dumps(document_summaries, indent=2)
        prompt = CASE_ANALYSIS_PROMPT.format(document_summaries=summaries_text)
        return await self._generate_structured_output(prompt, CaseAnalysisBase)

    async def generate_legal_opinion(self, case_information: dict) -> LegalOpinionBase:
        case_info_text = json.dumps(case_information, indent=2)
        prompt = LEGAL_OPINION_PROMPT.format(case_information=case_info_text)
        return await self._generate_structured_output(prompt, LegalOpinionBase)
