from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import BaseModel

class Testimonial(BaseModel):
    __tablename__ = "testimonials"

    client_name = Column(String(255), nullable=False)
    client_designation = Column(String(255), nullable=True)
    client_image_url = Column(String(1024), nullable=True)
    rating = Column(Integer, nullable=False, default=5)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
