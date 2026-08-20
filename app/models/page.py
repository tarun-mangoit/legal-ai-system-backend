from sqlalchemy import Column, String, Text, Boolean
from .base import BaseModel

class Page(BaseModel):
    __tablename__ = "pages"
    
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    featured_image_url = Column(String(1024), nullable=True)
    is_published = Column(Boolean, default=True)
