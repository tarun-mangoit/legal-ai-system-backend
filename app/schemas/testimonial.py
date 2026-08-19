from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class TestimonialBase(BaseModel):
    client_name: str
    client_designation: Optional[str] = None
    client_image_url: Optional[str] = None
    rating: int = 5
    content: str
    is_active: bool = True

class TestimonialCreate(TestimonialBase):
    pass

class TestimonialUpdate(BaseModel):
    client_name: Optional[str] = None
    client_designation: Optional[str] = None
    client_image_url: Optional[str] = None
    rating: Optional[int] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None

class TestimonialResponse(TestimonialBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
