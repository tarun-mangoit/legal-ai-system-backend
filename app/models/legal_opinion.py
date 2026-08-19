import uuid
from enum import Enum
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class OpinionStatus(Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    FINALIZED = "FINALIZED"
    REJECTED = "REJECTED"

class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class LegalOpinion(BaseModel):
    __tablename__ = "legal_opinions"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True)
    advocate_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    summary = Column(Text, nullable=True)
    legal_analysis = Column(Text, nullable=True)
    facts = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)
    applicable_laws = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    winning_probability = Column(Integer, nullable=True) # 0-100
    risk_level = Column(SQLEnum(RiskLevel), nullable=True)
    status = Column(SQLEnum(OpinionStatus), default=OpinionStatus.DRAFT, nullable=False)
    
    is_final = Column(Boolean, default=False, nullable=False)
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    case = relationship("Case", back_populates="legal_opinion")
    advocate = relationship("User", foreign_keys=[advocate_id])
    revisions = relationship("OpinionRevision", back_populates="opinion", cascade="all, delete-orphan")
    comments = relationship("OpinionComment", back_populates="opinion", cascade="all, delete-orphan")

class OpinionRevision(BaseModel):
    __tablename__ = "opinion_revisions"

    opinion_id = Column(UUID(as_uuid=True), ForeignKey("legal_opinions.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    changes_summary = Column(String, nullable=True)

    opinion = relationship("LegalOpinion", back_populates="revisions")
    author = relationship("User", foreign_keys=[changed_by])

class OpinionComment(BaseModel):
    __tablename__ = "opinion_comments"

    opinion_id = Column(UUID(as_uuid=True), ForeignKey("legal_opinions.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment = Column(Text, nullable=False)

    opinion = relationship("LegalOpinion", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
