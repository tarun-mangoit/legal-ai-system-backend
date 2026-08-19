import uuid
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from ..models.case_message import CaseConversation, CaseMessage, CaseMessageAttachment, CaseMessageRead, ConversationType, MessageType

class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(self, case_id: uuid.UUID, conversation_type: ConversationType) -> CaseConversation:
        stmt = select(CaseConversation).where(
            and_(
                CaseConversation.case_id == case_id,
                CaseConversation.conversation_type == conversation_type
            )
        )
        result = await self.session.execute(stmt)
        conversation = result.scalars().first()

        if not conversation:
            conversation = CaseConversation(case_id=case_id, conversation_type=conversation_type)
            self.session.add(conversation)
            await self.session.commit()
            await self.session.refresh(conversation)
            
        return conversation

    async def get_messages(self, conversation_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[CaseMessage]:
        stmt = select(CaseMessage).options(
            selectinload(CaseMessage.sender),
            selectinload(CaseMessage.attachments),
            selectinload(CaseMessage.reads)
        ).where(
            and_(
                CaseMessage.conversation_id == conversation_id,
                CaseMessage.deleted_at == None
            )
        ).order_by(CaseMessage.created_at.asc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_message(self, conversation_id: uuid.UUID, sender_id: Optional[uuid.UUID], message_type: MessageType, message: str, parent_message_id: Optional[uuid.UUID] = None) -> CaseMessage:
        new_message = CaseMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            message_type=message_type,
            message=message,
            parent_message_id=parent_message_id
        )
        self.session.add(new_message)
        await self.session.commit()
        await self.session.refresh(new_message)
        
        # Load relationships so it's ready to return
        stmt = select(CaseMessage).options(
            selectinload(CaseMessage.sender),
            selectinload(CaseMessage.attachments),
            selectinload(CaseMessage.reads)
        ).where(CaseMessage.id == new_message.id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add_attachment(self, message_id: uuid.UUID, file_name: str, file_path: str, file_size: int, mime_type: str, document_id: Optional[uuid.UUID] = None) -> CaseMessageAttachment:
        attachment = CaseMessageAttachment(
            message_id=message_id,
            document_id=document_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type
        )
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment

    async def get_attachment(self, attachment_id: uuid.UUID) -> Optional[CaseMessageAttachment]:
        stmt = select(CaseMessageAttachment).options(
            selectinload(CaseMessageAttachment.message).selectinload(CaseMessage.conversation)
        ).where(CaseMessageAttachment.id == attachment_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def mark_as_read(self, conversation_id: uuid.UUID, user_id: uuid.UUID):
        # Find all messages in the conversation not yet read by this user
        stmt = select(CaseMessage).where(
            and_(
                CaseMessage.conversation_id == conversation_id,
                CaseMessage.deleted_at == None,
                ~CaseMessage.reads.any(CaseMessageRead.user_id == user_id)
            )
        )
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        
        for msg in messages:
            read_record = CaseMessageRead(message_id=msg.id, user_id=user_id)
            self.session.add(read_record)
            
        if messages:
            await self.session.commit()

    async def get_unread_count(self, user_id: uuid.UUID, case_id: uuid.UUID) -> int:
        # Complex query to count unread messages in conversations for a specific case
        stmt = select(CaseMessage).join(CaseConversation).where(
            and_(
                CaseConversation.case_id == case_id,
                CaseMessage.deleted_at == None,
                ~CaseMessage.reads.any(CaseMessageRead.user_id == user_id)
            )
        )
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
