import enum
from sqlalchemy import Column, String, ForeignKey, JSON, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel

class CaseAnalysisStatus(str, enum.Enum):
    NOT_GENERATED = "NOT_GENERATED"
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"

class CaseAnalysis(BaseModel):
    __tablename__ = "case_analyses"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    executive_summary = Column(String, nullable=True)
    material_facts = Column(JSON, nullable=True)
    chronology = Column(JSON, nullable=True)
    legal_issues = Column(JSON, nullable=True)
    applicable_laws = Column(JSON, nullable=True)
    evidence_assessment = Column(JSON, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    risks = Column(JSON, nullable=True)
    missing_information = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    suggested_precedents = Column(JSON, nullable=True)
    
    ai_model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    
    status = Column(Enum(CaseAnalysisStatus, name="case_analysis_status_enum", create_type=False), nullable=False, default=CaseAnalysisStatus.NOT_GENERATED)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    case = relationship("Case")
    creator = relationship("User", foreign_keys=[created_by])
