import enum
from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel

class DocumentCategory(str, enum.Enum):
    EVIDENCE = "EVIDENCE"
    PLEADING = "PLEADING"
    ORDER = "ORDER"
    CORRESPONDENCE = "CORRESPONDENCE"
    IDENTIFICATION = "IDENTIFICATION"
    CONTRACT = "CONTRACT"
    OTHER = "OTHER"

class DocumentProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    OCR_REQUIRED = "OCR_REQUIRED"
    TEXT_EXTRACTED = "TEXT_EXTRACTED"
    EMBEDDING_CREATED = "EMBEDDING_CREATED"
    READY = "READY"
    SUMMARY_GENERATING = "SUMMARY_GENERATING"
    SUMMARY_READY = "SUMMARY_READY"
    FAILED = "FAILED"

class CaseDocument(BaseModel):
    __tablename__ = "case_documents"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    category = Column(String, nullable=False, default=DocumentCategory.OTHER.value)
    
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False, unique=True, index=True)
    mime_type = Column(String, nullable=False)
    extension = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)
    
    sha256_hash = Column(String, index=True, nullable=False)
    
    is_deleted = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)
    remarks = Column(String, nullable=True)
    extracted_text = Column(String, nullable=True)
    status = Column(Enum(DocumentProcessingStatus, name="document_processing_status_enum", create_type=False), nullable=False, default=DocumentProcessingStatus.UPLOADED)
    include_in_analysis = Column(Boolean, nullable=False, default=False)

    # Relationships
    case = relationship("Case", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])
