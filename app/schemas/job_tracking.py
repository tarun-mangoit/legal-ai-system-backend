from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional
from datetime import datetime

class JobTrackingResponse(BaseModel):
    id: UUID4
    document_id: UUID4
    document_name: str
    case_id: UUID4
    job_type: str # 'OCR' or 'AI'
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class AIUsageResponse(BaseModel):
    id: UUID4
    document_id: UUID4
    document_name: str
    case_id: UUID4
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    processing_time: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
