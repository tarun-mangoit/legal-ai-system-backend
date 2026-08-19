from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
import uuid
from datetime import datetime

class CitationCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CitationCategoryResponse(CitationCategoryBase):
    id: uuid.UUID
    class Config:
        from_attributes = True

class CitationBase(BaseModel):
    title: str
    reference_number: str
    court: str
    jurisdiction: str
    citation_type: str
    description: Optional[str] = None
    keywords: List[str] = []
    summary: Optional[str] = None
    url: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    is_active: bool = True

class CitationCreate(CitationBase):
    pass

class CitationUpdate(BaseModel):
    title: Optional[str] = None
    reference_number: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    citation_type: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

class CitationResponse(CitationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
