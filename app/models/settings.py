import uuid
from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel as Base

class SiteSettings(Base):
    __tablename__ = "site_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=True)
    about_text = Column(Text, nullable=True)
    address = Column(String(512), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    copyright_text = Column(String(255), nullable=True)
    
    # Store links as JSON arrays: [{"label": "Home", "url": "/"}, ...]
    header_links = Column(JSON, default=list)
    header_right_links = Column(JSON, default=list)
    quick_links = Column(JSON, default=list)
    practice_areas = Column(JSON, default=list)
    bottom_links = Column(JSON, default=list)
    statistics_image_url = Column(String(512), nullable=True)
    statistics_items = Column(JSON, default=list)
    default_hero_image_url = Column(String(1024), nullable=True)
