import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import Response

from app.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.case_message import MessageType
from app.repositories.message_repository import MessageRepository
from app.repositories.case_repository import CaseRepository
from app.services.message_service import MessageService
from app.core.local_storage_provider import LocalStorageProvider

router = APIRouter()

def get_message_service(db: AsyncSession = Depends(get_db)):
    msg_repo = MessageRepository(db)
    case_repo = CaseRepository()
    storage = LocalStorageProvider()
    return MessageService(msg_repo, case_repo, storage, db)

@router.get("/{case_id}/messages")
async def get_messages(
    case_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user)
):
    """Get standard client conversation messages"""
    return await service.get_messages(case_id, current_user, is_internal=False, skip=skip, limit=limit)

@router.post("/{case_id}/messages")
async def send_message(
    case_id: uuid.UUID,
    message: str = Form(...),
    files: List[UploadFile] = File(None),
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user)
):
    """Send a message to the client conversation"""
    if not message and not files:
        raise HTTPException(status_code=400, detail="Message or files required")
    return await service.send_message(case_id, current_user, message=message, files=files, is_internal=False)

@router.get("/{case_id}/internal-notes")
async def get_internal_notes(
    case_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user)
):
    """Get internal notes (Admin/Advocate only)"""
    return await service.get_messages(case_id, current_user, is_internal=True, skip=skip, limit=limit)

@router.post("/{case_id}/internal-notes")
async def send_internal_note(
    case_id: uuid.UUID,
    message: str = Form(...),
    files: List[UploadFile] = File(None),
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user)
):
    """Send an internal note (Admin/Advocate only)"""
    if not message and not files:
        raise HTTPException(status_code=400, detail="Message or files required")
    return await service.send_message(
        case_id, current_user, message=message, files=files, 
        is_internal=True, message_type=MessageType.INTERNAL_NOTE
    )

@router.get("/{case_id}/messages/attachments/{attachment_id}")
async def download_message_attachment(
    case_id: uuid.UUID,
    attachment_id: uuid.UUID,
    service: MessageService = Depends(get_message_service),
    current_user: User = Depends(get_current_user)
):
    """Download an attachment securely"""
    file_bytes, filename, mime_type = await service.get_attachment_download(case_id, attachment_id, current_user)
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
