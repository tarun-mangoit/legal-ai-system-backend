import uuid
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..models.user import User
from ..models.case import Case
from ..models.case_message import ConversationType, MessageType
from ..repositories.message_repository import MessageRepository
from ..repositories.case_repository import CaseRepository
from ..core.storage_provider import StorageProvider
from .document_service import ALLOWED_MIME_TYPES, MAX_FILE_SIZE

class MessageService:
    def __init__(self, message_repository: MessageRepository, case_repository: CaseRepository, storage_provider: StorageProvider, db: AsyncSession):
        self.message_repo = message_repository
        self.case_repo = case_repository
        self.storage = storage_provider
        self.db = db

    async def _get_user_role(self, user: User) -> str:
        from ..models.role import Role
        role = await self.message_repo.session.get(Role, user.role_id)
        return role.name if role else "unknown"

    async def _verify_case_access(self, case_id: uuid.UUID, user: User) -> Case:
        case = await self.case_repo.get(self.db, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
            
        role_name = await self._get_user_role(user)
        if role_name == "client" and case.client_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this case")
        elif role_name == "advocate" and case.advocate_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this case")
            
        return case

    async def get_messages(self, case_id: uuid.UUID, user: User, is_internal: bool = False, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        await self._verify_case_access(case_id, user)
        
        if is_internal:
            role_name = await self._get_user_role(user)
            if role_name == "client":
                raise HTTPException(status_code=403, detail="Clients cannot access internal notes")
            conversation_type = ConversationType.INTERNAL
        else:
            conversation_type = ConversationType.CLIENT
            
        conversation = await self.message_repo.get_or_create_conversation(case_id, conversation_type)
        messages = await self.message_repo.get_messages(conversation.id, skip, limit)
        
        # Mark as read automatically when fetching
        await self.message_repo.mark_as_read(conversation.id, user.id)
        
        result = []
        for msg in messages:
            read_status = any(r.user_id != user.id for r in msg.reads) # Very basic: if anyone else read it
            if msg.sender_id == user.id:
                # If I sent it, check if others read it
                is_read = len(msg.reads) > 1 # Assuming sender automatically counts as read, so >1 means someone else read it
            else:
                is_read = True # I'm fetching it now, so I read it
                
            result.append({
                "id": str(msg.id),
                "sender_id": str(msg.sender_id) if msg.sender_id else None,
                "sender_name": f"{msg.sender.first_name} {msg.sender.last_name}" if msg.sender else "System",
                "message_type": msg.message_type.value,
                "message": msg.message,
                "created_at": msg.created_at,
                "is_read": is_read,
                "attachments": [
                    {
                        "id": str(att.id),
                        "file_name": att.file_name,
                        "file_size": att.file_size,
                        "mime_type": att.mime_type,
                        "document_id": str(att.document_id) if att.document_id else None
                    } for att in msg.attachments
                ]
            })
            
        return result

    async def send_message(
        self, case_id: uuid.UUID, user: User, message: str, 
        is_internal: bool = False, message_type: MessageType = MessageType.TEXT,
        files: Optional[List[UploadFile]] = None
    ):
        await self._verify_case_access(case_id, user)
        role_name = await self._get_user_role(user)
        
        if is_internal and role_name == "client":
            raise HTTPException(status_code=403, detail="Clients cannot create internal notes")
            
        conversation_type = ConversationType.INTERNAL if is_internal else ConversationType.CLIENT
        conversation = await self.message_repo.get_or_create_conversation(case_id, conversation_type)
        
        # Create message
        new_msg = await self.message_repo.create_message(
            conversation_id=conversation.id,
            sender_id=user.id,
            message_type=message_type,
            message=message
        )
        
        # Handle attachments
        if files:
            for file in files:
                file.file.seek(0, 2)
                file_size = file.file.tell()
                await file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    continue # Skip large files or raise error
                    
                if file.content_type not in ALLOWED_MIME_TYPES:
                    continue
                    
                extension = ALLOWED_MIME_TYPES[file.content_type]
                stored_filename = f"{uuid.uuid4()}{extension}"
                now = datetime.utcnow()
                path = f"{now.year}/{now.month:02d}/case_{case_id}/message_attachments/{stored_filename}"
                
                storage_path = await self.storage.save_file(file, path)
                
                await self.message_repo.add_attachment(
                    message_id=new_msg.id,
                    file_name=file.filename,
                    file_path=storage_path,
                    file_size=file_size,
                    mime_type=file.content_type
                )
                
        # Trigger notifications (if not internal note, or if internal note, notify advocate/admin)
        # We can integrate with Notification system here
        
        return {"status": "success", "message_id": str(new_msg.id)}
        
    async def get_attachment_download(self, case_id: uuid.UUID, attachment_id: uuid.UUID, user: User):
        await self._verify_case_access(case_id, user)
        attachment = await self.message_repo.get_attachment(attachment_id)
        if not attachment:
             raise HTTPException(status_code=404, detail="Attachment not found")
             
        # Verify if user has access to this conversation
        if attachment.message.conversation.conversation_type == ConversationType.INTERNAL:
             role_name = await self._get_user_role(user)
             if role_name == "client":
                  raise HTTPException(status_code=403, detail="Cannot access internal attachments")
                  
        file_bytes = await self.storage.get_file(attachment.file_path)
        return file_bytes, attachment.file_name, attachment.mime_type
