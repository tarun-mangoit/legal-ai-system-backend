import asyncio
import uuid
import logging
from celery import shared_task
from ..core.celery_app import celery_app
from ..database.session import AsyncSessionLocal
from ..repositories.processing_repositories import OCRRepository, AIRepository
from ..repositories.document_repository import DocumentRepository
from ..services.ocr_service import OCRService
from ..services.ai_service import AIService
from ..models.ai_summary import ProcessingStatus

logger = logging.getLogger(__name__)

def async_run(coro):
    """Helper to run async code synchronously in celery workers."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@shared_task(bind=True, max_retries=3)
def process_document_pipeline(self, document_id_str: str, case_id_str: str):
    """
    Main Celery pipeline: Upload -> OCR -> AI Analysis -> Store Result
    """
    logger.info(f"Starting processing pipeline for document: {document_id_str}")
    document_id = uuid.UUID(document_id_str)
    case_id = uuid.UUID(case_id_str)
    
    async def _run_pipeline():
        async with AsyncSessionLocal() as db:
            ocr_repo = OCRRepository(db)
            ai_repo = AIRepository(db)
            doc_repo = DocumentRepository(db)
            
            ocr_service = OCRService()
            ai_service = AIService(ai_repo)
            
            # 1. Update Job Statuses to PROCESSING
            await ocr_repo.update_status(document_id, ProcessingStatus.PROCESSING)
            await ai_repo.update_job_status(document_id, ProcessingStatus.PROCESSING)
            
            # Fetch document
            document = await doc_repo.get_by_id(document_id)
            if not document:
                error = f"Document {document_id} not found."
                await ocr_repo.update_status(document_id, ProcessingStatus.FAILED, error)
                await ai_repo.update_job_status(document_id, ProcessingStatus.FAILED, error)
                return
                
            # 2. Extract Text (OCR/Parsing)
            try:
                extracted_text = ocr_service.extract_text(document.storage_path, document.mime_type, document.extension)
                
                # Update Document with extracted text
                document.extracted_text = extracted_text
                await db.commit()
                
                await ocr_repo.update_status(document_id, ProcessingStatus.COMPLETED)
                
            except Exception as e:
                logger.error(f"OCR Failed for document {document_id}: {e}")
                await ocr_repo.update_status(document_id, ProcessingStatus.FAILED, str(e))
                await ai_repo.update_job_status(document_id, ProcessingStatus.FAILED, f"OCR Failed: {e}")
                raise self.retry(exc=e, countdown=60)
                
            # 3. AI Analysis
            if not extracted_text or not extracted_text.strip():
                error = "Extracted text is empty. Cannot perform AI analysis."
                await ai_repo.update_job_status(document_id, ProcessingStatus.FAILED, error)
                return
                
            try:
                await ai_service.analyze(case_id, document_id, extracted_text)
                await ai_repo.update_job_status(document_id, ProcessingStatus.COMPLETED)
            except Exception as e:
                logger.error(f"AI Analysis Failed for document {document_id}: {e}")
                await ai_repo.update_job_status(document_id, ProcessingStatus.FAILED, str(e), increment_retry=True)
                raise self.retry(exc=e, countdown=120)

    # Execute the async coroutine
    try:
        async_run(_run_pipeline())
    except Exception as e:
        logger.error(f"Pipeline crashed for document {document_id}: {e}")
        # The retry is raised inside the coroutine, but Celery intercepts it outside if raised properly
        # Wait, self.retry inside coroutine throws Retry exception. We need to handle it.
        # It's better to catch Retry and re-raise.
        raise
