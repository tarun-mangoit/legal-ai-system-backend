import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.database.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.case_document import DocumentCategory
from app.schemas.document import DocumentResponse, DocumentWithStatusResponse
from app.repositories.document_repository import DocumentRepository
from app.core.local_storage_provider import LocalStorageProvider
from app.services.document_service import DocumentService

router = APIRouter()

def get_document_service(db: AsyncSession = Depends(get_db)):
    repository = DocumentRepository(db)
    storage = LocalStorageProvider()
    return DocumentService(repository, storage)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    case_id: uuid.UUID = Form(...),
    category: DocumentCategory = Form(...),
    remarks: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Upload a document for a specific case.
    """
    return await service.upload_document(
        case_id=case_id,
        user=current_user,
        file=file,
        category=category,
        remarks=remarks
    )

@router.get("", response_model=List[DocumentWithStatusResponse])
async def get_all_documents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    List all documents in the system with their AI status (Admin/Advocate only).
    """
    return await service.get_all_documents(current_user, skip, limit)

@router.get("/case/{case_id}", response_model=List[DocumentResponse])
async def list_documents(
    case_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    List all documents for a given case.
    """
    return await service.list_case_documents(case_id, current_user, skip, limit)

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Get document metadata.
    """
    return await service.get_document(document_id, current_user)

@router.get("/download/{document_id}")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Download a document file.
    """
    file_bytes, filename, mime_type = await service.download_document(document_id, current_user)
    
    return StreamingResponse(
        iter([file_bytes]), 
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Soft delete a document.
    """
    success = await service.delete_document(document_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete document")
    return {"message": "Document deleted successfully"}

@router.patch("/{document_id}/restore")
async def restore_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
):
    """
    Restore a deleted document (Admin only).
    """
    success = await service.restore_document(document_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to restore document")
    return {"message": "Document restored successfully"}
