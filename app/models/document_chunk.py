from sqlalchemy import Column, String, ForeignKey, Integer, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel

class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"

    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(String, nullable=False)
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=False, default=0)
    
    # Vector embedding fallback for Phase 1
    embedding = Column(JSON, nullable=True) 
    
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("CaseDocument")
    case = relationship("Case")
