from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.ai_conversation import AIConversationType
from app.models.ai_message import AIRole

class AIMessageSource(BaseModel):
    document_id: UUID
    document_name: str
    page: Optional[int] = None

class AIMessageBase(BaseModel):
    role: AIRole
    message: str
    sources: Optional[List[AIMessageSource]] = None

class AIMessageResponse(AIMessageBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIConversationResponse(BaseModel):
    id: UUID
    case_id: UUID
    user_id: UUID
    conversation_type: AIConversationType
    title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[AIMessageResponse] = []

    class Config:
        from_attributes = True

class CaseChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str

class CaseChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: List[AIMessageSource] = []

class DocumentChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str
    document_ids: List[UUID]

class DocumentChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    answer: str
    sources: List[AIMessageSource] = []
