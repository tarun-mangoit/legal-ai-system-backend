from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class PublicCaseCategoryBase(BaseModel):
    name: str
    slug: str

class PublicCaseCategoryCreate(PublicCaseCategoryBase):
    pass

class PublicCaseCategoryResponse(PublicCaseCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublicCaseTagBase(BaseModel):
    name: str
    slug: str

class PublicCaseTagCreate(PublicCaseTagBase):
    pass

class PublicCaseTagResponse(PublicCaseTagBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublicCaseBase(BaseModel):
    title: str
    slug: str
    summary: Optional[str] = None
    content: str
    cover_image_url: Optional[str] = None
    category_id: Optional[UUID] = None
    is_active: bool = True

class PublicCaseCreate(PublicCaseBase):
    tag_ids: List[UUID] = []

class PublicCaseUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    tag_ids: Optional[List[UUID]] = None

class PublicCaseResponse(PublicCaseBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[PublicCaseCategoryResponse] = None
    tags: List[PublicCaseTagResponse] = []

    class Config:
        from_attributes = True

class PublicCaseCategoryWithCount(PublicCaseCategoryResponse):
    count: int

class SidebarDataResponse(BaseModel):
    categories: List[PublicCaseCategoryWithCount]
    recent_cases: List[PublicCaseResponse]
    tags: List[PublicCaseTagResponse]

class PublicCaseNavResponse(BaseModel):
    title: str
    slug: str

class PublicCaseDetailResponse(PublicCaseResponse):
    previous_case: Optional[PublicCaseNavResponse] = None
    next_case: Optional[PublicCaseNavResponse] = None
