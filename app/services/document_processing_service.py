import uuid
from typing import Optional, Dict, Any
from ..repositories.processing_repositories import OCRRepository, AIRepository
from ..tasks.document_tasks import process_document_pipeline
from ..models.ai_summary import ProcessingStatus
from fastapi import HTTPException
from ..models.user import User

class DocumentProcessingService:
    def __init__(self, ocr_repository: OCRRepository, ai_repository: AIRepository):
        self.ocr_repo = ocr_repository
        self.ai_repo = ai_repository
        
    async def _get_user_role(self, user: User) -> str:
        # Simplification: Assume user object has a role_id which can be mapped to 'admin'
        # In actual implementation, you would look this up from db or JWT claims
        return "admin" if user.role_id else "client"

    async def trigger_processing(self, document_id: uuid.UUID, case_id: uuid.UUID):
        """Initializes jobs and triggers the Celery pipeline."""
        # Ensure jobs exist
        await self.ocr_repo.get_or_create_job(document_id)
        await self.ai_repo.get_or_create_job(document_id)
        
        await self.ocr_repo.update_status(document_id, ProcessingStatus.PENDING, "")
        await self.ai_repo.update_job_status(document_id, ProcessingStatus.PENDING, "")
        
        # Dispatch Celery task
        process_document_pipeline.delay(str(document_id), str(case_id))
        
        return {"message": "Processing started", "document_id": str(document_id)}

    async def get_processing_status(self, document_id: uuid.UUID) -> Dict[str, Any]:
        """Returns the current status of OCR and AI processing."""
        ocr_job = await self.ocr_repo.get_or_create_job(document_id)
        ai_job = await self.ai_repo.get_or_create_job(document_id)
        
        # Determine overall status
        if ocr_job.status == ProcessingStatus.FAILED.value or ai_job.status == ProcessingStatus.FAILED.value:
            overall = ProcessingStatus.FAILED.value
        elif ocr_job.status == ProcessingStatus.PENDING.value and ai_job.status == ProcessingStatus.PENDING.value:
            overall = ProcessingStatus.PENDING.value
        elif ocr_job.status == ProcessingStatus.COMPLETED.value and ai_job.status == ProcessingStatus.COMPLETED.value:
            overall = ProcessingStatus.COMPLETED.value
        else:
            overall = ProcessingStatus.PROCESSING.value
            
        return {
            "document_id": str(document_id),
            "overall_status": overall,
            "ocr_status": ocr_job.status,
            "ai_status": ai_job.status,
            "ocr_error": ocr_job.error_message,
            "ai_error": ai_job.error_message,
            "ai_retries": ai_job.retry_count
        }

    async def get_summary(self, document_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        summary = await self.ai_repo.get_summary_by_document(document_id)
        if summary:
            return {
                "id": str(summary.id),
                "case_id": str(summary.case_id),
                "document_id": str(summary.document_id),
                
                "case_details": summary.case_details,
                "background": summary.background,
                "plaintiff_claims": summary.plaintiff_claims or [],
                "defendant_position": summary.defendant_position or [],
                
                "important_facts": summary.important_facts or [],
                "timeline": summary.timeline or [],
                "legal_issues": summary.legal_issues or [],
                
                "reliefs_sought": summary.reliefs_sought or [],
                "supporting_documents": summary.supporting_documents or [],
                
                "risk_assessment": summary.risk_assessment,
                "overall_summary": summary.overall_summary,
                
                "provider": summary.provider,
                "status": summary.status
            }
        return None

    async def get_all_jobs(self, user: User, skip: int = 0, limit: int = 100) -> list[Dict[str, Any]]:
        role_name = await self._get_user_role(user)
        if role_name not in ["admin", "advocate"]:
            raise HTTPException(status_code=403, detail="Not authorized to view all jobs")
            
        raw_jobs = await self.ai_repo.get_all_jobs(skip, limit)
        jobs = []
        for item in raw_jobs:
            job = item["job"]
            jobs.append({
                "id": job.id,
                "document_id": job.document_id,
                "document_name": item["document_name"],
                "case_id": item["case_id"],
                "job_type": item["type"],
                "status": job.status,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "error_message": job.error_message
            })
        return jobs

    async def get_all_usage(self, user: User, skip: int = 0, limit: int = 100) -> list[Dict[str, Any]]:
        role_name = await self._get_user_role(user)
        if role_name not in ["admin", "advocate"]:
            raise HTTPException(status_code=403, detail="Not authorized to view AI usage")
            
        raw_usage = await self.ai_repo.get_all_usage_logs(skip, limit)
        usage = []
        for log, doc_name, case_id in raw_usage:
            usage.append({
                "id": log.id,
                "document_id": log.document_id,
                "document_name": doc_name,
                "case_id": case_id,
                "provider": log.provider,
                "model": log.model,
                "input_tokens": log.input_tokens,
                "output_tokens": log.output_tokens,
                "cost": log.cost,
                "processing_time": log.processing_time,
                "created_at": log.created_at
            })
        return usage
