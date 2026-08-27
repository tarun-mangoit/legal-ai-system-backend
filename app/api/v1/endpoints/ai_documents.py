import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.ai_legal import DocumentSummaryResponse, DocumentSummaryUpdate, DocumentSummaryCreate
from app.models.case_document import CaseDocument, DocumentProcessingStatus
from app.models.document_summary import DocumentSummary
from app.tasks.ai_tasks import generate_document_summary_task, process_document_task
from datetime import datetime
from sqlalchemy import select

router = APIRouter()

@router.post("/{document_id}/process", response_model=dict)
async def process_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Dispatch to background task
    process_document_task.delay(str(document_id))
    return {"status": "success", "message": f"Document {document_id} queued for processing"}

@router.post("/{document_id}/summary", response_model=DocumentSummaryResponse)
async def generate_summary(document_id: uuid.UUID, case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Check if summary exists
    result = await db.execute(select(DocumentSummary).where(DocumentSummary.document_id == document_id))
    summary = result.scalars().first()
    
    if summary:
        # Clear existing AI fields
        summary.summary = "Generating summary in background..."
        summary.key_facts = None
        summary.important_dates = None
        summary.legal_references = None
        summary.potential_issues = None
        summary.evidence_found = None
        summary.missing_information = None
        summary.ai_confidence = None
    else:
        # Create new record
        summary = DocumentSummary(
            document_id=document_id,
            case_id=case_id,
            summary="Generating summary in background..."
        )
        db.add(summary)
    
    # Update document status
    doc_result = await db.execute(select(CaseDocument).where(CaseDocument.id == document_id))
    document = doc_result.scalars().first()
    if document:
        document.status = DocumentProcessingStatus.SUMMARY_GENERATING

    await db.commit()
    await db.refresh(summary)

    # Dispatch the celery task
    generate_document_summary_task.delay(str(document_id), str(case_id))
    
    return summary

@router.get("/{document_id}/summary", response_model=DocumentSummaryResponse)
async def get_summary(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentSummary).where(DocumentSummary.document_id == document_id))
    summary = result.scalars().first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Document summary not found")
        
    return summary

@router.put("/{document_id}/summary", response_model=DocumentSummaryResponse)
async def update_summary(document_id: uuid.UUID, data: DocumentSummaryUpdate, db: AsyncSession = Depends(get_db)):
    # Mock update
    return DocumentSummaryResponse(
        id=uuid.uuid4(),
        document_id=document_id,
        case_id=uuid.uuid4(),
        summary=data.summary or "Mock updated summary",
        created_at=datetime.utcnow()
    )

@router.put("/{document_id}/relevance", response_model=dict)
async def update_document_relevance(document_id: uuid.UUID, include_in_analysis: bool, db: AsyncSession = Depends(get_db)):
    # Mock behavior
    return {"status": "success", "include_in_analysis": include_in_analysis}
