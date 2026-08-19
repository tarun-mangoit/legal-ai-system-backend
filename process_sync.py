import asyncio
from app.database.session import AsyncSessionLocal
from app.models.job_tracking import OCRJob
from app.repositories.processing_repositories import OCRRepository, AIRepository
from app.repositories.document_repository import DocumentRepository
from app.services.ocr_service import OCRService
from app.services.ai_service import AIService
from app.models.ai_summary import ProcessingStatus
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OCRJob).where(OCRJob.status == 'PENDING'))
        jobs = result.scalars().all()
        
        ocr_repo = OCRRepository(db)
        ai_repo = AIRepository(db)
        doc_repo = DocumentRepository(db)
        
        ocr_service = OCRService()
        ai_service = AIService(ai_repo)
        
        for job in jobs:
            print(f"Processing task for Document ID: {job.document_id}")
            doc = await doc_repo.get_by_id(job.document_id)
            if doc:
                try:
                    await ocr_repo.update_status(job.document_id, ProcessingStatus.PROCESSING)
                    await ai_repo.update_job_status(job.document_id, ProcessingStatus.PROCESSING)
                    extracted_text = ocr_service.extract_text(doc.storage_path, doc.mime_type, doc.extension)
                    doc.extracted_text = extracted_text
                    await db.commit()
                    await ocr_repo.update_status(job.document_id, ProcessingStatus.COMPLETED)
                    print(f"OCR finished for: {job.document_id}")
                    
                    if extracted_text:
                        await ai_service.analyze(doc.case_id, job.document_id, extracted_text)
                        await ai_repo.update_job_status(job.document_id, ProcessingStatus.COMPLETED)
                        print(f"AI Summary generated for: {job.document_id}")
                    
                except Exception as e:
                    print(f"Error processing Document ID {job.document_id}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
