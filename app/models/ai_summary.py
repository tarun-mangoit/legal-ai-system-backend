import enum
from sqlalchemy import Column, String, ForeignKey, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

class AISummary(BaseModel):
    __tablename__ = "ai_summaries"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("case_documents.id"), nullable=False, unique=True)
    
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    processing_time = Column(Float, nullable=False, default=0.0)
    cost = Column(Float, nullable=False, default=0.0)
    
    case_details = Column(JSON, nullable=True)
    background = Column(String, nullable=True)
    plaintiff_claims = Column(JSON, nullable=True)
    defendant_position = Column(JSON, nullable=True)
    
    important_facts = Column(JSON, nullable=True)
    timeline = Column(JSON, nullable=True)
    legal_issues = Column(JSON, nullable=True)
    
    reliefs_sought = Column(JSON, nullable=True)
    supporting_documents = Column(JSON, nullable=True)
    
    risk_assessment = Column(JSON, nullable=True)
    overall_summary = Column(String, nullable=True)
    
    raw_response = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default=ProcessingStatus.PENDING.value)

    case = relationship("Case")
    document = relationship("CaseDocument")
