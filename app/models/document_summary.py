from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel

class DocumentSummary(BaseModel):
    __tablename__ = "document_summaries"

    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id", ondelete="CASCADE"), nullable=False, unique=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    
    summary = Column(String, nullable=True)
    document_type = Column(String, nullable=True)
    
    key_facts = Column(JSON, nullable=True)
    important_dates = Column(JSON, nullable=True)
    legal_references = Column(JSON, nullable=True)
    potential_issues = Column(JSON, nullable=True)
    evidence_found = Column(JSON, nullable=True)
    missing_information = Column(JSON, nullable=True)
    
    ai_confidence = Column(Float, nullable=True)
    ai_model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    document = relationship("CaseDocument")
    case = relationship("Case")
