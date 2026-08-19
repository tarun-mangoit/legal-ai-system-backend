import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.processing_repositories import OCRRepository, AIRepository
from app.repositories.document_repository import DocumentRepository
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_processing_service import DocumentProcessingService
from app.schemas.job_tracking import JobTrackingResponse, AIUsageResponse
from typing import List

router = APIRouter()

def get_processing_service(db: AsyncSession = Depends(get_db)):
    ocr_repo = OCRRepository(db)
    ai_repo = AIRepository(db)
    return DocumentProcessingService(ocr_repo, ai_repo)

@router.get("/jobs", response_model=List[JobTrackingResponse])
async def get_all_jobs(
    skip: int = 0,
    limit: int = 100,
    service: DocumentProcessingService = Depends(get_processing_service),
    current_user: User = Depends(get_current_user)
):
    return await service.get_all_jobs(current_user, skip, limit)

@router.get("/usage", response_model=List[AIUsageResponse])
async def get_all_usage(
    skip: int = 0,
    limit: int = 100,
    service: DocumentProcessingService = Depends(get_processing_service),
    current_user: User = Depends(get_current_user)
):
    return await service.get_all_usage(current_user, skip, limit)

@router.post("/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: DocumentProcessingService = Depends(get_processing_service),
    current_user: User = Depends(get_current_user)
):
    """Triggers the async document processing pipeline."""
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return await service.trigger_processing(document_id, document.case_id)

@router.get("/{document_id}/processing-status")
async def get_processing_status(
    document_id: uuid.UUID,
    service: DocumentProcessingService = Depends(get_processing_service),
    current_user: User = Depends(get_current_user)
):
    """Gets the current status of document processing."""
    return await service.get_processing_status(document_id)

@router.get("/{document_id}/summary")
async def get_document_summary(
    document_id: uuid.UUID,
    service: DocumentProcessingService = Depends(get_processing_service),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the AI summary for a document."""
    return await service.get_summary(document_id)

@router.post("/{document_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_processing(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    service: DocumentProcessingService = Depends(get_processing_service),
    current_user: User = Depends(get_current_user)
):
    """Retries the document processing pipeline."""
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return await service.trigger_processing(document_id, document.case_id)

@router.get("/{document_id}/text")
async def get_extracted_text(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the raw extracted text of the document."""
    doc_repo = DocumentRepository(db)
    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.extracted_text:
        return None
        
    return {"document_id": str(document_id), "extracted_text": document.extracted_text}
