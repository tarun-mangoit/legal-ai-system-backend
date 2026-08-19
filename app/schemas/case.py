from pydantic import BaseModel, Field, UUID4, constr
from typing import Optional, List
from datetime import datetime
from app.models.case import CaseStatus, CasePriority
from app.schemas.user import UserResponse
from app.schemas.document import DocumentResponse
from app.schemas.payment import PaymentResponse

class CaseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    category: Optional[str] = Field(None, max_length=100) # Maps to Practice Area
    case_type: Optional[str] = Field(None, max_length=100)
    priority: CasePriority = CasePriority.MEDIUM
    
    # Legal Matter fields
    incident_date: Optional[str] = None
    notice_date: Optional[str] = None
    filing_date: Optional[str] = None
    next_hearing_date: Optional[str] = None
    location: Optional[str] = None
    previous_legal_action: Optional[str] = None
    previous_case_info: Optional[str] = None
    opposing_party_name: Optional[str] = None
    opposing_party_type: Optional[str] = None
    additional_information: Optional[str] = None
    case_fee: Optional[float] = None

class CaseCreate(CaseBase):
    client_id: Optional[UUID4] = None

class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = Field(None, max_length=100)
    case_type: Optional[str] = Field(None, max_length=100)
    priority: Optional[CasePriority] = None
    
    incident_date: Optional[str] = None
    notice_date: Optional[str] = None
    filing_date: Optional[str] = None
    next_hearing_date: Optional[str] = None
    location: Optional[str] = None
    previous_legal_action: Optional[str] = None
    previous_case_info: Optional[str] = None
    opposing_party_name: Optional[str] = None
    opposing_party_type: Optional[str] = None
    additional_information: Optional[str] = None
    case_fee: Optional[float] = None

class CaseStatusUpdate(BaseModel):
    status: CaseStatus

class CaseFeeUpdate(BaseModel):
    fee: float

class CaseResponse(CaseBase):
    id: UUID4
    case_number: str
    client_id: UUID4
    advocate_id: Optional[UUID4] = None
    status: CaseStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    client: Optional[UserResponse] = None
    advocate: Optional[UserResponse] = None

    model_config = {"from_attributes": True}

class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    skip: int
    limit: int

class CaseHistoryResponse(BaseModel):
    id: UUID4
    case_id: UUID4
    changed_by: UUID4
    action_type: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class CaseAssignmentCreate(BaseModel):
    advocate_id: UUID4

class CasePermissions(BaseModel):
    can_view_ai_analysis: bool
    can_edit_case: bool
    can_assign_advocate: bool
    can_update_status: bool
    can_view_audit_logs: bool
    can_view_internal_notes: bool
    can_view_payment_admin: bool
    can_delete_case: bool
    can_close_case: bool

class CaseDetailAggregatedResponse(BaseModel):
    case: CaseResponse
    client: Optional[UserResponse] = None
    advocate: Optional[UserResponse] = None
    documents: List[DocumentResponse] = []
    payments: List[PaymentResponse] = []
    activities: List[CaseHistoryResponse] = []
    permissions: CasePermissions

    model_config = {"from_attributes": True}
