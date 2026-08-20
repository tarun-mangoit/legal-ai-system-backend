from sqlalchemy import Column, String, Text
from .base import BaseModel

class SectionContent(BaseModel):
    __tablename__ = "section_contents"
    
    section_key = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    subtitle = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    image_url = Column(String(1024), nullable=True)
