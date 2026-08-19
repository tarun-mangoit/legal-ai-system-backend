import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base

class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    html_content = Column(Text, nullable=False)
    template_type = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports = relationship("Report", back_populates="template")


class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False, index=True)
    opinion_id = Column(UUID(as_uuid=True), ForeignKey("legal_opinions.id"), nullable=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    version = Column(Integer, default=1, nullable=False)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    
    file_path = Column(String, nullable=True)
    storage_provider = Column(String, nullable=True)
    storage_key = Column(String, nullable=True)
    
    generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    case = relationship("Case", backref="reports")
    opinion = relationship("LegalOpinion", backref="reports")
    template = relationship("ReportTemplate", back_populates="reports")
    generator = relationship("User", backref="generated_reports")
    versions = relationship("ReportVersion", back_populates="report", cascade="all, delete-orphan")


class ReportVersion(Base):
    __tablename__ = "report_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    file_path = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    changes = Column(Text, nullable=True)
    
    generated_at = Column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="versions")
    generator = relationship("User")
