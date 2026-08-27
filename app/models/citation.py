import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel

class CitationVerificationStatus(str, enum.Enum):
    AI_SUGGESTED = "AI_SUGGESTED"
    ADVOCATE_VERIFIED = "ADVOCATE_VERIFIED"
    REJECTED = "REJECTED"

class Citation(BaseModel):
    __tablename__ = "citations"

    case_name = Column(String, nullable=False, index=True)
    citation = Column(String, nullable=False, unique=True, index=True)
    court = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    legal_area = Column(String, nullable=True)
    principle = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    
    verified = Column(SQLEnum(CitationVerificationStatus, name="citation_verification_status_enum", create_type=False), nullable=False, default=CitationVerificationStatus.AI_SUGGESTED)
    
    # Vector embedding fallback for Phase 1
    embedding = Column(JSON, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", foreign_keys=[created_by])
