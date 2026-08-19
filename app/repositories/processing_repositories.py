from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
import uuid
from datetime import datetime

from ..models.job_tracking import OCRJob, AIJob, AIUsageLog
from ..models.ai_summary import AISummary, ProcessingStatus

class OCRRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_job(self, document_id: uuid.UUID) -> OCRJob:
        result = await self.session.execute(
            select(OCRJob).where(OCRJob.document_id == document_id)
        )
        job = result.scalars().first()
        
        if not job:
            job = OCRJob(document_id=document_id)
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            
        return job

    async def update_status(self, job_id: uuid.UUID, status: ProcessingStatus, error_message: str = None) -> OCRJob:
        job = await self.session.get(OCRJob, job_id)
        if job:
            job.status = status.value
            if status == ProcessingStatus.PROCESSING:
                job.started_at = datetime.utcnow()
            elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                job.completed_at = datetime.utcnow()
                
            if error_message:
                job.error_message = error_message
                
            await self.session.commit()
            await self.session.refresh(job)
        return job


class AIRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_job(self, document_id: uuid.UUID) -> AIJob:
        result = await self.session.execute(
            select(AIJob).where(AIJob.document_id == document_id)
        )
        job = result.scalars().first()
        
        if not job:
            job = AIJob(document_id=document_id)
            self.session.add(job)
            await self.session.commit()
            await self.session.refresh(job)
            
        return job

    async def update_job_status(self, job_id: uuid.UUID, status: ProcessingStatus, error_message: str = None, increment_retry: bool = False) -> AIJob:
        job = await self.session.get(AIJob, job_id)
        if job:
            job.status = status.value
            if status == ProcessingStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
                job.completed_at = datetime.utcnow()
                
            if error_message:
                job.error_message = error_message
                
            if increment_retry:
                job.retry_count += 1
                
            await self.session.commit()
            await self.session.refresh(job)
        return job

    async def log_usage(self, log_data: dict) -> AIUsageLog:
        log = AIUsageLog(**log_data)
        self.session.add(log)
        await self.session.commit()
        return log

    async def save_summary(self, summary_data: dict) -> AISummary:
        result = await self.session.execute(
            select(AISummary).where(AISummary.document_id == summary_data.get("document_id"))
        )
        summary = result.scalars().first()
        
        if summary:
            # Update existing
            for key, value in summary_data.items():
                setattr(summary, key, value)
        else:
            # Create new
            summary = AISummary(**summary_data)
            self.session.add(summary)
            
        await self.session.commit()
        await self.session.refresh(summary)
        return summary
        
    async def get_summary_by_document(self, document_id: uuid.UUID) -> Optional[AISummary]:
        result = await self.session.execute(
            select(AISummary).where(AISummary.document_id == document_id)
        )
        return result.scalars().first()

    async def get_all_jobs(self, skip: int = 0, limit: int = 100) -> list[tuple]:
        from ..models.case_document import CaseDocument
        from sqlalchemy.orm import joinedload
        
        # We need to query AIJobs and OCRJobs, and we want the document info.
        # Since these are two different tables, it's easiest to do separate queries and combine,
        # or we can just fetch AIJob with Document, and OCRJob with Document.
        
        ai_query = (
            select(AIJob, CaseDocument.original_filename, CaseDocument.case_id)
            .join(CaseDocument, AIJob.document_id == CaseDocument.id)
            .order_by(AIJob.created_at.desc())
            .offset(skip).limit(limit)
        )
        
        ocr_query = (
            select(OCRJob, CaseDocument.original_filename, CaseDocument.case_id)
            .join(CaseDocument, OCRJob.document_id == CaseDocument.id)
            .order_by(OCRJob.created_at.desc())
            .offset(skip).limit(limit)
        )
        
        ai_results = await self.session.execute(ai_query)
        ocr_results = await self.session.execute(ocr_query)
        
        jobs = []
        for job, doc_name, case_id in ai_results.all():
            jobs.append({"job": job, "type": "AI", "document_name": doc_name, "case_id": case_id})
            
        for job, doc_name, case_id in ocr_results.all():
            jobs.append({"job": job, "type": "OCR", "document_name": doc_name, "case_id": case_id})
            
        # Sort in memory by created_at desc and slice
        jobs.sort(key=lambda x: x["job"].created_at or datetime.min, reverse=True)
        return jobs[:limit]

    async def get_all_usage_logs(self, skip: int = 0, limit: int = 100) -> list[tuple]:
        from ..models.case_document import CaseDocument
        query = (
            select(AIUsageLog, CaseDocument.original_filename, CaseDocument.case_id)
            .join(CaseDocument, AIUsageLog.document_id == CaseDocument.id)
            .order_by(AIUsageLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.all()
