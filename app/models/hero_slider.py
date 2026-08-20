import uuid
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel

class HeroSlider(BaseModel):
    __tablename__ = "hero_sliders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    button_text = Column(String(50), nullable=False, default="Contact Us")
    image_url = Column(String(1024), nullable=False)
    target_url = Column(String(1024), nullable=False)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
