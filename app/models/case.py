import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    PENDING_ASSIGNMENT = "PENDING_ASSIGNMENT"
    ADVOCATE_ASSIGNED = "ADVOCATE_ASSIGNED"
    DOCUMENTS_UPLOADED = "DOCUMENTS_UPLOADED"
    AI_PROCESSING = "AI_PROCESSING"
    IN_PROGRESS = "IN_PROGRESS"
    DOCUMENTS_UNDER_REVIEW = "DOCUMENTS_UNDER_REVIEW"
    INFORMATION_REQUIRED = "INFORMATION_REQUIRED"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    LEGAL_OPINION_DRAFT = "LEGAL_OPINION_DRAFT"
    LEGAL_OPINION_SUBMITTED = "LEGAL_OPINION_SUBMITTED"
    OPINION_GENERATED = "OPINION_GENERATED"
    REPORT_GENERATED = "REPORT_GENERATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"

class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Case(BaseModel):
    __tablename__ = "cases"

    case_number = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    advocate_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=True) # Maps to Practice Area
    case_type = Column(String, nullable=True)
    
    # Legal Matter specific fields
    incident_date = Column(String, nullable=True)
    notice_date = Column(String, nullable=True)
    filing_date = Column(String, nullable=True)
    next_hearing_date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    previous_legal_action = Column(String, nullable=True)
    previous_case_info = Column(String, nullable=True)
    opposing_party_name = Column(String, nullable=True)
    opposing_party_type = Column(String, nullable=True)
    additional_information = Column(String, nullable=True)
    
    case_fee = Column(Float, nullable=True)
    
    status = Column(Enum(CaseStatus, name="case_status_enum", create_type=False), nullable=False, default=CaseStatus.NEW)
    priority = Column(Enum(CasePriority, name="case_priority_enum", create_type=False), nullable=False, default=CasePriority.MEDIUM)
    
    # Relationships
    client = relationship("User", foreign_keys=[client_id], backref="client_cases")
    advocate = relationship("User", foreign_keys=[advocate_id], backref="advocate_cases")
    history = relationship("CaseHistory", back_populates="case", cascade="all, delete-orphan")
    assignments = relationship("CaseAssignment", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("CaseDocument", back_populates="case", cascade="all, delete-orphan")
    legal_opinion = relationship("LegalOpinion", back_populates="case", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="case", cascade="all, delete-orphan")
