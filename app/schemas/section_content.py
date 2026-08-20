from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class SectionContentBase(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None

class SectionContentCreate(SectionContentBase):
    section_key: str

class SectionContentUpdate(SectionContentBase):
    pass

class SectionContentResponse(SectionContentBase):
    id: UUID
    section_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
