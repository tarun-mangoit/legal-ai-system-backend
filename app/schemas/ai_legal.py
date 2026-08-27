from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from app.models.case_document import DocumentProcessingStatus
from app.models.case_analysis import CaseAnalysisStatus
from app.models.legal_opinion import OpinionStatus
from app.models.citation import CitationVerificationStatus

# -----------------
# Document Summary
# -----------------
class DocumentSummaryBase(BaseModel):
    summary: Optional[str] = None
    document_type: Optional[str] = None
    key_facts: Optional[List[str]] = None
    important_dates: Optional[List[Dict[str, str]]] = None
    legal_references: Optional[List[str]] = None
    potential_issues: Optional[List[str]] = None
    evidence_found: Optional[List[str]] = None
    missing_information: Optional[List[str]] = None
    ai_confidence: Optional[float] = None

class DocumentSummaryCreate(DocumentSummaryBase):
    pass

class DocumentSummaryUpdate(DocumentSummaryBase):
    pass

class DocumentSummaryResponse(DocumentSummaryBase):
    id: UUID
    document_id: UUID
    case_id: UUID
    ai_model: Optional[str] = None
    prompt_version: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# -----------------
# Case Analysis
# -----------------
class CaseAnalysisBase(BaseModel):
    executive_summary: Optional[str] = None
    material_facts: Optional[List[str]] = None
    chronology: Optional[List[Dict[str, str]]] = None
    legal_issues: Optional[List[str]] = None
    applicable_laws: Optional[List[str]] = None
    evidence_assessment: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    missing_information: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    suggested_precedents: Optional[List[Dict[str, str]]] = None

class CaseAnalysisUpdate(CaseAnalysisBase):
    pass

class CaseAnalysisResponse(CaseAnalysisBase):
    id: UUID
    case_id: UUID
    status: CaseAnalysisStatus
    ai_model: Optional[str] = None
    prompt_version: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# -----------------
# Legal Opinion
# -----------------
class LegalOpinionBase(BaseModel):
    documents_reviewed: Optional[List[str]] = None
    instructions: Optional[str] = None
    brief_facts: Optional[str] = None
    issues: Optional[List[str]] = None
    applicable_law: Optional[List[str]] = None
    legal_analysis: Optional[str] = None
    evidence_assessment: Optional[str] = None
    precedents: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    risk_level: Optional[str] = None
    conclusion: Optional[str] = None
    recommendations: Optional[List[str]] = None
    disclaimer: Optional[str] = None
    
    # Advocate's fields
    advocate_opinion: Optional[str] = None
    advocate_recommendations: Optional[Union[List[str], str]] = None
    winning_probability: Optional[int] = Field(None, ge=0, le=100)
    advocate_risk_assessment: Optional[str] = None
    advocate_notes: Optional[str] = None

class LegalOpinionUpdate(LegalOpinionBase):
    status: Optional[OpinionStatus] = None

class LegalOpinionResponse(LegalOpinionBase):
    id: UUID
    case_id: UUID
    version: int
    status: OpinionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# -----------------
# Citations
# -----------------
class CitationBase(BaseModel):
    case_name: str
    citation: str
    court: Optional[str] = None
    year: Optional[int] = None
    legal_area: Optional[str] = None
    principle: Optional[str] = None
    full_text: Optional[str] = None
    source: Optional[str] = None

class CitationCreate(CitationBase):
    pass

class CitationUpdate(CitationBase):
    verified: Optional[CitationVerificationStatus] = None

class CitationResponse(CitationBase):
    id: UUID
    verified: CitationVerificationStatus
    created_at: datetime

    class Config:
        from_attributes = True
