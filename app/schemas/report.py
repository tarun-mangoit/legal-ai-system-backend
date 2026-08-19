from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
from app.models.report import ReportStatus

class ReportTemplateBase(BaseModel):
    name: str
    html_content: str
    template_type: str

class ReportTemplateResponse(ReportTemplateBase):
    id: uuid.UUID
    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    case_id: uuid.UUID
    opinion_id: Optional[uuid.UUID] = None
    template_id: uuid.UUID
    generated_by: uuid.UUID
    version: int
    status: ReportStatus
    file_path: Optional[str] = None
    storage_provider: Optional[str] = None
    storage_key: Optional[str] = None

class ReportResponse(ReportBase):
    id: uuid.UUID
    generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
