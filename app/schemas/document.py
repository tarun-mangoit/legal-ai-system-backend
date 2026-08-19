from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.case_document import DocumentCategory

class DocumentBase(BaseModel):
    category: DocumentCategory
    remarks: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: UUID4
    case_id: UUID4
    uploaded_by: UUID4
    original_filename: str
    mime_type: str
    extension: str
    file_size: int
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class DocumentWithStatusResponse(DocumentResponse):
    ai_status: Optional[str] = "NONE"
    client_name: Optional[str] = None
    client_id: Optional[UUID4] = None
    advocate_name: Optional[str] = None
    advocate_id: Optional[UUID4] = None
