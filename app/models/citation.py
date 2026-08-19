import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from .base import Base

class CitationCategory(Base):
    __tablename__ = "citation_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citations = relationship("Citation", back_populates="category")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    reference_number = Column(String, nullable=False, index=True)
    court = Column(String, nullable=False)
    jurisdiction = Column(String, nullable=False)
    citation_type = Column(String, nullable=False)  # e.g., 'Case Law', 'Statute'
    description = Column(Text, nullable=True)
    keywords = Column(ARRAY(String), default=[])
    summary = Column(Text, nullable=True)
    url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    category_id = Column(UUID(as_uuid=True), ForeignKey("citation_categories.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("CitationCategory", back_populates="citations")
