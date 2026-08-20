from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class HeroSliderBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    button_text: str = "Contact Us"
    target_url: str
    is_active: bool = True
    display_order: int = 0

class HeroSliderCreate(HeroSliderBase):
    pass

class HeroSliderUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    button_text: Optional[str] = None
    target_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class HeroSliderResponse(HeroSliderBase):
    id: UUID
    image_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
