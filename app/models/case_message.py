import enum
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .base import BaseModel

class ConversationType(str, enum.Enum):
    CLIENT = "CLIENT"
    INTERNAL = "INTERNAL"

class MessageType(str, enum.Enum):
    TEXT = "TEXT"
    INTERNAL_NOTE = "INTERNAL_NOTE"
    SYSTEM = "SYSTEM"
    DOCUMENT = "DOCUMENT"
    DOCUMENT_REQUEST = "DOCUMENT_REQUEST"

class CaseConversation(BaseModel):
    __tablename__ = "case_conversations"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    conversation_type = Column(Enum(ConversationType), nullable=False)

    case = relationship("Case")
    messages = relationship("CaseMessage", back_populates="conversation", cascade="all, delete-orphan")

class CaseMessage(BaseModel):
    __tablename__ = "case_messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("case_conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Nullable for SYSTEM messages
    message_type = Column(Enum(MessageType), nullable=False, default=MessageType.TEXT)
    message = Column(Text, nullable=False)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("case_messages.id"), nullable=True)
    
    deleted_at = Column(DateTime, nullable=True)

    conversation = relationship("CaseConversation", back_populates="messages")
    sender = relationship("User")
    attachments = relationship("CaseMessageAttachment", back_populates="message", cascade="all, delete-orphan")
    reads = relationship("CaseMessageRead", back_populates="message", cascade="all, delete-orphan")
    parent_message = relationship("CaseMessage", remote_side="CaseMessage.id")

class CaseMessageAttachment(BaseModel):
    __tablename__ = "case_message_attachments"

    message_id = Column(UUID(as_uuid=True), ForeignKey("case_messages.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id"), nullable=True) # Optional link to official CaseDocument
    
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    message = relationship("CaseMessage", back_populates="attachments")
    document = relationship("CaseDocument")

class CaseMessageRead(BaseModel):
    __tablename__ = "case_message_reads"

    message_id = Column(UUID(as_uuid=True), ForeignKey("case_messages.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    message = relationship("CaseMessage", back_populates="reads")
    user = relationship("User")
