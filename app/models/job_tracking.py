from sqlalchemy import Column, String, ForeignKey, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from .ai_summary import ProcessingStatus

class OCRJob(BaseModel):
    __tablename__ = "ocr_jobs"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default=ProcessingStatus.PENDING.value)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)

    document = relationship("CaseDocument")

class AIJob(BaseModel):
    __tablename__ = "ai_jobs"
    
    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default=ProcessingStatus.PENDING.value)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(String, nullable=True)

    document = relationship("CaseDocument")

class AIUsageLog(BaseModel):
    __tablename__ = "ai_usage_logs"

    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id"), nullable=False, index=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=False, default=0.0)
    processing_time = Column(Float, nullable=False, default=0.0)

    document = relationship("CaseDocument")
