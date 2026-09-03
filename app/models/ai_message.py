import enum
from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel

class AIRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

class AIMessage(BaseModel):
    __tablename__ = "ai_messages"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("ai_conversations.id"), nullable=False, index=True)
    role = Column(Enum(AIRole, name="ai_role_enum", create_type=False), nullable=False)
    message = Column(String, nullable=False)
    sources = Column(JSONB, nullable=True)  # List of dicts representing sources

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")
