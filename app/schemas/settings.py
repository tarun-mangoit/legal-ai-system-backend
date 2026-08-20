from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class LinkItem(BaseModel):
    label: str
    url: str

class StatisticItem(BaseModel):
    value: str
    label: str

class SiteSettingsBase(BaseModel):
    company_name: Optional[str] = None
    about_text: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    copyright_text: Optional[str] = None
    
    header_links: Optional[List[LinkItem]] = []
    header_right_links: Optional[List[LinkItem]] = []
    quick_links: Optional[List[LinkItem]] = []
    practice_areas: Optional[List[LinkItem]] = []
    bottom_links: Optional[List[LinkItem]] = []
    
    statistics_image_url: Optional[str] = None
    statistics_items: Optional[List[StatisticItem]] = []

class SiteSettingsUpdate(SiteSettingsBase):
    pass

class SiteSettingsResponse(SiteSettingsBase):
    id: UUID

    class Config:
        from_attributes = True
