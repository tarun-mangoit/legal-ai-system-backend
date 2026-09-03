import enum
from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class AIConversationType(str, enum.Enum):
    CASE_CHAT = "CASE_CHAT"
    DOCUMENT_CHAT = "DOCUMENT_CHAT"

class AIConversation(BaseModel):
    __tablename__ = "ai_conversations"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_type = Column(Enum(AIConversationType, name="ai_conversation_type_enum", create_type=False), nullable=False)
    title = Column(String, nullable=True)

    # Relationships
    case = relationship("Case", backref="ai_conversations")
    user = relationship("User", backref="ai_conversations")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="asc(AIMessage.created_at)")
