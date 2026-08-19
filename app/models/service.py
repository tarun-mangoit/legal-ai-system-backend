from sqlalchemy import Column, String, Boolean, Text, Integer
from .base import BaseModel

class Service(BaseModel):
    __tablename__ = "services"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    icon_svg = Column(Text, nullable=False)
    action_text = Column(String(100), nullable=False)
    link = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
