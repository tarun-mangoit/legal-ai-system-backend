import os
import uuid
import logging
from ..core.ai_providers import GeminiProvider
from ..repositories.processing_repositories import AIRepository
from ..models.ai_summary import ProcessingStatus
from app.services.notification_events import notification_events
from app.models.case import Case

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, repository: AIRepository):
        self.repository = repository
        self.ai_provider = GeminiProvider()
        self._prompt_template = None
        self._prompt_version = "v1"

    @property
    def prompt_template(self) -> str:
        if self._prompt_template is None:
            prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'legal_analysis.txt')
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self._prompt_template = f.read()
            except Exception as e:
                logger.error(f"Failed to load prompt: {e}")
                self._prompt_template = "Extract JSON: {document_text}"
        return self._prompt_template

    async def analyze(self, case_id: uuid.UUID, document_id: uuid.UUID, text: str) -> dict:
        """
        Analyzes the given text using the AI provider and saves the summary and usage log.
        Raises ValueError if parsing fails.
        """
        prompt = self.prompt_template
        
        # Limit text length to prevent blowing up context windows unnecessarily
        # 100k chars is approx 25k tokens, safe for GPT-4-turbo
        max_chars = 100000 
        if len(text) > max_chars:
            text = text[:max_chars]
            
        try:
            parsed_json, usage = await self.ai_provider.analyze_document(text, prompt)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise
            
        # Log Usage
        usage_log_data = {
            "document_id": document_id,
            "provider": usage["provider"],
            "model": usage["model"],
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "cost": 0.0, # Calculate if pricing is known
            "processing_time": 0.0 # Could calculate based on start/end time
        }
        await self.repository.log_usage(usage_log_data)
        
        # Save Summary
        summary_data = {
            "case_id": case_id,
            "document_id": document_id,
            "provider": usage["provider"],
            "model": usage["model"],
            "prompt_version": self._prompt_version,
            "input_tokens": usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "total_tokens": usage["total_tokens"],
            
            "case_details": parsed_json.get("case_details", {}),
            "background": parsed_json.get("background"),
            "plaintiff_claims": parsed_json.get("plaintiff_claims", []),
            "defendant_position": parsed_json.get("defendant_position", []),
            
            "important_facts": parsed_json.get("important_facts", []),
            "timeline": parsed_json.get("timeline", []),
            "legal_issues": parsed_json.get("legal_issues", []),
            
            "reliefs_sought": parsed_json.get("reliefs_sought", []),
            "supporting_documents": parsed_json.get("supporting_documents", []),
            
            "risk_assessment": parsed_json.get("risk_assessment", {}),
            "overall_summary": parsed_json.get("overall_summary"),
            
            "raw_response": parsed_json,
            "status": ProcessingStatus.COMPLETED.value
        }
        
        summary = await self.repository.save_summary(summary_data)
        
        # Trigger notification
        try:
            from sqlalchemy import select
            result = await self.repository.session.execute(select(Case).where(Case.id == case_id))
            case_obj = result.scalars().first()
            if case_obj:
                # Notify both client and advocate if they exist
                for uid in [case_obj.client_id, case_obj.advocate_id]:
                    if uid:
                        await notification_events.handle_ai_processing_completed(
                            db=self.repository.session,
                            user_id=str(uid),
                            case_id=str(case_id),
                            case_number=case_obj.case_number
                        )
        except Exception as e:
            logger.error(f"Failed to trigger AI notification: {e}")
            
        return summary
