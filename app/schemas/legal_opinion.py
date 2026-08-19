from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.legal_opinion import OpinionStatus, RiskLevel

class OpinionCommentBase(BaseModel):
    comment: str

class OpinionCommentCreate(OpinionCommentBase):
    pass

class OpinionCommentResponse(OpinionCommentBase):
    id: UUID
    opinion_id: UUID
    author_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class OpinionRevisionResponse(BaseModel):
    id: UUID
    opinion_id: UUID
    revision_number: int
    changed_by: Optional[UUID]
    changes_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LegalOpinionBase(BaseModel):
    summary: Optional[str] = None
    legal_analysis: Optional[str] = None
    facts: Optional[str] = None
    issues: Optional[str] = None
    applicable_laws: Optional[str] = None
    recommendations: Optional[str] = None
    winning_probability: Optional[int] = Field(None, ge=0, le=100)
    risk_level: Optional[RiskLevel] = None

class LegalOpinionCreate(LegalOpinionBase):
    case_id: UUID
    advocate_id: Optional[UUID] = None

class LegalOpinionUpdate(LegalOpinionBase):
    changes_summary: Optional[str] = None

class LegalOpinionResponse(LegalOpinionBase):
    id: UUID
    case_id: UUID
    advocate_id: Optional[UUID]
    status: OpinionStatus
    is_final: bool
    finalized_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    revisions: Optional[List[OpinionRevisionResponse]] = []
    comments: Optional[List[OpinionCommentResponse]] = []

    class Config:
        from_attributes = True
