from sqlalchemy import Column, String, Boolean, Text, Integer
from .base import BaseModel

class PracticeArea(BaseModel):
    __tablename__ = "practice_areas"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    icon_svg = Column(Text, nullable=False)
    action_text = Column(String(100), nullable=False, default="Read More")
    link = Column(String(255), nullable=False, default="#")
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
