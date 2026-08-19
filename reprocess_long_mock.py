import asyncio
from app.database.session import AsyncSessionLocal
from app.models.ai_summary import AISummary, ProcessingStatus
from app.models.job_tracking import AIJob, AIUsageLog, OCRJob
from app.models.case_document import CaseDocument
from app.repositories.processing_repositories import OCRRepository, AIRepository
from app.repositories.document_repository import DocumentRepository
from app.services.ocr_service import OCRService
from app.services.ai_service import AIService
from sqlalchemy import select, delete

async def main():
    async with AsyncSessionLocal() as db:
        doc_id = "49f32c5b-eac5-4aae-954b-9266f67ca355"
        
        # Delete existing summary and usage logs to allow re-run
        await db.execute(delete(AISummary).where(AISummary.document_id == doc_id))
        await db.execute(delete(AIUsageLog).where(AIUsageLog.document_id == doc_id))
        
        # Reset AI job status
        job = await db.execute(select(AIJob).where(AIJob.document_id == doc_id))
        job = job.scalars().first()
        if job:
            job.status = 'PENDING'
            
        await db.commit()
        
        # Process again
        ocr_repo = OCRRepository(db)
        ai_repo = AIRepository(db)
        doc_repo = DocumentRepository(db)
        
        ocr_service = OCRService()
        ai_service = AIService(ai_repo)
        
        doc = await doc_repo.get_by_id(doc_id)
        if doc:
            try:
                await ocr_repo.update_status(doc_id, ProcessingStatus.PROCESSING)
                await ai_repo.update_job_status(doc_id, ProcessingStatus.PROCESSING)
                extracted_text = ocr_service.extract_text(doc.storage_path, doc.mime_type, doc.extension)
                doc.extracted_text = extracted_text
                await db.commit()
                await ocr_repo.update_status(doc_id, ProcessingStatus.COMPLETED)
                
                await ai_service.analyze(doc.case_id, doc_id, extracted_text)
                await ai_repo.update_job_status(doc_id, ProcessingStatus.COMPLETED)
                print(f"Long AI Summary successfully generated for {doc_id}!")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
