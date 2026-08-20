from sqlalchemy import Column, Integer, String, Text
from .base import BaseModel

class PageSEO(BaseModel):
    __tablename__ = "page_seo"
    page_identifier = Column(String(50), unique=True, index=True, nullable=False)
    
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(Text, nullable=True)
    robots_tag = Column(String(255), default="index, follow")
    
    canonical_url = Column(String(255), nullable=True)
    og_image_url = Column(String(255), nullable=True)
