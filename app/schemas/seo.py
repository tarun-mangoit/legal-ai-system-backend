from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class PageSEOBase(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    robots_tag: Optional[str] = "index, follow"
    canonical_url: Optional[str] = None
    og_image_url: Optional[str] = None

class PageSEOCreate(PageSEOBase):
    page_identifier: str

class PageSEOUpdate(PageSEOBase):
    pass

class PageSEOResponse(PageSEOBase):
    id: UUID
    page_identifier: str

    model_config = ConfigDict(from_attributes=True)
