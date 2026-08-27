import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import BaseModel

class OpinionStatus(str, enum.Enum):
    NOT_GENERATED = "NOT_GENERATED"
    GENERATING = "GENERATING"
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    REVISED = "REVISED"
    APPROVED = "APPROVED"
    PDF_GENERATED = "PDF_GENERATED"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class LegalOpinion(BaseModel):
    __tablename__ = "legal_opinions"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True)
    case_analysis_id = Column(UUID(as_uuid=True), ForeignKey("case_analyses.id", ondelete="SET NULL"), nullable=True)
    
    version = Column(Integer, nullable=False, default=1)
    status = Column(SQLEnum(OpinionStatus, name="opinion_status_enum", create_type=False), default=OpinionStatus.NOT_GENERATED, nullable=False)

    # AI Generated Content (Draft)
    documents_reviewed = Column(JSON, nullable=True)
    instructions = Column(Text, nullable=True)
    brief_facts = Column(Text, nullable=True)
    issues = Column(JSON, nullable=True)
    applicable_law = Column(JSON, nullable=True)
    legal_analysis = Column(Text, nullable=True)
    evidence_assessment = Column(Text, nullable=True)
    precedents = Column(JSON, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    risks = Column(JSON, nullable=True)
    risk_level = Column(String, nullable=True)
    conclusion = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    disclaimer = Column(Text, nullable=True)

    # Advocate's Professional Opinion (Not overwritten by AI)
    advocate_opinion = Column(Text, nullable=True)
    advocate_recommendations = Column(JSON, nullable=True)
    winning_probability = Column(Integer, nullable=True) # 0-100
    advocate_risk_assessment = Column(Text, nullable=True)
    advocate_notes = Column(Text, nullable=True)

    ai_model = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Signatures
    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    signature_file = Column(String, nullable=True)

    case = relationship("Case", back_populates="legal_opinion")
    analysis = relationship("CaseAnalysis")
    creator = relationship("User", foreign_keys=[created_by])
    signer = relationship("User", foreign_keys=[signed_by])
    versions = relationship("LegalOpinionVersion", back_populates="opinion", cascade="all, delete-orphan")

class LegalOpinionVersion(BaseModel):
    __tablename__ = "legal_opinion_versions"

    opinion_id = Column(UUID(as_uuid=True), ForeignKey("legal_opinions.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(JSON, nullable=False) # Store snapshot of the opinion
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_summary = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    opinion = relationship("LegalOpinion", back_populates="versions")
    author = relationship("User", foreign_keys=[changed_by])
